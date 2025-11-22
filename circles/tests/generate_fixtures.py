"""Generate test fixture files for adapter tests."""

from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_fixtures():
    """Generate all test fixture files."""
    # Get fixtures directory
    fixtures_dir = Path(__file__).parent / "fixtures"
    images_dir = fixtures_dir / "images"
    documents_dir = fixtures_dir / "documents"

    # Ensure directories exist
    images_dir.mkdir(parents=True, exist_ok=True)
    documents_dir.mkdir(parents=True, exist_ok=True)

    print("Generating test fixtures...")

    # Generate sample JPEG image (100x100 red)
    print("Creating sample.jpg...")
    img_jpg = Image.new("RGB", (100, 100), color="red")
    img_jpg.save(images_dir / "sample.jpg", "JPEG")

    # Generate sample PNG image (100x100 blue)
    print("Creating sample.png...")
    img_png = Image.new("RGB", (100, 100), color="blue")
    img_png.save(images_dir / "sample.png", "PNG")

    # Generate invalid file (text file pretending to be image)
    print("Creating invalid.txt...")
    with open(images_dir / "invalid.txt", "w") as f:
        f.write("This is not an image file")

    # Generate sample PDF
    print("Creating sample.pdf...")
    pdf_path = documents_dir / "sample.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "Sample PDF Document")
    c.drawString(100, 730, "This is a test document for adapter testing.")
    c.drawString(100, 710, "It contains some sample text to be converted to markdown.")
    c.save()

    # Generate sample HTML
    print("Creating sample.html...")
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Sample HTML Document</title>
</head>
<body>
    <h1>Sample HTML Document</h1>
    <p>This is a test HTML file for adapter testing.</p>
    <p>It contains some sample content to be converted to markdown.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
</body>
</html>"""
    with open(documents_dir / "sample.html", "w") as f:
        f.write(html_content)

    print(f"✅ Test fixtures generated in {fixtures_dir}")
    print(f"   - Images: {list(images_dir.glob('*'))}")
    print(f"   - Documents: {list(documents_dir.glob('*'))}")


if __name__ == "__main__":
    generate_fixtures()
