"""
LangGraph nodes for video processing workflow.

Each node is a pure function that takes state and returns updated state.
Nodes wrap existing pipeline functions for compatibility.
"""
import time
from datetime import datetime
from typing import Optional

from loguru import logger

from .workflow_state import VideoProcessingState
from .auto_categorizer import AutoCategorizer


def categorize_node(
    state: VideoProcessingState,
    video_processor,
    auto_categorizer: AutoCategorizer,
    base_dir: str
) -> VideoProcessingState:
    """
    Auto-categorize video based on transcript and title.

    This node fetches the transcript/title if needed and determines the subject.
    """
    logger.info("🔍 Auto-categorizing video content...")

    try:
        # Fetch transcript and title if not already fetched
        if not state.get('transcript'):
            logger.info("  Fetching transcript for categorization...")
            transcript_data = video_processor.get_transcript(state['video_id'])
            state['transcript'] = transcript_data['transcript']
            state['transcript_data'] = transcript_data

            logger.info("  Fetching title for categorization...")
            video_title = video_processor.get_video_title(
                state['video_id'],
                worker_id=state.get('worker_id')
            )
            state['video_title'] = video_title
            state['needs_ai_title'] = video_title.startswith("Video_")

        # Categorize
        detected_subject = auto_categorizer.categorize_video(
            state['transcript'],
            state['video_title'],
            base_dir,
            subject=state.get('subject')  # User override takes precedence
        )

        logger.info(f"  ✓ Detected subject: {detected_subject}")
        state['detected_subject'] = detected_subject
        state['subject'] = detected_subject
        state['output_dir'] = f"{base_dir}/{detected_subject}"

    except Exception as e:
        logger.error(f"  ✗ Auto-categorization failed: {e}")
        state['error'] = f"Categorization failed: {e}"
        # Continue with base directory
        state['output_dir'] = base_dir

    return state


def fetch_transcript_node(
    state: VideoProcessingState,
    video_processor
) -> VideoProcessingState:
    """
    Fetch transcript and title from YouTube.

    Skips if already fetched (e.g., by categorization node).
    """
    # Check if already done
    if state.get('transcript'):
        logger.info("  📝 Transcript already fetched, skipping")
        return state

    stage_start = time.time()

    try:
        # Fetch transcript
        logger.info(f"  📝 Fetching transcript for {state['video_id']}...")
        transcript_data = video_processor.get_transcript(state['video_id'])

        if not transcript_data:
            raise ValueError("Could not get transcript: Both Tor and yt-dlp fallback failed")

        state['transcript'] = transcript_data['transcript']
        state['transcript_data'] = transcript_data

        if transcript_data.get('duration'):
            logger.info(f"    Duration: {transcript_data['duration']}")
        logger.info(f"    Length: {transcript_data['length']} characters")

        # Fetch title (non-critical - use video ID as fallback)
        logger.info(f"  🏷️  Fetching title...")
        try:
            video_title = video_processor.get_video_title(
                state['video_id'],
                worker_id=state.get('worker_id')
            )
            if video_title and not video_title.startswith("Video_"):
                logger.info(f"    Title: {video_title}")
                state['video_title'] = video_title
                state['needs_ai_title'] = False
            else:
                logger.warning(f"    ⚠️  Got fallback title, will use video ID")
                state['video_title'] = f"Video_{state['video_id']}"
                state['needs_ai_title'] = True
        except Exception as title_error:
            logger.warning(f"    ⚠️  Title fetch failed: {title_error}")
            state['video_title'] = f"Video_{state['video_id']}"
            state['needs_ai_title'] = True

        # Track timing
        if 'timings' not in state:
            state['timings'] = {}
        state['timings']['fetch_transcript'] = time.time() - stage_start

    except Exception as e:
        logger.error(f"  ✗ Transcript fetch failed: {e}")
        state['error'] = f"Transcript fetch failed: {e}"
        state['failed'] = True
        raise

    return state


def generate_notes_node(
    state: VideoProcessingState,
    notes_generator
) -> VideoProcessingState:
    """
    Generate study notes using Claude API.

    Also extracts AI title if needed.
    """
    stage_start = time.time()

    try:
        logger.info("  📚 Generating study notes...")

        # Generate notes
        study_notes = notes_generator.generate_notes(
            state['transcript'],
            state['video_title']
        )

        state['study_notes'] = study_notes
        logger.info(f"    ✓ Generated {len(study_notes)} characters of notes")

        # Extract AI title if needed
        if state.get('needs_ai_title', False):
            logger.info("  🤖 Extracting title from AI-generated notes...")
            try:
                # Extract first heading as title
                import re
                match = re.search(r'^#\s+(.+)$', study_notes, re.MULTILINE)
                if match:
                    ai_title = match.group(1).strip()
                    state['ai_extracted_title'] = ai_title
                    state['video_title'] = ai_title
                    logger.info(f"    ✓ Extracted title: {ai_title}")
                else:
                    logger.warning("    ⚠️  Could not extract title from notes")
            except Exception as e:
                logger.warning(f"    ⚠️  Title extraction failed: {e}")

        # Track timing
        if 'timings' not in state:
            state['timings'] = {}
        state['timings']['generate_notes'] = time.time() - stage_start

    except Exception as e:
        logger.error(f"  ✗ Notes generation failed: {e}")
        state['error'] = f"Notes generation failed: {e}"
        state['failed'] = True
        raise

    return state


