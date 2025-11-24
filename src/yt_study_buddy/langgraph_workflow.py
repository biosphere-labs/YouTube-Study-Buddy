"""
LangGraph workflow for video processing.

Replaces processing_pipeline.py with a declarative graph-based approach.
"""
import time
from datetime import datetime
from functools import partial
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from .workflow_state import (
    VideoProcessingState,
    ShouldCategorize,
    ShouldGenerateAssessment,
    ShouldExportPDF
)
from .workflow_nodes import (
    categorize_node,
    fetch_transcript_node,
    generate_notes_node,
    generate_assessment_node,
    write_files_node,
    obsidian_links_node,
    export_pdf_node,
    log_job_node
)


# Conditional edge functions
def should_categorize(state: VideoProcessingState) -> ShouldCategorize:
    """Decide if we need to categorize."""
    # Categorize if auto_categorize enabled AND no subject provided
    if state.get('auto_categorize') and not state.get('subject'):
        return "categorize"
    return "skip_categorize"


def should_generate_assessment(state: VideoProcessingState) -> ShouldGenerateAssessment:
    """Decide if we should generate assessment."""
    if state.get('generate_assessment'):
        return "generate_assessment"
    return "skip_assessment"


def should_export_pdf(state: VideoProcessingState) -> ShouldExportPDF:
    """Decide if we should export to PDF."""
    if state.get('export_pdf'):
        return "export_pdf"
    return "skip_export"


def create_workflow(components: dict) -> StateGraph:
    """
    Create the video processing workflow graph.

    Args:
        components: Dictionary with all required components:
            - 'video_processor': VideoProcessor instance
            - 'notes_generator': StudyNotesGenerator instance
            - 'assessment_generator': AssessmentGenerator instance (optional)
            - 'obsidian_linker': ObsidianLinker instance
            - 'pdf_exporter': PDFExporter instance (optional)
            - 'job_logger': JobLogger instance (optional)
            - 'filename_sanitizer': Function to sanitize filenames
            - 'auto_categorizer': AutoCategorizer instance (optional)
            - 'base_dir': Base output directory

    Returns:
        Compiled LangGraph workflow
    """
    # Create workflow
    workflow = StateGraph(VideoProcessingState)

    # Bind components to nodes using partial
    categorize_fn = partial(
        categorize_node,
        auto_categorizer=components.get('auto_categorizer'),
        base_dir=components.get('base_dir', 'notes')
    )

    fetch_transcript_fn = partial(
        fetch_transcript_node,
        video_processor=components['video_processor']
    )

    generate_notes_fn = partial(
        generate_notes_node,
        notes_generator=components['notes_generator']
    )

    generate_assessment_fn = partial(
        generate_assessment_node,
        assessment_generator=components.get('assessment_generator')
    )

    write_files_fn = partial(
        write_files_node,
        filename_sanitizer=components['filename_sanitizer']
    )

    obsidian_links_fn = partial(
        obsidian_links_node,
        obsidian_linker=components['obsidian_linker']
    )

    export_pdf_fn = partial(
        export_pdf_node,
        pdf_exporter=components.get('pdf_exporter')
    )

    log_job_fn = partial(
        log_job_node,
        job_logger=components.get('job_logger')
    )

    # Add nodes
    workflow.add_node("categorize", categorize_fn)
    workflow.add_node("fetch_transcript", fetch_transcript_fn)
    workflow.add_node("generate_notes", generate_notes_fn)
    workflow.add_node("generate_assessment", generate_assessment_fn)
    workflow.add_node("write_files", write_files_fn)
    workflow.add_node("obsidian_links", obsidian_links_fn)
    workflow.add_node("export_pdf", export_pdf_fn)
    workflow.add_node("log_job", log_job_fn)

    # Define workflow structure
    # Start by fetching transcript - always needed
    workflow.set_entry_point("fetch_transcript")

    # After fetch, conditionally categorize if needed
    workflow.add_conditional_edges(
        "fetch_transcript",
        should_categorize,
        {
            "categorize": "categorize",
            "skip_categorize": "generate_notes"
        }
    )

    # After categorization, generate notes
    workflow.add_edge("categorize", "generate_notes")

    # Conditional: Should we generate assessment?
    workflow.add_conditional_edges(
        "generate_notes",
        should_generate_assessment,
        {
            "generate_assessment": "generate_assessment",
            "skip_assessment": "write_files"
        }
    )

    # After assessment, write files
    workflow.add_edge("generate_assessment", "write_files")

    # After writing files, add Obsidian links
    workflow.add_edge("write_files", "obsidian_links")

    # Conditional: Should we export PDF?
    workflow.add_conditional_edges(
        "obsidian_links",
        should_export_pdf,
        {
            "export_pdf": "export_pdf",
            "skip_export": "log_job"
        }
    )

    # After PDF export, log job
    workflow.add_edge("export_pdf", "log_job")

    # After logging, we're done
    workflow.add_edge("log_job", END)

    return workflow


