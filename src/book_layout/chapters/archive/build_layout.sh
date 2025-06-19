#!/bin/bash

set -e

# Compile all chapters into one tex file
echo '\input{chatgpt_layout.sty}' > full.tex
echo '\begin{document}' >> full.tex

for chapter in chapters/*.md; do
    base=$(basename "$chapter" .md)
    pandoc "$chapter" -o "chapters/${base}.tex" --from markdown --to latex
    echo "\input{chapters/${base}.tex}" >> full.tex
done

echo '\end{document}' >> full.tex

# Compile PDF
pdflatex -output-directory output full.tex
