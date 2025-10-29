# Obsidian Linker - Root Cause Analysis

## Issue Summary

The Obsidian linker is **NOT working** - it's not creating any `[[links]]` between related notes, despite the infrastructure being in place and the `global_context` parameter flowing through correctly.

## Root Cause

**The similarity threshold is too strict** (85%) combined with **phrase extraction issues**.

### Problem 1: Similarity Threshold Too High

The linker uses `min_similarity=85` as the default threshold for fuzzy matching (obsidian_linker.py:24).

**Test Results:**
- `"Neural Networks"` vs `"Neural Networks Introduction"` → **70% match** (below 85% threshold)
- `"Deep Learning"` vs `"Deep Learning Basics"` → **79% match** (below 85% threshold)
- `"Backpropagation"` vs `"Backpropagation Algorithm"` → **75% match** (below 85% threshold)

**All realistic matches fail to meet the threshold!**

### Problem 2: Phrase Extraction Issues

The phrase extraction logic (obsidian_linker.py:147-167) has limitations:

1. **Only extracts capitalized phrases** - Misses common lowercase technical terms
2. **Splits on sentence boundaries poorly** - Creates invalid phrases like `"Overview\nModern"` and `"Uses\nTransfer"`
3. **Requires exact capitalization** - `"neural networks"` (lowercase) won't be extracted even though it's in the text

**Example from test:**
```
Text: "Modern applications use Neural Networks and Deep Learning"
Extracted: ['Deep Learning', 'Overview\nModern', 'Applications', 'Neural Networks']
```

The phrase `"Neural Networks"` is extracted, but it doesn't match `"Neural Networks Introduction"` with sufficient score.

### Problem 3: Validation Too Strict

The validation check (obsidian_linker.py:169-190) filters out phrases containing certain markers, which can eliminate valid matches.

## Code Flow Verification

✅ **CLI arguments flow correctly:**
- `cli.py:441` - `global_context=not args.subject_only`
- `cli.py:56` - Passed to `ObsidianLinker(base_dir, subject, global_context)`
- `processing_pipeline.py:444` - `process_obsidian_links()` is called
- `obsidian_linker.py:20` - Parameters stored correctly

✅ **Index building works:**
- Global mode: Scans all subjects ✅
- Subject-only mode: Scans only specified subject ✅
- Test showed 3 notes indexed across 2 subjects in global mode ✅

❌ **Link creation fails:**
- `find_potential_links()` returns 0 matches
- `apply_links()` has nothing to apply
- Files are not modified

## Detailed Findings

### File: `obsidian_linker.py`

**Line 24:** Threshold too high
```python
def __init__(self, base_dir="Study notes", subject=None, global_context=True, min_similarity=85):
    #                                                                                     ^^^ TOO HIGH
```

**Line 100-105:** Sentence splitting is naive
```python
sentences = re.split(r'[.!?]+', content)
# This doesn't handle newlines properly, creates malformed phrases
```

**Line 147-167:** Phrase extraction logic
```python
def _extract_phrases(self, sentence):
    # Only looks for capitalized phrases - misses lowercase technical terms
    capitalized_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sentence)
```

**Line 116-122:** Fuzzy matching with high threshold
```python
matches = process.extractBests(
    phrase, available_titles.keys(),
    scorer=fuzz.token_sort_ratio,
    score_cutoff=self.min_similarity,  # 85 is too high!
    limit=3
)
```

## Fix Complexity Assessment

### Effort Level: **LOW to MEDIUM**

### Required Changes:

#### 1. **Lower the Default Threshold** (5 minutes)
**Impact:** HIGH
**Complexity:** TRIVIAL

```python
# obsidian_linker.py:24
def __init__(self, base_dir="Study notes", subject=None, global_context=True, min_similarity=70):
    #                                                                                     ^^^ Change to 70
```

**Rationale:** 70% threshold would catch:
- "Neural Networks" → "Neural Networks Introduction" (70%)
- "Deep Learning" → "Deep Learning Basics" (79%)
- "Backpropagation" → "Backpropagation Algorithm" (75%)

#### 2. **Improve Phrase Extraction** (30-60 minutes)
**Impact:** HIGH
**Complexity:** MEDIUM

