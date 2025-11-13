"""
Command-line interface for YouTube Study Buddy.

Usage:
    youtube-study-buddy <url1> <url2> ...
    youtube-study-buddy --file urls.txt
    youtube-study-buddy --subject "Topic" <url1> <url2>
"""

import argparse
import os
import sys

from pathlib import Path
from loguru import logger

from .assessment_generator import AssessmentGenerator
from .auto_categorizer import AutoCategorizer
from .job_logger import create_default_logger
from .knowledge_graph import KnowledgeGraph
from .obsidian_linker import ObsidianLinker
from .langgraph_workflow import process_video_with_langgraph
from .study_notes_generator import StudyNotesGenerator
from .video_job import create_job_from_url
from .video_processor import VideoProcessor

try:
    from .pdf_exporter import PDFExporter
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class YouTubeStudyNotes:
    """Main application class for processing YouTube videos into study notes."""

    def __init__(self, subject=None, global_context=True, base_dir="notes",
                 generate_assessments=True, auto_categorize=True,
                 export_pdf=False, pdf_theme='obsidian'):
        self.subject = subject
        self.global_context = global_context
        self.base_dir = base_dir
        self.output_dir = os.path.join(base_dir, subject) if subject else base_dir
        self.generate_assessments = generate_assessments
        self.auto_categorize = auto_categorize and not subject  # Only auto-categorize when no subject provided
        self.export_pdf = export_pdf
        self.pdf_theme = pdf_theme

        self.video_processor = VideoProcessor("tor")
        self.knowledge_graph = KnowledgeGraph(base_dir, subject, global_context)
        self.notes_generator = StudyNotesGenerator()
        self.obsidian_linker = ObsidianLinker(base_dir, subject, global_context)

        # Initialize new components
        self.auto_categorizer = AutoCategorizer() if self.auto_categorize else None
        self.assessment_generator = AssessmentGenerator(self.notes_generator.client) if generate_assessments else None

        # Initialize PDF exporter if requested
        if self.export_pdf:
            if not PDF_AVAILABLE:
                logger.warning("Warning: PDF export requires additional dependencies:")
                logger.info("  uv pip install weasyprint markdown2")
                logger.info("Continuing without PDF export...")
                self.export_pdf = False
                self.pdf_exporter = None
            else:
                self.pdf_exporter = PDFExporter(theme=self.pdf_theme)
        else:
            self.pdf_exporter = None

        # Job logger for tracking all processing results
        self.job_logger = create_default_logger(Path(self.base_dir))

    def read_urls_from_file(self, filename='urls.txt'):
        """Read URLs from a text file, ignoring comments and empty lines."""
        urls = []
        if not os.path.exists(filename):
            return urls

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        urls.append(line)
        except Exception as e:
            logger.error(f"Warning: Could not read {filename}: {e}")

        return urls

    def process_single_url(self, url):
        """
        Process a single YouTube URL using stateless pipeline.

        Args:
            url: YouTube URL to process

        Returns:
            Dictionary with processing outcome
        """
        # Extract video ID
        video_id = self.video_processor.get_video_id(url)
        if not video_id:
            logger.error(f"ERROR: Invalid YouTube URL: {url}")
            return {
                'url': url,
                'video_id': 'invalid',
                'success': False,
                'error': 'Invalid YouTube URL'
            }

        logger.info(f"\nFound video ID: {video_id}")
        if self.subject:
            logger.info(f"Subject: {self.subject}")
            logger.info(f"Cross-reference scope: {'Global' if self.global_context else 'Subject-only'}")

        # Build components dict for LangGraph workflow
        components = {
            'video_processor': self.video_processor,
            'notes_generator': self.notes_generator,
            'assessment_generator': self.assessment_generator,
            'obsidian_linker': self.obsidian_linker,
            'pdf_exporter': self.pdf_exporter,
            'job_logger': self.job_logger,
            'filename_sanitizer': self.video_processor.sanitize_filename,
            'auto_categorizer': self.auto_categorizer,
            'base_dir': self.base_dir
        }

        # Process through LangGraph workflow
        try:
            final_state = process_video_with_langgraph(
                url=url,
                video_id=video_id,
                components=components,
                subject=self.subject,
                auto_categorize=self.auto_categorize,
                generate_assessment=self.generate_assessments,
                export_pdf=self.export_pdf,
                worker_id=None
            )

            # Update components with detected subject (if categorized)
            if final_state.get('detected_subject'):
                detected_subject = final_state['detected_subject']
                self.knowledge_graph = KnowledgeGraph(self.base_dir, detected_subject, self.global_context)
                self.obsidian_linker = ObsidianLinker(self.base_dir, detected_subject, self.global_context)

            # Update knowledge graph cache
            self.knowledge_graph.refresh_cache()

            # Convert state to result dictionary
            return {
                'url': final_state['url'],
                'video_id': final_state['video_id'],
                'success': final_state.get('completed', False),
                'title': final_state.get('video_title'),
                'filepath': final_state.get('notes_file_path'),
                'duration_seconds': final_state.get('processing_duration'),
                'method': final_state.get('transcript_data', {}).get('method', 'tor') if final_state.get('transcript_data') else 'unknown'
            }

        except Exception as e:
            logger.error(f"\nERROR processing {url}: {e}")

            # Job was already logged by pipeline, just return failure
            return {
                'url': url,
                'video_id': video_id,
                'success': False,
                'error': str(e),
                'duration_seconds': 0
            }

    def _handle_rate_limit_error(self, e):
        """Handle rate limit errors with helpful message."""
        if "rate limit" in str(e).lower() or "429" in str(e) or "too many requests" in str(e).lower():
            logger.warning("\n⚠ RATE LIMITING DETECTED!")
            logger.info("YouTube is temporarily blocking requests. Solutions:")
            logger.info("1. Wait 15-30 minutes before trying again")
            logger.info("2. Process fewer videos at once")
            logger.info("3. Ensure Tor proxy is running: docker-compose up -d tor-proxy")
        else:
            logger.info("\nTroubleshooting:")
            logger.info("1. Check if the video has captions/subtitles enabled")
            logger.info("2. Some videos restrict transcript access")
            logger.info("3. Ensure Tor proxy is running: docker-compose up -d tor-proxy")

    def process_urls(self, urls):
        """Process a list of URLs sequentially."""
        if not urls:
            logger.info("No URLs provided")
            return

        # Check if API is ready
        if not self.notes_generator.is_ready():
            return

        logger.debug(f"\nProcessing {len(urls)} URL(s) sequentially...")
        if self.subject:
            logger.info(f"Subject: {self.subject}")
            logger.info(f"Cross-reference scope: {'Subject-only' if not self.global_context else 'Global'}")

        # Process each URL sequentially
        results = []
        for i, url in enumerate(urls, 1):
            logger.info(f"\n[{i}/{len(urls)}] Processing: {url}")
            result = self.process_single_url(url)
            results.append(result)

            # Add delay between videos to avoid rate limiting
            if i < len(urls):
                import time
                time.sleep(3.0)

        # Show summary
        successful = sum(1 for r in results if r['success'])
        logger.info(f"\n{'='*50}")
        logger.success(f"COMPLETE: {successful}/{len(urls)} URL(s) processed successfully")
        logger.info(f"Output saved to: {self.output_dir}/")

        # Show knowledge graph stats
        stats = self.knowledge_graph.get_stats()
        logger.info(f"Knowledge Graph ({stats['scope']}): {stats['total_notes']} notes, {stats['total_concepts']} concepts")
        if stats.get('subject_count'):
            logger.info(f"Subjects: {stats['subject_count']} ({', '.join(stats['subjects'])})")
        logger.info("="*50)

        # Show statistics at the end
        if hasattr(self.video_processor.provider, 'print_stats'):
            self.video_processor.provider.print_stats()


