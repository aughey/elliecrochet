#!/usr/bin/env python3
"""Static site generator: parses Markdown content and renders into HTML template."""

import re
import shutil
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
TEMPLATE_DIR = ROOT / "templates"
BUILD_DIR = ROOT / "build"
CONTENT_FILE = CONTENT_DIR / "page.md"


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


def generate():
    """Main generation pipeline."""
    # Read content
    raw = CONTENT_FILE.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw)

    # Parse sections
    raw_sections = split_sections(body)
    sections = build_section_data(raw_sections)

    # Load template
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    template = env.get_template("base.html")

    # Render
    html = template.render(
        title=frontmatter.get("title", "My Website"),
        email=frontmatter.get("email", ""),
        discord=frontmatter.get("discord", ""),
        sections=sections,
    )

    # Write output
    BUILD_DIR.mkdir(exist_ok=True)
    (BUILD_DIR / "index.html").write_text(html, encoding="utf-8")

    # Copy images
    src_images = CONTENT_DIR / "images"
    dst_images = BUILD_DIR / "images"
    if src_images.exists():
        if dst_images.exists():
            shutil.rmtree(dst_images)
        shutil.copytree(src_images, dst_images)

    print(f"Site generated in {BUILD_DIR}/")


if __name__ == "__main__":
    generate()
