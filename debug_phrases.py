#!/usr/bin/env python3
from src.yt_study_buddy.obsidian_linker import ObsidianLinker

content = """# Deep Learning Overview

## Introduction
Neural Networks form the foundation of modern AI.
The field has revolutionized machine learning through
deep architectures and powerful training algorithms.
"""

linker = ObsidianLinker(base_dir="test", min_similarity=70)

# Test sentence splitting
import re
normalized = re.sub(r'\n+', ' ', content)
normalized = re.sub(r'\s+', ' ', normalized)
sentences = re.split(r'[.!?]+\s+', normalized)

print("Sentences:")
for i, sent in enumerate(sentences):
    print(f"{i}: {sent}")
    phrases = linker._extract_phrases(sent)
    print(f"   Phrases: {phrases}\n")