def show_help():
    """Display help information."""
    print("""
YouTube Study Buddy - Transform YouTube videos into AI-powered study notes

Usage:
  youtube-study-buddy <url1> <url2> ...                    # Process URLs
  youtube-study-buddy --file urls.txt                      # Process URLs from file
  youtube-study-buddy --subject "Machine Learning" <url>   # With subject organization

Options:
  --subject <name>         Organize notes by subject (creates notes/<subject>/ folder)
  --subject-only           Cross-reference only within the specified subject (default: global)
  --file <filename>        Read URLs from file (one per line)
  --no-assessments         Disable assessment generation
  --no-auto-categorize     Disable auto-categorization
  --export-pdf             Export notes to PDF with Obsidian-style formatting
  --pdf-theme <theme>      PDF theme: default, obsidian, academic, minimal (default: obsidian)
  --help, -h               Show this help message

Examples:
  # Process a single video
  youtube-study-buddy https://youtube.com/watch?v=xyz

  # Process multiple videos from file
  youtube-study-buddy --file urls.txt

  # With subject organization
  youtube-study-buddy --subject "Machine Learning" https://youtube.com/watch?v=xyz

  # Export to PDF with Obsidian theme
  youtube-study-buddy --export-pdf https://youtube.com/watch?v=xyz

  # Export with academic theme
  youtube-study-buddy --export-pdf --pdf-theme academic --file urls.txt

Performance:
  Processing time: ~60s per video (depends on video length and transcript complexity)

Playlist Extraction:
  # Extract URLs from a YouTube playlist using yt-dlp
  yt-dlp --flat-playlist --print url "PLAYLIST_URL" > urls.txt
  youtube-study-buddy --file urls.txt

Requirements:
  - Claude API key (set CLAUDE_API_KEY or ANTHROPIC_API_KEY environment variable)
    Get it from: https://console.anthropic.com/
  - Tor proxy running: docker-compose up -d tor-proxy

Output:
  - Notes saved in notes/<subject>/ folders
  - Cross-references to related notes automatically included
  - Obsidian [[links]] automatically added between related notes

For interactive GUI: streamlit run streamlit_app.py
    """)


