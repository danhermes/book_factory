*.tex vs *.sty — What's the Difference?
✅ .tex = Content or full document
A LaTeX source file: it's the main entry point for a document.

Contains \documentclass, content, and layout in one place.

What you actually compile (pdflatex mybook.tex).

✅ .sty = Style module
A package of layout macros and settings.

You \usepackage{mylayout} in a .tex file to load it.

Keeps your layout reusable across books or projects.

Lives in the same folder or a TeX path.

✅ When to use .sty
When your layout logic is stable and shared across documents.

When your Markdown-to-TeX pipeline just wants to inject content.

When you're separating presentation from content.

You’ll end up with:

promptpower_layout.sty → all layout config

book_main.tex → loads layout, inserts converted content

🛠️ MD → LaTeX → PDF Pipeline Plan
🔁 Overall Flow:
scss
Copy
Edit
Markdown → (Pandoc or custom converter) → LaTeX → PDF
📁 Suggested Structure
pgsql
Copy
Edit
book_layout/
├── promptpower_layout.sty       # layout rules (memoir, margins, fonts, etc)
├── preamble.tex                 # wrapper that loads layout + content
├── chapters/
│   ├── ch1_request.md
│   └── ch2_examples.md
├── build_layout.sh              # script: md → tex → pdf
├── output/
│   └── promptpower.pdf