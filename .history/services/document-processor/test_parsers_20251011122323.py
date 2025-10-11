"""
Test script for document parsers.
Tests each parser with sample documents to verify functionality.
"""

import asyncio
import sys
from pathlib import Path
from io import BytesIO

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers import (
    ParserFactory,
    TxtParser,
    PdfParser,
    DocxParser,
    PptxParser,
    HtmlParser,
    MarkdownParser,
    ParsedDocument,
)


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_result(label: str, value: str, max_length: int = 100):
    """Print a labeled result with truncation"""
    value_str = str(value)
    if len(value_str) > max_length:
        value_str = value_str[:max_length] + "..."
    print(f"  {label:20}: {value_str}")


async def create_test_files():
    """Create sample test files for each format"""
    test_dir = Path(__file__).parent / "test_files"
    test_dir.mkdir(exist_ok=True)

    # Create TXT file
    txt_file = test_dir / "sample.txt"
    txt_file.write_text(
        "Sample Text Document\n\n"
        "This is a test document to verify the text parser.\n"
        "It contains multiple lines and paragraphs.\n\n"
        "Second paragraph with more content."
    )

    # Create HTML file
    html_file = test_dir / "sample.html"
    html_file.write_text(
        """<!DOCTYPE html>
<html>
<head>
    <title>Sample HTML Document</title>
    <meta name="description" content="Test HTML file">
    <meta name="author" content="Test Author">
</head>
<body>
    <h1>Main Heading</h1>
    <p>This is a paragraph with <a href="https://example.com">a link</a>.</p>
    <img src="image.jpg" alt="Test image">
    <table>
        <tr><th>Column 1</th><th>Column 2</th></tr>
        <tr><td>Data 1</td><td>Data 2</td></tr>
    </table>
</body>
</html>"""
    )

    # Create Markdown file
    md_file = test_dir / "sample.md"
    md_file.write_text(
        """# Sample Markdown Document

This is a **test** document with *formatting*.

## Features

- Bullet points
- Multiple lines
- Code blocks

```python
def hello():
    print("Hello, World!")
```

| Table | Column |
|-------|--------|
| Data1 | Data2  |
"""
    )

    return test_dir