def generate_assessment_node(
    state: VideoProcessingState,
    assessment_generator
) -> VideoProcessingState:
    """
    Generate assessment questions using Claude API.
    """
    stage_start = time.time()

    try:
        logger.info("  📝 Generating assessment questions...")

        assessment = assessment_generator.generate_assessment(
            state['transcript'],
            state['study_notes'],
            state['video_title']
        )

        state['assessment'] = assessment
        logger.info(f"    ✓ Generated {len(assessment)} characters of assessment")

        # Track timing
        if 'timings' not in state:
            state['timings'] = {}
        state['timings']['generate_assessment'] = time.time() - stage_start

    except Exception as e:
        logger.error(f"  ✗ Assessment generation failed: {e}")
        state['error'] = f"Assessment generation failed: {e}"
        # Non-critical - continue without assessment

    return state


def write_files_node(
    state: VideoProcessingState,
    filename_sanitizer
) -> VideoProcessingState:
    """
    Write markdown files to disk.
    """
    import os
    from pathlib import Path

    stage_start = time.time()

    try:
        logger.info("  💾 Writing markdown files...")

        output_dir = Path(state['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        safe_title = filename_sanitizer(state['video_title'])

        # Write notes file
        notes_path = output_dir / f"{safe_title}.md"
        notes_path.write_text(state['study_notes'], encoding='utf-8')
        state['notes_file_path'] = str(notes_path)
        logger.info(f"    ✓ Wrote notes: {notes_path}")

        # Write assessment file if generated
        if state.get('assessment'):
            assessment_path = output_dir / f"Assessment_{safe_title}.md"
            assessment_path.write_text(state['assessment'], encoding='utf-8')
            state['assessment_file_path'] = str(assessment_path)
            logger.info(f"    ✓ Wrote assessment: {assessment_path}")

        # Track timing
        if 'timings' not in state:
            state['timings'] = {}
        state['timings']['write_files'] = time.time() - stage_start

    except Exception as e:
        logger.error(f"  ✗ File writing failed: {e}")
        state['error'] = f"File writing failed: {e}"
        state['failed'] = True
        raise

    return state


def obsidian_links_node(
    state: VideoProcessingState,
    obsidian_linker
) -> VideoProcessingState:
    """
    Process Obsidian wiki-style links.
    """
    stage_start = time.time()

    try:
        logger.info("  🔗 Processing Obsidian links...")

        # Process links for notes file
        if state.get('notes_file_path'):
            linked_notes = obsidian_linker.process_file(
                state['notes_file_path'],
                state['video_title']
            )
            state['linked_notes'] = linked_notes
            state['obsidian_links_added'] = True

            if linked_notes:
                logger.info(f"    ✓ Added {len(linked_notes)} wiki-links")
            else:
                logger.info("    No related notes found for linking")

        # Track timing
        if 'timings' not in state:
            state['timings'] = {}
        state['timings']['obsidian_links'] = time.time() - stage_start

    except Exception as e:
        logger.error(f"  ✗ Obsidian linking failed: {e}")
        state['error'] = f"Obsidian linking failed: {e}"
        # Non-critical - continue

    return state


def export_pdf_node(
    state: VideoProcessingState,
    pdf_exporter
) -> VideoProcessingState:
    """
    Export markdown to PDF.
    """
    import os
    from pathlib import Path

    stage_start = time.time()

    try:
        logger.info("  📄 Exporting to PDF...")

        if not state.get('notes_file_path'):
            logger.warning("    ⚠️  No notes file to export")
            return state

        # Create PDF subdirectory
        output_dir = Path(state['output_dir'])
        pdf_dir = output_dir / "pdfs"
        pdf_dir.mkdir(exist_ok=True)

        # Export PDF
        notes_path = Path(state['notes_file_path'])
        pdf_path = pdf_dir / f"{notes_path.stem}.pdf"

        pdf_exporter.export_to_pdf(
            str(notes_path),
            str(pdf_path)
        )

        state['pdf_file_path'] = str(pdf_path)
        logger.info(f"    ✓ Exported PDF: {pdf_path}")

        # Track timing
        if 'timings' not in state:
            state['timings'] = {}
        state['timings']['export_pdf'] = time.time() - stage_start

    except Exception as e:
        logger.error(f"  ✗ PDF export failed: {e}")
        state['error'] = f"PDF export failed: {e}"
        # Non-critical - continue

    return state


def log_job_node(
    state: VideoProcessingState,
    job_logger
) -> VideoProcessingState:
    """
    Log completed job to processing log.
    """
    try:
        # Convert state back to VideoProcessingJob for logging
        # (We can refactor job_logger later to accept state directly)
        from .video_job import VideoProcessingJob, ProcessingStage

        job = VideoProcessingJob(
            url=state['url'],
            video_id=state['video_id'],
            subject=state.get('subject'),
            worker_id=state.get('worker_id')
        )

        # Populate job with state data
        job.transcript = state.get('transcript')
        job.transcript_data = state.get('transcript_data')
        job.video_title = state.get('video_title')
        job.study_notes = state.get('study_notes')
        job.assessment = state.get('assessment')
        job.notes_file_path = state.get('notes_file_path')
        job.assessment_file_path = state.get('assessment_file_path')
        job.start_time = state.get('start_time')
        job.end_time = state.get('end_time')
        job.processing_duration = state.get('processing_duration')

        if state.get('failed'):
            job.mark_failed(state.get('error', 'Unknown error'))
        else:
            job.mark_completed(state.get('processing_duration', 0))

        job_logger.log_job(job)
        logger.debug("  ✓ Job logged to processing_log.json")

    except Exception as e:
        logger.warning(f"  ⚠️  Job logging failed: {e}")
        # Non-critical

    return state
