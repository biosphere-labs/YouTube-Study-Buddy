# Refactoring Task: Remove Legacy Parallel Processing Code

## Context

Please read the `ARCHITECTURE.md` file in this repository carefully. It contains a detailed analysis of how this CLI tool integrates with AWS Lambda functions.

## Problem Statement

This repository (YouTube Study Buddy CLI) contains extensive parallel processing infrastructure that is **no longer necessary** because:

1. **AWS Lambda handles concurrency automatically** - Each Lambda instance processes one video independently
2. **SQS provides queuing** - The message queue already handles job distribution
3. **Simplicity needed** - The parallel processing code adds unnecessary complexity for Lambda deployment

## Current Architecture Issue

As documented in ARCHITECTURE.md under "Legacy Components (To Be Removed)", the following components were designed for standalone batch processing but are NOT used by the Lambda integration:

### Components to Remove

1. **Worker Pool Management** (`parallel_processor.py`)
   - `ParallelVideoProcessor` class
   - Thread pool executor logic
   - Worker coordination

2. **Job Management** (`video_job.py`)
   - In-memory job queue
   - Job state tracking (mostly redundant with DynamoDB)
   - Note: Keep only the `VideoProcessingJob` data class if Lambda still uses it

3. **Multi-Video Coordinator** (`video_processor.py`)
   - Batch video processing logic
   - May duplicate functionality from processing_pipeline.py

4. **Tor Coordinator** (in `tor_transcript_fetcher.py`)
   - `SingleTorCoordinator` class
   - Synchronized access to single Tor daemon
   - Cooldown management for workers
   - Note: Keep the base `TorTranscriptFetcher` class

5. **Docker Compose Parallel Configuration**
   - `docker-compose.parallel.yml`
   - Multi-worker container setup

6. **CLI Batch Mode** (in `cli.py`)
   - `--parallel` flag and related logic
   - `--workers` flag
   - Worker factory functions
   - Thread locks (`_file_lock`, `_kg_lock`)

### Components to Keep

**Core Processing Logic** (used by Lambda):
- `processing_pipeline.py` - Single video processing pipeline
- `langgraph_workflow.py` - Workflow orchestration
- `workflow_nodes.py` - Individual processing steps
- `workflow_state.py` - State management
- `video_processor.py` - If it only contains single-video logic
- `study_notes_generator.py` - AI note generation
- `transcript_provider.py` - Transcript extraction
- `tor_transcript_fetcher.py` - Base Tor client (remove coordinator)

## Why This Refactoring Is Important

### 1. Reduces Lambda Package Size
- Smaller deployment package = faster cold starts
- Current package includes unused dependencies for threading/multiprocessing
- Smaller package = easier to stay under Lambda's 250MB limit

### 2. Eliminates Confusion
- Developers (and Claude Code) won't be confused about which code is actually used
- Clear separation between "core processing" and "CLI wrapper"
- Easier to understand the Lambda integration

### 3. Simplifies Maintenance
- Less code to maintain and test
- No need to keep parallel processing code up-to-date
- Reduces cognitive load when making changes

### 4. Improves Code Quality
- Single Responsibility Principle: CLI does one video at a time
- Lambda Layer will be smaller and faster to deploy
- Easier to write tests for core functionality

### 5. Prevents Bugs
- No risk of thread safety issues in Lambda (Lambda is single-threaded per instance)
- No risk of accidentally invoking parallel mode in Lambda context
- Clearer error handling paths

## Refactoring Approach

Please analyze the codebase and create a refactoring plan that:

### Phase 1: Analysis
1. **Identify dependencies**: Which files import `parallel_processor.py`, `video_job.py`, etc.?
2. **Check Lambda usage**: Verify what the `process_video` Lambda actually imports from this package
3. **Document kept vs. removed**: Create a clear list of what stays and what goes

### Phase 2: Deprecation
1. **Mark as deprecated**: Add deprecation warnings to parallel processing code
2. **Update CLI help**: Remove references to `--parallel` and `--workers` flags
3. **Add migration guide**: Document how users should use SQS + Lambda instead

### Phase 3: Removal
1. **Remove files**: Delete `parallel_processor.py`, worker coordination code
2. **Update imports**: Remove imports of deleted modules
3. **Simplify CLI**: Remove parallel-related flags and logic from `cli.py`
4. **Clean up**: Remove thread locks, worker factories, Tor coordinator

### Phase 4: Simplification
1. **Simplify `cli.py`**: Focus on single-video processing only
2. **Update docs**: Reflect that this is now a single-video processing library
3. **Update tests**: Remove parallel processing tests
4. **Update README**: Explain Lambda-first architecture

## Suggested Implementation Order

1. **Start with `cli.py`**:
   - Remove `--parallel`, `--workers` flags
   - Remove `ParallelVideoProcessor` initialization
   - Remove worker factory logic
   - Simplify `process_urls()` to always process sequentially

2. **Remove parallel infrastructure**:
   - Delete `parallel_processor.py`
   - Remove `SingleTorCoordinator` from `tor_transcript_fetcher.py`
   - Delete `docker-compose.parallel.yml`

3. **Check `video_job.py`**:
   - If Lambda uses `VideoProcessingJob` data class, keep it
   - Remove job queue management if present
   - Simplify to just data model

4. **Update dependencies**:
   - Remove threading/multiprocessing dependencies from `pyproject.toml` if unused
   - Update documentation

5. **Test Lambda integration**:
   - Ensure Lambda can still import required modules
   - Verify single-video processing works
   - Check Lambda Layer build process

## Expected Outcomes

After refactoring:

1. **Simplified CLI**: Only processes one video at a time
   ```bash
   # Old (deprecated)
   youtube-study-buddy --parallel --workers 5 urls.txt

   # New (simplified)
   youtube-study-buddy https://youtube.com/watch?v=xyz
   ```

2. **Clearer purpose**: "Single-video processing library used by Lambda"

3. **Smaller codebase**: Estimated 20-30% reduction in code

4. **Better Lambda integration**: Faster cold starts, smaller package

## Questions to Answer

Before starting, please analyze and answer:

1. Does `video_job.py` contain any logic actually used by Lambda?
2. Are there any tests that specifically test parallel processing?
3. Does the frontend documentation reference `--parallel` mode?
4. Are there any environment variables or configs related to parallel processing?
5. What is the current Lambda package size, and how much will this reduce it?

## Success Criteria

The refactoring is complete when:

- [ ] All parallel processing code is removed or deprecated
- [ ] CLI runs successfully in single-video mode
- [ ] Lambda integration still works (check `process_video` handler)
- [ ] No references to `--parallel` or `--workers` in help text
- [ ] Documentation updated to reflect Lambda-first architecture
- [ ] Tests pass (remove parallel-specific tests)
- [ ] Lambda package size is reduced

## Important Notes

- **Do NOT remove** the core processing pipeline (`processing_pipeline.py`, `langgraph_workflow.py`)
- **Do NOT change** the Lambda handler in the infrastructure repo (separate repo)
- **Do verify** what Lambda actually imports before removing anything
- **Do update** ARCHITECTURE.md after refactoring to remove "Legacy Components" section

## Request to Claude Code

Please read ARCHITECTURE.md, then:

1. Analyze the current codebase structure
2. Create a detailed refactoring plan with specific file changes
3. Identify all imports of parallel processing code
4. Propose a safe removal strategy
5. Estimate the impact on Lambda package size
6. Create a checklist of changes needed

Focus on making this CLI a clean, simple, single-video processing library that Lambda can easily import and use.