async def test_txt_parser(test_dir: Path):
    """Test TXT parser"""
    print_header("Testing TXT Parser")

    txt_file = test_dir / "sample.txt"
    parser = TxtParser()

    try:
        result = await parser.parse(txt_file)

        print("✅ TXT Parse successful!")
        print_result("Parser used", result.parser_used)
        print_result("Text length", f"{result.text_length} characters")
        print_result("Word count", result.metadata.get('word_count', 'N/A'))
        print_result("Line count", result.metadata.get('line_count', 'N/A'))
        print_result("Encoding", result.metadata.get('encoding', 'N/A'))
        print_result("Parsing time", f"{result.parsing_time:.3f}s")
        print_result("First 100 chars", result.text[:100])

        return True
    except Exception as e:
        print(f"❌ TXT Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_html_parser(test_dir: Path):
    """Test HTML parser"""
    print_header("Testing HTML Parser")

    html_file = test_dir / "sample.html"
    parser = HtmlParser()

    try:
        result = await parser.parse(html_file)

        print("✅ HTML Parse successful!")
        print_result("Parser used", result.parser_used)
        print_result("Text length", f"{result.text_length} characters")
        print_result("Title", result.metadata.get('title', 'N/A'))
        print_result("Meta tags", len(result.metadata.get('meta_tags', {})))
        print_result("Links found", len(result.links) if result.links else 0)
        print_result("Images found", len(result.images) if result.images else 0)
        print_result("Tables found", len(result.tables) if result.tables else 0)
        print_result("Parsing time", f"{result.parsing_time:.3f}s")
        print_result("First 100 chars", result.text[:100])

        return True
    except Exception as e:
        print(f"❌ HTML Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_markdown_parser(test_dir: Path):
    """Test Markdown parser"""
    print_header("Testing Markdown Parser")

    md_file = test_dir / "sample.md"
    parser = MarkdownParser()

    try:
        result = await parser.parse(md_file)

        print("✅ Markdown Parse successful!")
        print_result("Parser used", result.parser_used)
        print_result("Text length", f"{result.text_length} characters")
        print_result("Title", result.metadata.get('title', 'N/A'))
        print_result("Has code blocks", result.metadata.get('has_code_blocks', False))
        print_result("Tables found", len(result.tables) if result.tables else 0)
        print_result("Parsing time", f"{result.parsing_time:.3f}s")
        print_result("First 100 chars", result.text[:100])

        return True
    except Exception as e:
        print(f"❌ Markdown Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_parser_factory(test_dir: Path):
    """Test ParserFactory automatic selection"""
    print_header("Testing Parser Factory")

    test_files = {
        "sample.txt": "TxtParser",
        "sample.html": "HtmlParser",
        "sample.md": "MarkdownParser",
    }

    results = []
    for filename, expected_parser in test_files.items():
        file_path = test_dir / filename
        try:
            parser = ParserFactory.get_parser(file_path)
            parser_name = parser.__class__.__name__

            if parser_name == expected_parser:
                print(f"  ✅ {filename:20} -> {parser_name}")
                results.append(True)
            else:
                print(f"  ❌ {filename:20} -> {parser_name} (expected {expected_parser})")
                results.append(False)

        except Exception as e:
            print(f"  ❌ {filename:20} -> Error: {e}")
            results.append(False)

    return all(results)


async def test_supported_formats():
    """Test supported formats listing"""
    print_header("Testing Supported Formats")

    formats = ParserFactory.get_supported_formats()
    print(f"  Total formats supported: {len(formats)}")
    print(f"  Formats: {', '.join(sorted(formats))}")
    print()

    # Test format support checking
    test_cases = [
        (".txt", True),
        (".pdf", True),
        (".docx", True),
        (".pptx", True),
        (".html", True),
        (".md", True),
        (".json", False),
        (".csv", False),
    ]

    for ext, expected in test_cases:
        test_file = Path(f"test{ext}")
        is_supported = ParserFactory.is_supported(test_file)

        if is_supported == expected:
            status = "✅"
        else:
            status = "❌"

        print(f"  {status} {ext:10} -> {is_supported} (expected {expected})")

    return True


async def test_error_handling(test_dir: Path):
    """Test error handling for invalid files"""
    print_header("Testing Error Handling")

    # Test non-existent file
    try:
        parser = TxtParser()
        await parser.parse(test_dir / "nonexistent.txt")
        print("  ❌ Should have raised error for non-existent file")
        return False
    except FileNotFoundError:
        print("  ✅ Correctly raised FileNotFoundError for non-existent file")
    except Exception as e:
        print(f"  ⚠️  Raised unexpected error: {type(e).__name__}: {e}")

    # Test unsupported format
    try:
        unsupported = test_dir / "test.xyz"
        unsupported.write_text("test")
        ParserFactory.get_parser(unsupported)
        print("  ❌ Should have raised error for unsupported format")
        return False
    except Exception as e:
        print(f"  ✅ Correctly raised {type(e).__name__} for unsupported format")

    return True


async def main():
    """Main test runner"""
    print_header("Document Parser Test Suite")
    print("Testing Phase 3 document parsers...")
    print()

    # Create test files
    print("Creating test files...")
    test_dir = await create_test_files()
    print(f"✅ Test files created in: {test_dir}\n")

    # Run tests
    tests = [
        ("Supported Formats", test_supported_formats()),
        ("Parser Factory", test_parser_factory(test_dir)),
        ("TXT Parser", test_txt_parser(test_dir)),
        ("HTML Parser", test_html_parser(test_dir)),
        ("Markdown Parser", test_markdown_parser(test_dir)),
        ("Error Handling", test_error_handling(test_dir)),
    ]

    results = []
    for name, test_coro in tests:
        try:
            result = await test_coro
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status:10} {name}")

    print(f"\n  Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
