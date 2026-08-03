#!/usr/bin/env python3
"""Static site generator: parses Markdown content and renders into HTML template."""

import re
import shutil
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
TEMPLATE_DIR = ROOT / "templates"
BUILD_DIR = ROOT / "build"
CONTENT_FILE = CONTENT_DIR / "page.md"

# Camera originals run 2-4 MB each; downscale them for web delivery.
MAX_IMAGE_DIM = 1600
JPEG_QUALITY = 82
RASTER_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def parse_frontmatter(text):
    """Extract YAML frontmatter and remaining markdown body."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1)), match.group(2)
    return {}, text


def parse_images(md_text):
    """Extract image references from markdown text, return (cleaned_text, images)."""
    images = []
    pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+?)(?:\s+"([^"]*)")?\)')
    for m in pattern.finditer(md_text):
        images.append({"alt": m.group(1), "path": m.group(2), "caption": m.group(3) or ""})
    cleaned = pattern.sub("", md_text).strip()
    return cleaned, images


def split_sections(body):
    """Split markdown body into top-level sections by # headings."""
    sections = {}
    current_key = None
    current_lines = []

    for line in body.split("\n"):
        if line.startswith("# ") and not line.startswith("## ") and not line.startswith("### "):
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = line[2:].strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections


def parse_gallery_categories(gallery_md):
    """Parse gallery section into description + categories with images."""
    categories = []
    description = ""
    lines = gallery_md.split("\n")
    current_cat = None
    current_lines = []
    desc_lines = []

    for line in lines:
        if line.startswith("## "):
            if current_cat:
                _, images = parse_images("\n".join(current_lines))
                categories.append({"name": current_cat, "images": images})
            else:
                desc_lines = current_lines[:]
            current_cat = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_cat:
        _, images = parse_images("\n".join(current_lines))
        categories.append({"name": current_cat, "images": images})

    if desc_lines:
        description = "\n".join(desc_lines).strip()

    return description, categories


def build_section_data(raw_sections):
    """Convert raw markdown sections into structured template data."""
    sections = {}

    # Hero
    hero_md = raw_sections.get("hero", "")
    _, hero_images = parse_images(hero_md)
    sections["hero"] = {"images": hero_images}

    # About
    about_md = raw_sections.get("about", "")
    about_text, about_images = parse_images(about_md)
    sections["about"] = {
        "html": markdown.markdown(about_text),
        "images": about_images,
    }

    # Gallery
    gallery_md = raw_sections.get("gallery", "")
    description, categories = parse_gallery_categories(gallery_md)
    sections["gallery"] = {
        "html": bool(description),
        "description": description,
        "categories": categories,
    }

    # Contact
    contact_md = raw_sections.get("contact", "")
    contact_text, _ = parse_images(contact_md)
    sections["contact"] = {"html": markdown.markdown(contact_text)}

    # Closing
    closing_md = raw_sections.get("closing", "")
    closing_text, closing_images = parse_images(closing_md)
    sections["closing"] = {
        "text": closing_text,
        "images": closing_images,
    }

    return sections


def process_images():
    """Copy content images into the build, downscaling rasters for web delivery."""
    src_images = CONTENT_DIR / "images"
    dst_images = BUILD_DIR / "images"
    if not src_images.exists():
        return

    if dst_images.exists():
        shutil.rmtree(dst_images)
    dst_images.mkdir(parents=True)

    before_total = 0
    after_total = 0
    for src in sorted(src_images.iterdir()):
        if not src.is_file() or src.name == ".DS_Store":
            continue
        suffix = src.suffix.lower()
        # HEIC originals aren't web-servable; JPG conversions are referenced instead.
        if suffix == ".heic":
            continue

        dst = dst_images / src.name
        if suffix not in RASTER_SUFFIXES:
            shutil.copy2(src, dst)
            continue

        original_size = src.stat().st_size
        with Image.open(src) as img:
            # Honour EXIF rotation, otherwise phone shots come out sideways.
            img = ImageOps.exif_transpose(img)
            img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.LANCZOS)
            if suffix == ".png":
                img.save(dst, "PNG", optimize=True)
            elif suffix == ".webp":
                img.save(dst, "WEBP", quality=JPEG_QUALITY, method=6)
            else:
                img.convert("RGB").save(
                    dst, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True
                )

        # Small hand-tuned images can grow when re-encoded; keep whichever is smaller.
        if dst.stat().st_size >= original_size:
            shutil.copy2(src, dst)
        before_total += original_size
        after_total += dst.stat().st_size

    mib = 1024 * 1024
    print(
        f"  images: {before_total / mib:.1f} MiB -> {after_total / mib:.1f} MiB "
        f"(max {MAX_IMAGE_DIM}px, quality {JPEG_QUALITY})"
    )


def generate():
    """Main generation pipeline."""
    # Read content
    raw = CONTENT_FILE.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw)

    # Parse sections
    raw_sections = split_sections(body)
    sections = build_section_data(raw_sections)

    # Load templates
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    template_vars = dict(
        title=frontmatter.get("title", "My Website"),
        banner=frontmatter.get("banner"),
        sections=sections,
    )

    # Render all templates
    BUILD_DIR.mkdir(exist_ok=True)

    templates = [
        ("base.html", "index.html"),
        ("newspaper.html", "index2.html"),
    ]
    for template_name, output_name in templates:
        template = env.get_template(template_name)
        html = template.render(**template_vars)
        (BUILD_DIR / output_name).write_text(html, encoding="utf-8")
        print(f"  {template_name} -> {output_name}")

    process_images()

    print(f"Site generated in {BUILD_DIR}/")


if __name__ == "__main__":
    generate()