def main():
    """Main CLI entry point."""
    print("""
========================================
   YouTube to Study Notes Tool
   Tor-based Transcript + Claude AI
========================================
    """)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert YouTube videos to organized study notes', add_help=False)
    parser.add_argument('urls', nargs='*', help='YouTube URLs to process')
    parser.add_argument('--subject', '-s', help='Subject for organizing notes')
    parser.add_argument('--subject-only', action='store_true', help='Cross-reference only within subject')
    parser.add_argument('--file', '-f', help='Read URLs from file (one per line)')
    parser.add_argument('--no-assessments', action='store_true', help='Disable assessment generation')
    parser.add_argument('--no-auto-categorize', action='store_true', help='Disable auto-categorization')
    parser.add_argument('--export-pdf', action='store_true', help='Export notes to PDF (requires: uv pip install weasyprint markdown2)')
    parser.add_argument('--pdf-theme', default='obsidian', choices=['default', 'obsidian', 'academic', 'minimal'],
                       help='PDF theme style (default: obsidian)')
    parser.add_argument('--debug-logging', action='store_true', help='Enable detailed debug logging to debug_logs/ directory')
    parser.add_argument('--help', '-h', action='store_true', help='Show help message')

    args = parser.parse_args()

    if args.help:
        show_help()
        sys.exit(0)

    # Enable debug logging if requested
    if args.debug_logging:
        from .debug_logger import enable_debug_logging
        logger = enable_debug_logging()
        logger.success(f"✓ Debug logging enabled")
        logger.info(f"  Session log: {logger.session_log}")
        logger.info(f"  API log: {logger.api_log}")
        

    # Create app instance with configuration
    app = YouTubeStudyNotes(
        subject=args.subject,
        global_context=not args.subject_only,
        generate_assessments=not args.no_assessments,
        auto_categorize=not args.no_auto_categorize,
        export_pdf=args.export_pdf,
        pdf_theme=args.pdf_theme
    )

    # Collect URLs from either command line or file
    urls_to_process = []

    if args.file:
        # Read from file
        urls_to_process = app.read_urls_from_file(args.file)
        if not urls_to_process:
            logger.info(f"No URLs found in {args.file}")
            sys.exit(1)
    elif args.urls:
        # Use URLs from command line
        urls_to_process = args.urls
    else:
        # No URLs provided
        show_help()
        sys.exit(1)

    # Process the URLs
    app.process_urls(urls_to_process)

    # Show debug log analysis if enabled
    if args.debug_logging:
        logger.info("\n" + "="*60)
        from .debug_logger import get_logger
        debug_logger = get_logger()
        debug_logger.analyze_logs()


if __name__ == "__main__":
    main()