Current issues:
- Misses lowercase phrases
- Creates malformed phrases from newlines
- Doesn't extract noun phrases intelligently

**Proposed fixes:**
```python
def _extract_phrases(self, sentence):
    """Extract potential linkable phrases from a sentence."""
    phrases = []

    # Clean sentence first - replace newlines with spaces
    sentence = sentence.replace('\n', ' ').strip()

    # Skip empty or header lines
    if not sentence or sentence.startswith('#'):
        return []

    # Extract capitalized multi-word phrases (existing logic - keep)
    capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', sentence)
    phrases.extend([p for p in capitalized if len(p) > 3])

    # NEW: Extract technical terms (2-4 words, any case)
    # Matches: "neural networks", "deep learning", "machine learning" etc
    technical_terms = re.findall(
        r'\b(?:[a-z]+\s+){1,3}[a-z]+\b',
        sentence.lower()
    )
    # Filter for common multi-word technical phrases
    technical = [
        p for p in technical_terms
        if len(p) > 8 and ' ' in p  # Must be multi-word and substantial
        and p.split()[0] not in ['the', 'and', 'for', 'with', 'from']  # Filter common words
    ]
    phrases.extend(technical)

    # Keep existing logic for quoted terms, parenthetical, etc.
    # ...

    return list(set(phrases))
```

#### 3. **Add CLI Parameter** (10 minutes - OPTIONAL)
**Impact:** LOW
**Complexity:** TRIVIAL

Allow users to tune the threshold:

```python
# cli.py
parser.add_argument('--link-threshold', type=int, default=70,
                   help='Similarity threshold for Obsidian links (default: 70)')

# Pass to linker:
self.obsidian_linker = ObsidianLinker(base_dir, subject, global_context,
                                      min_similarity=args.link_threshold)
```

#### 4. **Improve Sentence Splitting** (15 minutes)
**Impact:** MEDIUM
**Complexity:** LOW

```python
# obsidian_linker.py:100
def find_potential_links(self, content, exclude_current_title=None):
    # ...

    # Better sentence splitting that handles newlines
    # First normalize newlines in paragraphs
    normalized = re.sub(r'\n+', ' ', content)  # Replace newlines with spaces
    normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace

    # Then split on sentence boundaries
    sentences = re.split(r'[.!?]+\s+', normalized)

    for sentence in sentences:
        if len(sentence.strip()) < 10:
            continue
        # ...
```

## Recommended Fix Priority

### Phase 1: Quick Win (15 minutes total)
1. ✅ **Lower threshold to 70%** (5 min)
2. ✅ **Fix sentence splitting/newline handling** (10 min)

**Expected impact:** Should immediately start creating links between related notes.

### Phase 2: Improvement (45 minutes)
3. ✅ **Improve phrase extraction** (30 min)
4. ✅ **Add CLI parameter for threshold** (10 min)
5. ✅ **Add test suite** (5 min - use existing test_linker_detailed.py)

**Expected impact:** Better quality links, more flexibility for users.

## Testing Strategy

1. Use existing test files in `test_obsidian_linker.py` and `test_linker_detailed.py`
2. Create test notes across multiple subjects
3. Verify links are created with new threshold
4. Check that global vs subject-only modes work correctly

## Verification Steps

After implementing fixes:

```bash
# Run diagnostic
cd ytstudybuddy-linker-fix
uv run python test_obsidian_linker.py

# Expected output:
#  ✅ Content was modified (links added)
#  Links added: 2-4
#  - [[Neural Networks Introduction]]
#  - [[Deep Learning Basics]]

# Test with real data
uv run yt-study-buddy --subject "AI" https://youtube.com/watch?v=...
# Check that generated notes have [[links]] to existing notes
```

## Summary

- **Root Cause:** Similarity threshold too high (85%) + phrase extraction issues
- **Impact:** Feature completely non-functional
- **Fix Complexity:** LOW (Phase 1) to MEDIUM (Phase 2)
- **Estimated Time:** 15 minutes for basic fix, 1 hour for complete solution
- **Priority:** HIGH (this is a key feature mentioned in README)

The good news: The infrastructure is all there and working correctly. It's just the matching parameters that need tuning!
