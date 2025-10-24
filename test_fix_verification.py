#!/usr/bin/env python3
"""
Verify that the Obsidian linker fix works.
"""

import tempfile
from pathlib import Path
from src.yt_study_buddy.obsidian_linker import ObsidianLinker


def test_fixed_linker():
    """Test that linker now creates links with threshold=70."""
    print("\n" + "="*60)
    print("VERIFICATION: Obsidian Linker Fix")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test notes
        ai_dir = base_dir / "AI"
        ai_dir.mkdir(parents=True)

        # Target note to link TO
        target1 = ai_dir / "Neural_Networks.md"
        target1.write_text("""# Neural Networks

## Core Concepts
- Artificial neurons
- Activation functions
- Forward propagation
""", encoding='utf-8')

        # Source note that should GET links
        source = ai_dir / "Deep_Learning_Overview.md"
        source_content = """# Deep Learning Overview

## Introduction
Neural Networks form the foundation of modern AI.
The field has revolutionized machine learning through
deep architectures and powerful training algorithms.

## Applications
Many real-world systems now use neural networks for
classification, regression, and generative tasks.
"""
        source.write_text(source_content, encoding='utf-8')

        # Initialize linker (should default to threshold=70 now)
        linker = ObsidianLinker(base_dir=str(base_dir), subject="AI", global_context=True)

        print(f"\n✓ Linker initialized with threshold: {linker.min_similarity}")

        # Build index
        linker.build_note_index()
        print(f"✓ Index built: {len(linker.note_titles)} notes")

        # Process the source file
        print(f"\n📝 Processing: {source.name}")
        print(f"Original content length: {len(source_content)} chars")

        linker.process_file(source)

        # Check result
        modified_content = source.read_text()
        print(f"Modified content length: {len(modified_content)} chars")

        if modified_content != source_content:
            print("\n✅ SUCCESS: Content was modified!")

            # Count links
            import re
            links = re.findall(r'\[\[([^\]]+)\]\]', modified_content)
            print(f"✅ Links added: {len(links)}")
            for link in links:
                print(f"   - [[{link}]]")

            # Show a snippet
            print(f"\n📄 Modified content snippet:")
            lines = modified_content.split('\n')
            for line in lines[:15]:
                if '[[' in line:
                    print(f"   {line}")

            return True
        else:
            print("\n❌ FAIL: Content was NOT modified")
            print("The fix did not work as expected.")
            return False


if __name__ == "__main__":
    success = test_fixed_linker()
    print("\n" + "="*60)
    if success:
        print("VERIFICATION PASSED ✅")
    else:
        print("VERIFICATION FAILED ❌")
    print("="*60 + "\n")
