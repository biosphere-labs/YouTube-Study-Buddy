"""
LangGraph state schema for video processing workflow.

This replaces the VideoProcessingJob class with a TypedDict-based state
that LangGraph can track and checkpoint automatically.
"""
from typing import TypedDict, Optional, Literal
from datetime import datetime


class VideoProcessingState(TypedDict, total=False):
    """State passed through the video processing workflow."""

    # Input
    url: str
    video_id: str
    subject: Optional[str]
    worker_id: Optional[int]

    # Auto-categorization
    auto_categorize: bool
    detected_subject: Optional[str]

    # Fetched data
    transcript: Optional[str]
    transcript_data: Optional[dict]
    video_title: Optional[str]
    needs_ai_title: bool

    # Generated content
    study_notes: Optional[str]
    ai_extracted_title: Optional[str]
    assessment: Optional[str]

    # Output paths
    output_dir: str
    notes_file_path: Optional[str]
    assessment_file_path: Optional[str]
    pdf_file_path: Optional[str]

    # Obsidian linking
    obsidian_links_added: bool
    linked_notes: list[str]

    # Configuration
    generate_assessment: bool
    export_pdf: bool

    # Status tracking
    error: Optional[str]
    failed: bool
    completed: bool

    # Timing
    start_time: Optional[float]
    end_time: Optional[float]
    processing_duration: Optional[float]
    timings: dict[str, float]  # Stage-level timings

    # Metadata
    created_at: str
    updated_at: str


# Conditional edge return types
ShouldCategorize = Literal["categorize", "skip_categorize"]
ShouldGenerateAssessment = Literal["generate_assessment", "skip_assessment"]
ShouldExportPDF = Literal["export_pdf", "skip_export"]
