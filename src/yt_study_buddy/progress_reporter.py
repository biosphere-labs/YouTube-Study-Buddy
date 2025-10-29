"""
Progress reporting module for JSON output format.

Enables real-time progress updates for FastAPI backend integration.
"""
import json
import sys
from typing import Optional
from enum import Enum


class ProgressStep(str, Enum):
    """Standard progress step identifiers."""
    STARTING = "starting"
    FETCHING_TRANSCRIPT = "fetching_transcript"
    CALLING_CLAUDE = "calling_claude"
    GENERATING_NOTES = "generating_notes"
    GENERATING_ASSESSMENT = "generating_assessment"
    CREATING_LINKS = "creating_links"
    WRITING_FILES = "writing_files"
    EXPORTING_PDF = "exporting_pdf"
    COMPLETED = "completed"
    ERROR = "error"


class ProgressReporter:
    """
    Reports progress events in JSON format for API integration.

    When enabled, outputs JSON progress events to stdout, one per line.
    Each event is immediately flushed for real-time streaming.
    """

    def __init__(self, enabled: bool = False):
        """
        Initialize the progress reporter.

        Args:
            enabled: If True, output JSON progress events. If False, do nothing.
        """
        self.enabled = enabled

    def report_step(self, step: str, progress: float, message: str, **kwargs):
        """
        Report a progress step.

        Args:
            step: Progress step identifier (from ProgressStep enum or custom string)
            progress: Progress percentage (0-100)
            message: Human-readable status message
            **kwargs: Additional fields to include in the JSON output
        """
        if not self.enabled:
            return

        event = {
            "step": step,
            "progress": progress,
            "message": message
        }

        # Add any additional fields
        event.update(kwargs)

        # Write to stdout and flush immediately
        print(json.dumps(event), file=sys.stdout, flush=True)

    def report_error(self, error: str, step: Optional[str] = None):
        """
        Report an error event.

        Args:
            error: Error message
            step: Optional step where error occurred
        """
        if not self.enabled:
            return

        event = {
            "step": ProgressStep.ERROR,
            "progress": 0,
            "message": f"Error: {error}",
            "error": error
        }

        if step:
            event["failed_step"] = step

        print(json.dumps(event), file=sys.stdout, flush=True)

    def report_complete(self, output_path: str, **kwargs):
        """
        Report successful completion.

        Args:
            output_path: Path to the generated output file
            **kwargs: Additional fields to include in the JSON output
        """
        if not self.enabled:
            return

        event = {
            "step": ProgressStep.COMPLETED,
            "progress": 100.0,
            "message": "Processing complete!",
            "output_path": output_path
        }

        # Add any additional fields
        event.update(kwargs)

        print(json.dumps(event), file=sys.stdout, flush=True)


# Singleton instance for global access
_global_reporter: Optional[ProgressReporter] = None


def init_progress_reporter(enabled: bool = False) -> ProgressReporter:
    """
    Initialize the global progress reporter.

    Args:
        enabled: If True, enable JSON progress output

    Returns:
        ProgressReporter instance
    """
    global _global_reporter
    _global_reporter = ProgressReporter(enabled=enabled)
    return _global_reporter


def get_progress_reporter() -> Optional[ProgressReporter]:
    """
    Get the global progress reporter instance.

    Returns:
        ProgressReporter instance or None if not initialized
    """
    return _global_reporter
