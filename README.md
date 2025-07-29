# Book Writing CLI

This CLI tool provides a unified interface for the book writing flow application, allowing you to generate outlines and chapter content for your book. It uses the existing crews and scripts in the project.

## Installation

Ensure you have all the required dependencies installed:

```bash
pip install crewai crewai-tools
```

Make the CLI script executable:

```bash
chmod +x book_cli.py
```

## Usage

The CLI provides three main commands:

### 1. Generate Book Outline

To generate a complete book outline:

```bash
python book_cli.py outline [--topic "Your Book Topic"]
```

To generate an outline for a specific chapter (this will first generate a full book outline and then extract the specified chapter):

```bash
python book_cli.py outline --chapter 1 [--topic "Your Book Topic"]
```

### 2. Generate Chapter Content

To generate content for a specific chapter:

```bash
python book_cli.py write --chapter 1 [--force]
```

The `--force` flag will regenerate the chapter even if it already exists.

### 3. Run Full Book Writing Flow

To run the complete chapter write flow (SKIPS outline generation for no. But typically: outline and then chapters):

```bash
python book_cli.py flow [--chapters "1,2,3" | --chapters "all"] [--topic "Your Book Topic"]
```

## Output Files

All generated files are saved in the following directories:

- Outlines: `output/outlines/`
- Chapters: `output/chapters/`

## How It Works

The CLI is a wrapper around the existing scripts in the project:

1. For outline generation, it uses `src/book_writing_flow/main.py` which utilizes the OutlineCrew
2. For chapter generation, it uses `simple_chapter_generator.py`
3. For the full flow, it combines both of the above

The CLI ensures that all output files are properly organized in the output directories.

## Book Binding

Once you have generated your chapters, you can compile them into a complete book PDF using the book binding script:

```bash
cd src/book_binding
./build_book.sh
```

This script will:
- Combine all chapter files from `output/chapters/clean/`
- Add front and back covers (if available)
- Include front and back matter (if available)
- Generate a table of contents
- Format everything into a professional PDF

The final book will be saved as `output/chapters/clean/final_book.pdf`.

For more details on the book binding process, see the [Book Binding README](src/book_binding/README.md).

## Examples

1. Generate a complete book outline:

```bash
python book_cli.py outline --topic "ChatGPT for Business"
```

2. Generate research and write all chapters for existing outline. (output/outlines/book_outline.json)

```bash
python book_cli.py flow --chapters "all"
```


3. Generate an outline for chapter 3:

```bash
python book_cli.py outline --chapter 3
```

4. Generate content for chapter 2:

```bash
python book_cli.py write --chapter 2
```

5. Force regeneration of chapter 2 even if it already exists:

```bash
python book_cli.py write --chapter 2 --force
```

6. Generate chapters 1, 3, and 5:

```bash
python book_cli.py flow --chapters "1,3,5"
```

7. Generate the entire book:

```bash
python book_cli.py flow --chapters "all"