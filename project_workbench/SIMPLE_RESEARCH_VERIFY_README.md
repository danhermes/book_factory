# Simple Research Verification Tool

This tool provides a quick way to verify that research is being used in the book chapters.

## Overview

The simple research verification tool checks three key aspects:

1. **Research Log Existence**: Verifies that research log files exist for each chapter
2. **Research in Writer Prompt**: Checks if research is being passed to the writer agent in the prompt
3. **Research in Chapter**: Verifies if research findings are used in the chapter content

## How to Use

### Verifying a Single Chapter

To verify research usage for a single chapter:

```bash
python simple_research_verify.py --chapter 1
```

### Verifying All Chapters

To verify research usage for all chapters:

```bash
python simple_research_verify.py
```

## Output

The tool provides a simple output with checkmarks (a...) or crosses (a) for each verification step:

```
Research Verification Results:
==================================================

Chapter 1:
  Research Log Exists: a...
  Research in Writer Prompt: a...
  Research in Chapter: a...
  Overall Verification: a...

Overall Statistics:
  Total Chapters: 1
  Verified Chapters: 1
  Verification Rate: 100.00%
```

## How It Works

1. **Research Log Check**: Looks for research log files in the `output/research` directory
2. **Writer Prompt Check**: Searches log files for evidence of research being passed to the writer agent
3. **Chapter Content Check**: Extracts key phrases from research findings and checks if they appear in the chapter content

## Limitations

- The tool uses simple phrase matching to determine if research is used in the chapter
- It doesn't perform semantic analysis or context analysis
- It may miss cases where research is paraphrased or used in a different context 