def compile_workflow(components: dict, checkpointer=None) -> StateGraph:
    """
    Create and compile the workflow with optional checkpointing.

    Args:
        components: Components dictionary
        checkpointer: Optional checkpointer for state persistence (default: MemorySaver)

    Returns:
        Compiled workflow ready to invoke
    """
    workflow = create_workflow(components)

    # Use MemorySaver by default for automatic state checkpointing
    if checkpointer is None:
        checkpointer = MemorySaver()

    compiled = workflow.compile(checkpointer=checkpointer)
    return compiled


def process_video_with_langgraph(
    url: str,
    video_id: str,
    components: dict,
    subject: str = None,
    auto_categorize: bool = True,
    generate_assessment: bool = True,
    export_pdf: bool = True,
    worker_id: int = None
) -> VideoProcessingState:
    """
    Process a video using the LangGraph workflow.

    This is the main entry point that replaces process_video_job() from processing_pipeline.py

    Args:
        url: YouTube video URL
        video_id: Extracted video ID
        components: Components dictionary
        subject: Optional subject override
        auto_categorize: Enable auto-categorization
        generate_assessment: Generate assessment questions
        export_pdf: Export to PDF
        worker_id: Optional worker ID for parallel processing

    Returns:
        Final state after workflow execution
    """
    start_time = time.time()

    # Initialize state
    initial_state: VideoProcessingState = {
        'url': url,
        'video_id': video_id,
        'subject': subject,
        'worker_id': worker_id,
        'auto_categorize': auto_categorize,
        'generate_assessment': generate_assessment,
        'export_pdf': export_pdf,
        'output_dir': components.get('base_dir', 'notes'),
        'failed': False,
        'completed': False,
        'start_time': start_time,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'timings': {},
        'needs_ai_title': False,
        'obsidian_links_added': False,
        'linked_notes': []
    }

    logger.info(f"\n{'='*60}")
    logger.info(f"Processing Video: {video_id}")
    logger.info(f"{'='*60}")

    try:
        # Compile workflow
        app = compile_workflow(components)

        # Execute workflow
        # Note: We use a thread_id for checkpointing (allows resuming failed runs)
        config = {"configurable": {"thread_id": video_id}}
        final_state = app.invoke(initial_state, config)

        # Mark completion
        final_state['end_time'] = time.time()
        final_state['processing_duration'] = final_state['end_time'] - start_time
        final_state['completed'] = True
        final_state['updated_at'] = datetime.now().isoformat()

        logger.success(f"  ✓ Job completed in {final_state['processing_duration']:.1f}s")
        logger.info(f"{'='*60}\n")

        return final_state

    except Exception as e:
        logger.error(f"  ✗ Workflow failed: {e}")
        logger.info(f"{'='*60}\n")

        # Create failed state
        failed_state = initial_state.copy()
        failed_state['error'] = str(e)
        failed_state['failed'] = True
        failed_state['end_time'] = time.time()
        failed_state['processing_duration'] = failed_state['end_time'] - start_time
        failed_state['updated_at'] = datetime.now().isoformat()

        return failed_state


def visualize_workflow(components: dict, output_path: str = "workflow_graph.png"):
    """
    Generate a visual representation of the workflow graph.

    Requires: pip install pygraphviz (optional)

    Args:
        components: Components dictionary
        output_path: Output path for graph image
    """
    try:
        workflow = create_workflow(components)
        compiled = workflow.compile()

        # Get mermaid representation
        mermaid = compiled.get_graph().draw_mermaid()

        # Save to file
        with open(output_path.replace('.png', '.mmd'), 'w') as f:
            f.write(mermaid)

        logger.info(f"Workflow graph saved to {output_path.replace('.png', '.mmd')}")
        logger.info("View at: https://mermaid.live/")

    except Exception as e:
        logger.warning(f"Could not generate workflow visualization: {e}")
