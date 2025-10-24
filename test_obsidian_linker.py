#!/usr/bin/env python3
"""
Diagnostic script to test Obsidian linker functionality.

Tests:
1. Index building in global vs subject-only mode
2. Link detection and application
3. Verify that global_context parameter flows through correctly
"""

import os
import tempfile
from pathlib import Path
from src.yt_study_buddy.obsidian_linker import ObsidianLinker


def setup_test_notes(base_dir):
    """Create test note structure."""
    # Create subject directories
    ai_dir = base_dir / "AI"
    ml_dir = base_dir / "Machine Learning"
    ai_dir.mkdir(parents=True)
    ml_dir.mkdir(parents=True)

    # Create sample notes
    note1 = ai_dir / "Neural_Networks_Intro.md"
    note1.write_text("""# Neural Networks Introduction

## Core Concepts
- Artificial neurons and activation functions
- Backpropagation algorithm
- Deep learning architectures

## Key Points
Neural networks are fundamental to modern AI systems.
""", encoding='utf-8')

    note2 = ml_dir / "Deep_Learning_Basics.md"
    note2.write_text("""# Deep Learning Basics

## Core Concepts
- Convolutional Neural Networks
- Recurrent Neural Networks
- Transfer learning

## Key Points
Deep learning uses neural networks with multiple layers.
""", encoding='utf-8')

    # Create a new note that should get links
    note3 = ai_dir / "AI_Applications.md"
    note3.write_text("""# AI Applications

## Overview
Modern applications use Neural Networks and Deep Learning
to solve complex problems. Backpropagation is the key
training algorithm.

## Real-world Uses
Transfer learning enables fast model adaptation.
""", encoding='utf-8')

    return note1, note2, note3


def test_global_context():
    """Test that global context allows cross-subject linking."""
    print("\n" + "="*60)
    print("TEST 1: Global Context (should link across subjects)")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        note1, note2, note3 = setup_test_notes(base_dir)

        # Initialize linker with GLOBAL context
        linker = ObsidianLinker(
            base_dir=str(base_dir),
            subject="AI",  # Current subject
            global_context=True  # KEY: Should allow cross-subject links
        )

        # Build index
        linker.build_note_index()
        stats = linker.get_stats()

        print(f"\n📊 Index Stats:")
        print(f"   Total notes indexed: {stats['total_notes']}")
        print(f"   Context: {stats['context']}")
        print(f"   Subjects found: {stats.get('subject_count', 0)}")
        if stats.get('subjects'):
            print(f"   Subject list: {', '.join(stats['subjects'])}")

        print(f"\n📝 Indexed Notes:")
        for title, data in linker.note_titles.items():
            print(f"   - {title} ({data['subject']})")

        # Process the new note
        print(f"\n🔗 Processing: {note3.name}")
        original_content = note3.read_text()
        linker.process_file(note3)
        modified_content = note3.read_text()

        # Check for links
        print(f"\n📄 Content Analysis:")
        if modified_content != original_content:
            print("   ✅ Content was modified (links added)")
            print(f"\n   Original length: {len(original_content)} chars")
            print(f"   Modified length: {len(modified_content)} chars")

            # Show added links
            import re
            links = re.findall(r'\[\[([^\]]+)\]\]', modified_content)
            if links:
                print(f"\n   Links added: {len(links)}")
                for link in links:
                    print(f"      - [[{link}]]")
            else:
                print("   ⚠️  No [[links]] found in content!")
        else:
            print("   ❌ Content NOT modified (no links added)")
            print("   This indicates linking is not working!")


def test_subject_only_context():
    """Test that subject-only context limits linking to same subject."""
    print("\n" + "="*60)
    print("TEST 2: Subject-Only Context (should link within subject only)")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        note1, note2, note3 = setup_test_notes(base_dir)

        # Initialize linker with SUBJECT-ONLY context
        linker = ObsidianLinker(
            base_dir=str(base_dir),
            subject="AI",  # Current subject
            global_context=False  # KEY: Should only link within AI subject
        )

        # Build index
        linker.build_note_index()
        stats = linker.get_stats()

        print(f"\n📊 Index Stats:")
        print(f"   Total notes indexed: {stats['total_notes']}")
        print(f"   Context: {stats['context']}")

        print(f"\n📝 Indexed Notes:")
        for title, data in linker.note_titles.items():
            print(f"   - {title} ({data['subject']})")

        # Expected: Should only index "Neural Networks Introduction" (AI subject)
        # Should NOT index "Deep Learning Basics" (Machine Learning subject)

        # Process the new note
        print(f"\n🔗 Processing: {note3.name}")
        linker.process_file(note3)
        modified_content = note3.read_text()

        # Check for links
        import re
        links = re.findall(r'\[\[([^\]]+)\]\]', modified_content)
        print(f"\n📄 Links added: {len(links)}")
        if links:
            for link in links:
                print(f"   - [[{link}]]")


def test_fuzzywuzzy_available():
    """Test if fuzzywuzzy is available."""
    print("\n" + "="*60)
    print("TEST 3: Dependencies Check")
    print("="*60)

    try:
        from fuzzywuzzy import fuzz, process
        print("✅ fuzzywuzzy is installed")

        # Test basic functionality
        score = fuzz.token_sort_ratio("Neural Networks", "Neural Networks Introduction")
        print(f"   Sample match score: {score}")

        return True
    except ImportError:
        print("❌ fuzzywuzzy is NOT installed")
        print("   Install with: uv pip install fuzzywuzzy python-Levenshtein")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("OBSIDIAN LINKER DIAGNOSTIC TESTS")
    print("="*60)

    # Check dependencies first
    has_fuzzy = test_fuzzywuzzy_available()

    if not has_fuzzy:
        print("\n⚠️  WARNING: fuzzywuzzy not available, linking will not work!")
        print("Install it to enable linking functionality.\n")

    # Run tests
    test_global_context()
    test_subject_only_context()

    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60 + "\n")
