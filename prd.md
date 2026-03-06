# PRD: Markdown-Driven Static Website Generator with S3 Deployment

## 1. Overview

This project implements a **lightweight static website generation pipeline** that allows non-technical users to update a website by editing Markdown files and adding images in a GitHub repository.

A CI build process will automatically:

1. Parse Markdown content
2. Inject it into HTML templates
3. Generate a static site
4. Upload the site to an S3 static website bucket

The resulting site will consist primarily of **a single HTML page with associated images and assets**, deployed as static content.

No backend runtime or CMS is required.

---

# 2. Goals

### Primary Goals

- Enable **non-technical users** to update site content via Markdown.
- Maintain **a fixed HTML design template**.
- Automatically generate static HTML from Markdown.
- Automatically deploy to **AWS S3 static website hosting**.
- Keep the system **simple, deterministic, and CI-driven**.

### Secondary Goals

- Allow creation of:
  - new content sections
  - image galleries
  - captions and image titles

- Allow incremental content updates without redesigning templates.

---

# 3. Non-Goals

This system will **not** include:

- a full CMS
- a database
- runtime server rendering
- WYSIWYG editors
- dynamic content

Everything must compile to **static HTML + assets**.

---

# 4. High-Level Architecture

```
GitHub Repository
│
├── content/
│   ├── page.md
│   └── images/
│       ├── gallery1/
│       └── gallery2/
│
├── templates/
│   └── base.html
│
├── build/
│
├── scripts/
│   ├── generate_site.py
│   └── deploy_s3.sh
│
└── .github/workflows/deploy.yml
```

Pipeline:

```
Commit
   │
GitHub Actions
   │
Run static generator
   │
Generate HTML + assets
   │
Upload to S3
   │
Website live
```

Static site generators combine **Markdown content with templates to produce HTML output** that can be hosted directly on a CDN or static host such as S3. ([Full Stack Python][1])

---

# 5. Recommended Technology Stack

## Language

**Python**

Reason:

- minimal boilerplate
- strong Markdown ecosystem
- easy scripting for CI

---

## Required Libraries

### Markdown parsing

```
markdown
```

or

```
markdown-it-py
```

---

### Templating Engine

Recommended:

### **Jinja2**

Reasons:

- industry standard
- powerful loops/conditionals
- widely used for static site generation
- integrates easily with Python scripts

Jinja2 is widely used to generate HTML by injecting structured data into templates at runtime. ([Medium][2])

Alternative templating engines (acceptable):

| Engine     | Notes                                   |
| ---------- | --------------------------------------- |
| Mustache   | very simple                             |
| Handlebars | JS equivalent                           |
| Tera       | Rust (not recommended for this project) |

---

### Image Metadata

Use:

```
pyyaml
```

or YAML frontmatter inside Markdown.

---

### File System Utilities

Standard Python libraries:

```
pathlib
shutil
os
```

---

### Deployment

AWS CLI

```
aws s3 sync
```

---

# 6. Repository Layout

## Content Directory

```
content/
   page.md
   images/
      gallery1/
         image1.jpg
         image2.jpg
      gallery2/
```

---

## Template Directory

```
templates/
   base.html
```

This file contains the full HTML layout.

Example placeholders:

```
{{ page_title }}

{{ introduction }}

{{ gallery_1 }}

{{ gallery_2 }}

{{ footer }}
```

---

# 7. Markdown Content Format

The Markdown document acts as the **content source**.

Example:

```
---
title: My Website
---

# Introduction

Welcome to our site.

# Gallery: Cars

![Red Car](images/gallery1/car1.jpg)
![Blue Car](images/gallery1/car2.jpg)

# About

This is the about section.
```

---

# 8. Section Parsing

The generator must parse Markdown sections.

Example mapping:

```
# Introduction → introduction
# Gallery: Cars → gallery_cars
# About → about
```

Parsed into:

```
{
  "introduction": "...html...",
  "gallery_cars": "...html...",
  "about": "...html..."
}
```

---

# 9. Image Gallery Support

Images must support:

- caption
- title
- alt text

Example Markdown:

```
![Title text](images/gallery1/photo1.jpg "Caption text")
```

Template example:

```
<div class="gallery">
{% for image in gallery_cars %}
   <figure>
      <img src="{{ image.path }}" alt="{{ image.alt }}">
      <figcaption>{{ image.caption }}</figcaption>
   </figure>
{% endfor %}
</div>
```

---

# 10. Static Site Generator Script

File:

```
scripts/generate_site.py
```

Responsibilities:

### 1. Load Markdown

```
content/page.md
```

---

### 2. Parse Sections

Split Markdown by headings.

---

### 3. Convert Markdown → HTML

Use:

```
markdown.markdown()
```

---

### 4. Load Template

```
templates/base.html
```

---

### 5. Inject Content

Using Jinja:

```
template.render(sections)
```

---

### 6. Write Output

```
build/index.html
```

---

### 7. Copy Static Assets

Copy:

```
content/images
```

to

```
build/images
```

---

# 11. S3 Deployment

Script:

```
scripts/deploy_s3.sh
```

Command:

```
aws s3 sync build/ s3://my-website-bucket --delete
```

Bucket must be configured for **static website hosting**.

---

# 12. CI Pipeline

GitHub Action:

```
.github/workflows/deploy.yml
```

Trigger:

```
on:
  push:
    branches:
      - main
```

Pipeline:

```
Checkout repo
Install Python
Install dependencies
Run site generator
Upload to S3
```

Example:

```
pip install markdown jinja2 pyyaml

python scripts/generate_site.py

aws s3 sync build/ s3://bucket-name
```

---

# 13. Secrets

Stored in GitHub:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
S3_BUCKET_NAME
```

---

# 14. User Workflow

Non-technical user workflow:

1. Open GitHub repository
2. Edit Markdown file
3. Add images
4. Commit changes
5. CI deploys automatically

No manual steps required.

---

# 15. Extensibility

Possible future additions:

- additional templates
- multiple pages
- automatic image resizing
- image compression
- sitemap generation
- RSS generation

---

# 16. Simplicity Requirements

The generator must:

- be under **~300 lines of code**
- have **no runtime server**
- produce deterministic builds
- use **existing libraries only**

---

# 17. Deliverables

The coding agent must produce:

### Code

```
scripts/generate_site.py
scripts/deploy_s3.sh
```

### Templates

```
templates/base.html
```

### Example Content

```
content/page.md
content/images/*
```

### CI

```
.github/workflows/deploy.yml
```

### Documentation

```
README.md
```

---

# 18. Success Criteria

The system is successful when:

1. A Markdown edit results in a new deployed site after commit.
2. Images appear correctly in galleries.
3. Users never edit HTML directly.
4. The site deploys automatically to S3.

---

# 19. Estimated Complexity

Implementation effort:

**Low**

Estimated:

```
1–2 days
```

---

# 20. Recommended Libraries Summary

| Component  | Library                   |
| ---------- | ------------------------- |
| Markdown   | markdown / markdown-it-py |
| Templating | Jinja2                    |
| YAML       | pyyaml                    |
| Deployment | AWS CLI                   |
