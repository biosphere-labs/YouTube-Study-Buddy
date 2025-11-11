"""
Tests for LangGraph workflow migration.
"""
import sys
from pathlib import Path
import pytest

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
def test_workflow_imports():
    """Test that LangGraph workflow modules can be imported."""
    try:
        from yt_study_buddy.workflow_state import VideoProcessingState
        from yt_study_buddy.workflow_nodes import (
            categorize_node,
            fetch_transcript_node,
            generate_notes_node,
            generate_assessment_node,
            write_files_node,
            obsidian_links_node,
            export_pdf_node,
            log_job_node
        )
        from yt_study_buddy.langgraph_workflow import (
            create_workflow,
            compile_workflow,
            process_video_with_langgraph,
            should_categorize,
            should_generate_assessment,
            should_export_pdf
        )

        print("✓ All LangGraph workflow modules imported successfully")

    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


@pytest.mark.unit
def test_conditional_edge_functions():
    """Test conditional edge decision functions."""
    from yt_study_buddy.langgraph_workflow import (
        should_categorize,
        should_generate_assessment,
        should_export_pdf
    )

    # Test should_categorize
    state1 = {'auto_categorize': True, 'subject': None}
    assert should_categorize(state1) == "categorize"

    state2 = {'auto_categorize': False, 'subject': None}
    assert should_categorize(state2) == "skip_categorize"

    state3 = {'auto_categorize': True, 'subject': "Math"}
    assert should_categorize(state3) == "skip_categorize"

    # Test should_generate_assessment
    state4 = {'generate_assessment': True}
    assert should_generate_assessment(state4) == "generate_assessment"

    state5 = {'generate_assessment': False}
    assert should_generate_assessment(state5) == "skip_assessment"

    # Test should_export_pdf
    state6 = {'export_pdf': True}
    assert should_export_pdf(state6) == "export_pdf"

    state7 = {'export_pdf': False}
    assert should_export_pdf(state7) == "skip_export"

    print("✓ All conditional edge functions work correctly")


@pytest.mark.unit
def test_state_schema():
    """Test VideoProcessingState schema."""
    from yt_study_buddy.workflow_state import VideoProcessingState

    # Create a minimal state
    state: VideoProcessingState = {
        'url': 'https://youtu.be/test123',
        'video_id': 'test123',
        'auto_categorize': True,
        'generate_assessment': True,
        'export_pdf': False,
        'output_dir': 'notes',
        'failed': False,
        'completed': False,
        'timings': {},
        'needs_ai_title': False,
        'obsidian_links_added': False,
        'linked_notes': []
    }

    # Verify basic fields
    assert state['video_id'] == 'test123'
    assert state['auto_categorize'] is True
    assert state['failed'] is False

    print("✓ VideoProcessingState schema works correctly")


@pytest.mark.unit
def test_workflow_graph_creation():
    """Test that workflow graph can be created."""
    from yt_study_buddy.langgraph_workflow import create_workflow

    # Create minimal components dict
    components = {
        'video_processor': None,
        'notes_generator': None,
        'assessment_generator': None,
        'obsidian_linker': None,
        'pdf_exporter': None,
        'job_logger': None,
        'filename_sanitizer': lambda x: x,
        'auto_categorizer': None,
        'base_dir': 'notes'
    }

    # This should not raise an exception
    try:
        workflow = create_workflow(components)
        assert workflow is not None
        print("✓ Workflow graph created successfully")

    except Exception as e:
        pytest.fail(f"Workflow graph creation failed: {e}")


@pytest.mark.unit
def test_cli_uses_langgraph():
    """Test that CLI now uses LangGraph workflow."""
    from yt_study_buddy.cli import YouTubeStudyNotes
    import inspect

    # Check that CLI imports the LangGraph function
    source = inspect.getsource(YouTubeStudyNotes)
    assert 'process_video_with_langgraph' in source
    assert 'langgraph_workflow' in source

    print("✓ CLI successfully migrated to use LangGraph workflow")


if __name__ == "__main__":
    # Quick standalone test run
    pytest.main([__file__, "-v"])
