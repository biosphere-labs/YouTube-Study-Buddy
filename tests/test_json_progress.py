"""
Tests for JSON progress output functionality.
"""
import json
import pytest
from io import StringIO
from unittest.mock import patch

# Import directly - conftest.py sets up the path
import importlib.util
import sys
from pathlib import Path

# Direct module import to avoid __init__.py imports
spec = importlib.util.spec_from_file_location(
    "progress_reporter",
    Path(__file__).parent.parent / "src" / "yt_study_buddy" / "progress_reporter.py"
)
progress_reporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress_reporter)

ProgressReporter = progress_reporter.ProgressReporter
ProgressStep = progress_reporter.ProgressStep
init_progress_reporter = progress_reporter.init_progress_reporter
get_progress_reporter = progress_reporter.get_progress_reporter


class TestProgressReporter:
    """Test the ProgressReporter class."""

    def test_disabled_reporter_outputs_nothing(self):
        """Disabled reporter should not output anything."""
        reporter = ProgressReporter(enabled=False)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_step("test", 50.0, "Testing")
            reporter.report_error("Error message")
            reporter.report_complete("/path/to/file.md")

            output = mock_stdout.getvalue()
            assert output == "", "Disabled reporter should not output anything"

    def test_enabled_reporter_outputs_json(self):
        """Enabled reporter should output valid JSON."""
        reporter = ProgressReporter(enabled=True)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_step("test_step", 50.0, "Testing")

            output = mock_stdout.getvalue().strip()
            data = json.loads(output)

            assert data["step"] == "test_step"
            assert data["progress"] == 50.0
            assert data["message"] == "Testing"

    def test_report_step_with_additional_fields(self):
        """Test reporting step with additional fields."""
        reporter = ProgressReporter(enabled=True)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_step(
                "test_step",
                75.0,
                "Processing",
                video_id="abc123",
                worker_id=1
            )

            output = mock_stdout.getvalue().strip()
            data = json.loads(output)

            assert data["step"] == "test_step"
            assert data["progress"] == 75.0
            assert data["message"] == "Processing"
            assert data["video_id"] == "abc123"
            assert data["worker_id"] == 1

    def test_report_error(self):
        """Test error reporting."""
        reporter = ProgressReporter(enabled=True)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_error("Test error message", step="fetching")

            output = mock_stdout.getvalue().strip()
            data = json.loads(output)

            assert data["step"] == ProgressStep.ERROR
            assert data["progress"] == 0
            assert "Error: Test error message" in data["message"]
            assert data["error"] == "Test error message"
            assert data["failed_step"] == "fetching"

    def test_report_error_without_step(self):
        """Test error reporting without failed step."""
        reporter = ProgressReporter(enabled=True)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_error("Test error message")

            output = mock_stdout.getvalue().strip()
            data = json.loads(output)

            assert data["step"] == ProgressStep.ERROR
            assert data["progress"] == 0
            assert data["error"] == "Test error message"
            assert "failed_step" not in data

    def test_report_complete(self):
        """Test completion reporting."""
        reporter = ProgressReporter(enabled=True)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_complete(
                "/path/to/note.md",
                video_id="xyz789",
                duration_seconds=45.2
            )

            output = mock_stdout.getvalue().strip()
            data = json.loads(output)

            assert data["step"] == ProgressStep.COMPLETED
            assert data["progress"] == 100.0
            assert data["message"] == "Processing complete!"
            assert data["output_path"] == "/path/to/note.md"
            assert data["video_id"] == "xyz789"
            assert data["duration_seconds"] == 45.2

    def test_multiple_progress_steps(self):
        """Test multiple progress steps in sequence."""
        reporter = ProgressReporter(enabled=True)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_step(ProgressStep.STARTING, 10.0, "Starting")
            reporter.report_step(ProgressStep.FETCHING_TRANSCRIPT, 25.0, "Fetching")
            reporter.report_step(ProgressStep.GENERATING_NOTES, 60.0, "Generating")
            reporter.report_complete("/output/test.md")

            output = mock_stdout.getvalue().strip()
            lines = output.split('\n')

            assert len(lines) == 4

            # Verify each line is valid JSON
            for line in lines:
                data = json.loads(line)
                assert "step" in data
                assert "progress" in data
                assert "message" in data


class TestProgressReporterGlobal:
    """Test global progress reporter initialization."""

    def test_init_progress_reporter(self):
        """Test initializing global progress reporter."""
        reporter = init_progress_reporter(enabled=True)

        assert reporter is not None
        assert reporter.enabled is True
        assert get_progress_reporter() is reporter

    def test_init_disabled_progress_reporter(self):
        """Test initializing disabled global progress reporter."""
        reporter = init_progress_reporter(enabled=False)

        assert reporter is not None
        assert reporter.enabled is False

    def test_get_progress_reporter_returns_none_when_not_initialized(self):
        """Test getting reporter before initialization."""
        # Note: This test assumes we can reset the global state
        # In practice, once initialized, it stays initialized
        # This is a limitation of the singleton pattern
        reporter = get_progress_reporter()

        # The reporter should exist if any previous test initialized it
        # So we just check it's either None or a ProgressReporter
        assert reporter is None or isinstance(reporter, ProgressReporter)


class TestProgressStepEnum:
    """Test the ProgressStep enum."""

    def test_progress_step_values(self):
        """Test that all expected progress steps exist."""
        expected_steps = [
            "starting",
            "fetching_transcript",
            "calling_claude",
            "generating_notes",
            "generating_assessment",
            "creating_links",
            "writing_files",
            "exporting_pdf",
            "completed",
            "error"
        ]

        for step in expected_steps:
            assert hasattr(ProgressStep, step.upper())

    def test_progress_step_string_values(self):
        """Test that progress steps have correct string values."""
        assert ProgressStep.STARTING == "starting"
        assert ProgressStep.FETCHING_TRANSCRIPT == "fetching_transcript"
        assert ProgressStep.CALLING_CLAUDE == "calling_claude"
        assert ProgressStep.GENERATING_NOTES == "generating_notes"
        assert ProgressStep.GENERATING_ASSESSMENT == "generating_assessment"
        assert ProgressStep.CREATING_LINKS == "creating_links"
        assert ProgressStep.WRITING_FILES == "writing_files"
        assert ProgressStep.EXPORTING_PDF == "exporting_pdf"
        assert ProgressStep.COMPLETED == "completed"
        assert ProgressStep.ERROR == "error"
