#!/usr/bin/env python3
"""
Detailed diagnostic to understand why Obsidian linker isn't creating links.
"""

import tempfile
from pathlib import Path
from src.yt_study_buddy.obsidian_linker import ObsidianLinker


def test_phrase_extraction():
    """Test the phrase extraction logic."""
    print("\n" + "="*60)
    print("DETAILED ANALYSIS: Phrase Extraction")
    print("="*60)

    test_content = """# AI Applications

## Overview
Modern applications use Neural Networks and Deep Learning
to solve complex problems. Backpropagation is the key
training algorithm.

## Real-world Uses
Transfer learning enables fast model adaptation.
"""

    linker = ObsidianLinker(base_dir="test", global_context=True)

    # Test phrase extraction
    sentences = test_content.split('.')
    print(f"\nTest content has {len(sentences)} sentences")

    for i, sentence in enumerate(sentences[:5], 1):
        if sentence.strip():
            print(f"\nSentence {i}: {sentence.strip()[:100]}")
            phrases = linker._extract_phrases(sentence)
            print(f"  Extracted phrases: {phrases}")


def test_fuzzy_matching():
    """Test fuzzy matching between phrases and titles."""
    print("\n" + "="*60)
    print("DETAILED ANALYSIS: Fuzzy Matching")
    print("="*60)

    from fuzzywuzzy import fuzz, process

    # Simulated note titles
    titles = [
        "Neural Networks Introduction",
        "Deep Learning Basics",
        "Backpropagation Algorithm"
    ]

    # Phrases from content
    test_phrases = [
        "Neural Networks",
        "Deep Learning",
        "Backpropagation",
        "Transfer learning",
        "Modern applications"
    ]

    print(f"\nAvailable titles: {titles}")
    print(f"\nTest phrases: {test_phrases}\n")

    for phrase in test_phrases:
        matches = process.extractBests(
            phrase,
            titles,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=85,  # Default threshold
            limit=3
        )
        print(f"Phrase: '{phrase}'")
        if matches:
            for title, score in matches:
                print(f"  ✅ Match: '{title}' (score: {score})")
        else:
            print(f"  ❌ No matches above threshold (85)")

        # Show best match even if below threshold
        all_matches = process.extractBests(
            phrase,
            titles,
            scorer=fuzz.token_sort_ratio,
            limit=1
        )
        if all_matches:
            title, score = all_matches[0]
            if score < 85:
                print(f"     (Best match: '{title}' with score {score}, below threshold)")


def test_link_application():
    """Test the complete link application process."""
    print("\n" + "="*60)
    print("DETAILED ANALYSIS: Full Link Application Process")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test notes
        ai_dir = base_dir / "AI"
        ai_dir.mkdir(parents=True)

        # Note to link TO
        target_note = ai_dir / "Neural_Networks.md"
        target_note.write_text("""# Neural Networks

## Core Concepts
- Artificial neurons
- Activation functions
""", encoding='utf-8')

        # Note that should GET links
        source_note = ai_dir / "Applications.md"
        source_content = """# Applications

## Overview
Neural Networks are used everywhere.
We use neural networks for classification.
"""
        source_note.write_text(source_content, encoding='utf-8')

        # Initialize linker
        linker = ObsidianLinker(base_dir=str(base_dir), subject="AI", global_context=True)
        linker.build_note_index()

        print(f"\nIndexed notes: {list(linker.note_titles.keys())}")

        # Read source and find potential links
        content = source_note.read_text()
        print(f"\nSource content:\n{content}")

        potential_links = linker.find_potential_links(content, exclude_current_title="Applications")

        print(f"\nPotential links found: {len(potential_links)}")
        for link in potential_links:
            print(f"  - Phrase: '{link['phrase']}' -> [[{link['title']}]] (score: {link['score']})")

        # Apply links
        print("\nApplying links...")
        modified_content = linker.apply_links(content, source_note, current_title="Applications")

        if modified_content != content:
            print("✅ Content was modified!")
            print(f"\nModified content:\n{modified_content}")
        else:
            print("❌ Content was NOT modified")


def test_with_lower_threshold():
    """Test with lower similarity threshold to see what matches we get."""
    print("\n" + "="*60)
    print("DETAILED ANALYSIS: Lower Threshold Test (70% instead of 85%)")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test notes
        ai_dir = base_dir / "AI"
        ai_dir.mkdir(parents=True)

        # Note to link TO
        target_note = ai_dir / "Neural_Networks_Introduction.md"
        target_note.write_text("""# Neural Networks Introduction

## Core Concepts
- Artificial neurons
""", encoding='utf-8')

        # Note that should GET links
        source_note = ai_dir / "Applications.md"
        source_content = """# Applications

## Overview
Modern applications use Neural Networks and deep learning.
"""
        source_note.write_text(source_content, encoding='utf-8')

        # Initialize linker with LOWER threshold
        linker = ObsidianLinker(
            base_dir=str(base_dir),
            subject="AI",
            global_context=True,
            min_similarity=70  # Lower threshold
        )
        linker.build_note_index()

        print(f"\nIndexed notes: {list(linker.note_titles.keys())}")

        # Find potential links
        content = source_note.read_text()
        potential_links = linker.find_potential_links(content, exclude_current_title="Applications")

        print(f"\nPotential links found (threshold=70): {len(potential_links)}")
        for link in potential_links:
            print(f"  - Phrase: '{link['phrase']}' -> [[{link['title']}]] (score: {link['score']})")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("OBSIDIAN LINKER - DETAILED DIAGNOSTICS")
    print("="*60)

    test_phrase_extraction()
    test_fuzzy_matching()
    test_link_application()
    test_with_lower_threshold()

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60 + "\n")
