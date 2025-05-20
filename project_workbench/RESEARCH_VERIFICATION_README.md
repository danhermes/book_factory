# Research Verification Tools

This directory contains tools to verify that writers are effectively using research findings in the book chapters.

## Overview

The research verification system consists of two main components:

1. **Research Logging**: Research findings are logged to files in the `output/research` directory during the chapter writing process.
2. **Research Verification**: The verification tools analyze the research logs and chapter content to determine if research findings are being used effectively.

## Files

- `verify_research_usage.py`: Core verification script that analyzes a single research log file and chapter file.
- `verify_all_research.py`: Script to verify research usage for all chapters.
- `RESEARCH_VERIFICATION_README.md`: This file.

## How to Use

### Verifying a Single Chapter

To verify research usage for a single chapter:

```bash
python verify_research_usage.py --research output/research/chapter_1_research.md --chapter output/chapters/chapter_1.md --output output/research_verification/chapter_1_verification.md
```

### Verifying All Chapters

To verify research usage for all chapters:

```bash
python verify_all_research.py --output output/research_verification
```

This will:
1. Find all research log files in `output/research`
2. Find all chapter files in `output/chapters`
3. Verify research usage for each chapter
4. Generate individual verification reports for each chapter
5. Generate a summary report

## Verification Process

The verification process works as follows:

1. **Extract Research Findings**: The script extracts research findings from the research log file.
2. **Extract Chapter Content**: The script extracts the content of each section from the chapter file.
3. **Verify Research Usage**: For each research finding, the script checks if key phrases from the finding are used in the section content.
4. **Generate Report**: The script generates a report showing which research findings were used and which were not.

## Understanding the Reports

The verification reports include:

- **Overall Results**: Total number of research findings, number of used findings, and overall score.
- **Section-by-Section Analysis**: For each section, the number of findings, number of used findings, and score.
- **Findings Details**: For each finding, the source, finding text, usage description, whether it was used, and evidence of usage.

## Limitations

The current verification process has some limitations:

1. **Simple Matching**: The script uses simple phrase matching to determine if a finding is used. This may miss cases where the finding is paraphrased or used in a different context.
2. **No Semantic Analysis**: The script does not perform semantic analysis to determine if the meaning of a finding is used, only if specific phrases are used.
3. **No Context Analysis**: The script does not analyze the context in which findings are used, so it cannot determine if they are used appropriately.

## Future Improvements

Potential improvements to the verification process:

1. **Semantic Similarity**: Use semantic similarity to determine if the meaning of a finding is used, even if the exact phrases are not.
2. **Context Analysis**: Analyze the context in which findings are used to determine if they are used appropriately.
3. **Citation Tracking**: Track citations to research sources to ensure proper attribution.
4. **Integration with Writing Process**: Integrate the verification process with the writing process to provide real-time feedback to writers. 