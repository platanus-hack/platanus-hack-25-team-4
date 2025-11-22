#!/usr/bin/env python3
"""
PDF Processing Script - Extract and process CV from mock_data.

This script processes PDF files from mock_data directory using available
PDF libraries (markitdown, PyPDF2, or pdfminer).
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Try importing various PDF libraries in order of preference
try:
    import markitdown

    PDF_LIBRARY = "markitdown"
except ImportError:
    markitdown = None
    PDF_LIBRARY = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from pdfminer.high_level import extract_text
except ImportError:
    extract_text = None


async def extract_pdf_content(file_path: Path) -> str:
    """
    Extract text content from PDF file using available library.

    Tries multiple extraction methods in order:
    1. markitdown (best for structured content)
    2. PyPDF2
    3. pdfminer
    4. pdftotext command-line tool
    5. String extraction from binary

    Args:
        file_path: Path to PDF file

    Returns:
        Extracted text content

    Raises:
        ValueError: If extraction fails with all methods
    """
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected PDF file, got: {file_path.suffix}")

    # Method 1: Try markitdown
    if markitdown is not None:
        try:
            converter = markitdown.MarkItDown()
            result = converter.convert(str(file_path))
            return result.text_content
        except Exception as e:
            print(f"  Warning: markitdown failed: {e}")

    # Method 2: Try PyPDF2
    if PdfReader is not None:
        try:
            pdf = PdfReader(str(file_path))
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            if text.strip():
                return text
        except Exception as e:
            print(f"  Warning: PyPDF2 failed: {e}")

    # Method 3: Try pdfminer
    if extract_text is not None:
        try:
            text = extract_text(str(file_path))
            if text.strip():
                return text
        except Exception as e:
            print(f"  Warning: pdfminer failed: {e}")

    # Method 4: Try pdftotext command-line tool
    try:
        result = subprocess.run(
            ["pdftotext", str(file_path), "-"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except Exception as e:
        print(f"  Warning: pdftotext failed: {e}")

    # Method 5: Binary string extraction (fallback)
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            # Extract ASCII text from PDF binary
            text = "".join(chr(c) for c in content if 32 <= c < 127 or c in (9, 10, 13))
            if text.strip():
                return text
    except Exception as e:
        print(f"  Warning: binary extraction failed: {e}")

    raise ValueError(
        f"Could not extract text from PDF. "
        f"Install markitdown, PyPDF2, or pdfminer: "
        f"pip install 'markitdown[all]' or pip install PyPDF2 or pip install pdfminer.six"
    )


def parse_cv_structure(content: str) -> Dict[str, Any]:
    """
    Parse CV content into structured sections.

    Looks for common CV sections and organizes content.

    Args:
        content: Full text content from CV

    Returns:
        Dictionary with parsed sections
    """
    sections = {
        "full_text": content,
        "extracted_sections": {},
    }

    # Common CV section headers (case-insensitive)
    section_keywords = {
        "experience": [
            "work experience",
            "professional experience",
            "employment",
            "career",
        ],
        "education": ["education", "academic", "degree"],
        "skills": ["skills", "technical skills", "competencies"],
        "contact": ["contact", "contact information", "email", "phone"],
        "summary": ["summary", "objective", "profile", "about"],
        "projects": ["projects", "portfolio", "accomplishments"],
        "languages": ["languages", "language proficiency"],
        "certifications": ["certifications", "licenses", "awards"],
    }

    content_lower = content.lower()
    lines = content.split("\n")

    # Simple section detection
    for line in lines:
        line_lower = line.lower().strip()
        for section_name, keywords in section_keywords.items():
            if any(keyword in line_lower for keyword in keywords):
                if section_name not in sections["extracted_sections"]:
                    sections["extracted_sections"][section_name] = []

    return sections


def format_output(result: Dict[str, Any]) -> str:
    """
    Format processing result for display.

    Args:
        result: Processing result dictionary

    Returns:
        Formatted output string
    """
    output = []
    output.append("=" * 80)
    output.append("PDF PROCESSING RESULT")
    output.append("=" * 80)

    if "error" in result:
        output.append(f"ERROR: {result['error']}")
    else:
        output.append(f"File: {result['file']}")
        output.append(f"File Size: {result['file_size']} bytes")
        output.append(f"Extraction Method: {result['method']}")
        output.append("\n" + "-" * 80)
        output.append("EXTRACTED CONTENT (First 2000 chars):")
        output.append("-" * 80)
        content = result["content"][:2000]
        output.append(content)
        if len(result["content"]) > 2000:
            output.append(
                f"\n... [Content truncated. Total length: {len(result['content'])} chars]"
            )

        output.append("\n" + "-" * 80)
        output.append("DETECTED SECTIONS:")
        output.append("-" * 80)
        if result["sections"]["extracted_sections"]:
            for section in result["sections"]["extracted_sections"].keys():
                output.append(f"  ✓ {section.title()}")
        else:
            output.append("  (No standard sections detected)")

    output.append("=" * 80)
    return "\n".join(output)


async def process_pdf(file_path: Path) -> Dict[str, Any]:
    """
    Process PDF file and extract content.

    Args:
        file_path: Path to PDF file

    Returns:
        Dictionary with processing result
    """
    try:
        # Extract content
        content = await extract_pdf_content(file_path)

        # Parse structure
        sections = parse_cv_structure(content)

        return {
            "file": str(file_path),
            "file_size": file_path.stat().st_size,
            "method": "markitdown",
            "content": content,
            "sections": sections,
        }

    except Exception as e:
        return {
            "error": str(e),
            "file": str(file_path),
        }


async def main():
    """Main entry point."""
    # Determine PDF file path
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        # Default to mock_data if available
        default_path = (
            Path(__file__).parent
            / "mock_data"
            / "user_1"
            / "CV-SMontagna-MLEngineer-ES-2025.pdf"
        )
        pdf_path = default_path if default_path.exists() else None

    if not pdf_path:
        print("Usage: python process_pdf.py <path_to_pdf>")
        print(
            "\nExample: python process_pdf.py mock_data/user_1/CV-SMontagna-MLEngineer-ES-2025.pdf"
        )
        sys.exit(1)

    # Process PDF
    print(f"Processing: {pdf_path}")
    result = await process_pdf(pdf_path)

    # Display result
    print(format_output(result))

    # Also save as JSON for programmatic access
    json_output = pdf_path.parent / f"{pdf_path.stem}_output.json"
    with open(json_output, "w") as f:
        # Convert Path to string for JSON serialization
        clean_result = {
            k: str(v) if isinstance(v, Path) else v for k, v in result.items()
        }
        json.dump(clean_result, f, indent=2)
    print(f"\nJSON output saved to: {json_output}")


if __name__ == "__main__":
    asyncio.run(main())
