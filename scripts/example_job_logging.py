#!/usr/bin/env python3
"""
Example of JSON job logging with the stateless pipeline.

This demonstrates how job results (including errors) are appended to a JSON array.
"""
import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, 'src')

from yt_study_buddy.video_job import VideoProcessingJob, create_job_from_url
from yt_study_buddy.job_logger import JobLogger, create_default_logger


def example_basic_logging():
    """Basic example: Create and log jobs."""
    logger.info("=" * 60)
    logger.info("BASIC JOB LOGGING EXAMPLE")
    logger.info("=" * 60)


    # Create logger (will create notes/processing_log.json)
    logger = create_default_logger(Path('notes'))
    logger.success(f"✓ Logger created: {logger.log_file}")


    # Create some example jobs
    jobs = [
        create_job_from_url(
            "https://youtu.be/example1",
            "example1",
            subject="AI",
            worker_id=0
        ),
        create_job_from_url(
            "https://youtu.be/example2",
            "example2",
            subject="AI",
            worker_id=1
        ),
    ]

    # Simulate processing
    logger.debug("Simulating job processing...")


    # Job 1: Success
    jobs[0].video_title = "Introduction to Machine Learning"
    jobs[0].transcript = "This is a sample transcript..."
    jobs[0].study_notes = "# Study Notes\n\nKey concepts..."
    jobs[0].notes_filepath = Path('notes/AI/Introduction_to_Machine_Learning.md')
    jobs[0].processing_duration = 45.2
    jobs[0].mark_completed(45.2)
    jobs[0].timings = {
        'fetch_transcript': 5.2,
        'generate_notes': 25.0,
        'write_files': 0.5,
        'export_pdfs': 14.5
    }

    # Job 2: Failed
    jobs[1].video_title = "Advanced Neural Networks"
    jobs[1].transcript = "Sample transcript..."
    jobs[1].processing_duration = 12.3
    jobs[1].mark_failed("API rate limit exceeded", jobs[1].stage)
    jobs[1].timings = {
        'fetch_transcript': 8.3,
        'generate_notes': 4.0
    }

    # Log jobs
    for job in jobs:
        logger.log_job(job)
        status = "✓ Success" if job.success else "✗ Failed"
        logger.debug(f"{status}: {job.video_title} ({job.processing_duration:.1f}s)")
        if job.error:
            logger.error(f"  Error: {job.error}")


    logger.success(f"✓ Logged {len(jobs)} jobs to {logger.log_file}")



def example_view_logs():
    """Example: Read and analyze logs."""
    logger.info("=" * 60)
    logger.info("VIEWING LOGGED JOBS")
    logger.info("=" * 60)


    logger = create_default_logger(Path('notes'))

    # Get all jobs
    all_jobs = logger.get_all_jobs()
    logger.info(f"Total jobs logged: {len(all_jobs)}")


    # Get statistics
    stats = logger.get_statistics()
    logger.info("Statistics:")
    logger.success(f"  Successful: {stats['successful']}")
    logger.error(f"  Failed: {stats['failed']}")
    logger.success(f"  Success rate: {stats['success_rate']*100:.1f}%")
    if stats['average_duration']:
        logger.info(f"  Average duration: {stats['average_duration']:.1f}s")
    logger.info(f"  Total files created: {stats['total_files_created']}")


    if stats['error_types']:
        logger.error("Error types:")
        for error_type, count in stats['error_types'].items():
            logger.error(f"  {error_type}: {count}")
    

    # Show failed jobs
    failed = logger.get_failed_jobs()
    if failed:
        logger.error(f"Failed jobs ({len(failed)}):")
        for job in failed:
            logger.error(f"  - {job['video_title']}: {job['error']}")
    

    # Show successful jobs
    successful = logger.get_successful_jobs()
    if successful:
        logger.success(f"Successful jobs ({len(successful)}):")
        for job in successful:
            files = job.get('total_files', 0)
            logger.info(f"  - {job['video_title']} ({files} files)")
    


def example_json_structure():
    """Show what the JSON structure looks like."""
    logger.info("=" * 60)
    logger.info("JSON STRUCTURE")
    logger.info("=" * 60)


    job = create_job_from_url(
        "https://youtu.be/example",
        "example",
        subject="AI"
    )
    job.video_title = "Example Video"
    job.transcript = "Sample transcript"
    job.study_notes = "Sample notes"
    job.notes_filepath = Path('notes/AI/Example_Video.md')
    job.processing_duration = 30.0
    job.mark_completed(30.0)

    import json
    logger.info("Example job as JSON:")
    logger.info(json.dumps(job.to_json(), indent=2))



def example_batch_logging():
    """Example: Log multiple jobs at once."""
    logger.info("=" * 60)
    logger.info("BATCH LOGGING")
    logger.info("=" * 60)


    logger = create_default_logger(Path('notes'))

    # Create batch of jobs
    jobs = [
        create_job_from_url(f"https://youtu.be/video{i}", f"video{i}")
        for i in range(5)
    ]

    # Simulate processing
    for i, job in enumerate(jobs):
        job.video_title = f"Video {i+1}"
        job.processing_duration = 30.0 + i * 5
        if i < 4:  # 4 success, 1 failure
            job.mark_completed(job.processing_duration)
        else:
            job.mark_failed("Network timeout")

    # Log entire batch at once (more efficient)
    logger.log_jobs_batch(jobs)

    logger.success(f"✓ Batch logged {len(jobs)} jobs")



if __name__ == '__main__':

    logger.info("JSON JOB LOGGING EXAMPLES")
    logger.info("=" * 60)


    # Clear existing log for clean demo
    logger = create_default_logger(Path('notes'))
    logger.clear_log()
    logger.success("✓ Cleared existing logs for clean demo")


    # Run examples
    example_basic_logging()
    example_view_logs()
    example_json_structure()
    example_batch_logging()

    # Final stats
    example_view_logs()

    logger.info("=" * 60)
    logger.success("DONE")
    logger.info("=" * 60)

    logger.info(f"View the JSON log at: {logger.log_file}")

    logger.info("Useful queries:")
    logger.info("  # View all jobs")
    logger.info(f"  cat {logger.log_file} | jq '.'")

    logger.info("  # Count jobs by status")
    logger.success(f"  cat {logger.log_file} | jq '[.[] | .success] | group_by(.) | map({{status: .[0], count: length}})'")

    logger.error("  # Show failed jobs only")
    logger.success(f"  cat {logger.log_file} | jq '[.[] | select(.success == false)]'")

    logger.success("  # Average duration of successful jobs")
    logger.success(f"  cat {logger.log_file} | jq '[.[] | select(.success == true) | .processing_duration] | add / length'")

