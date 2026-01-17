#!/usr/bin/env python3
"""
Simple static site generator for zyzyzynn blog.
Generates HTML from markdown files in posts/ directory.
"""

import os
import re
from datetime import datetime
import markdown
from pathlib import Path

# Configuration
POSTS_DIR = Path("posts")
OUTPUT_DIR = Path("build")
SITE_NAME = "zyzyzynn"
SITE_URL = "zyzyzynn.xyz"


def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip().strip("\"'")

    return frontmatter, parts[2].strip()


def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return datetime.now()

    for fmt in ["%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return datetime.now()


def slugify(title):
    """Convert title to URL-friendly slug."""
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", title.lower())
    slug = re.sub(r"\s+", "-", slug).strip("-")
    return slug


def render_header(title="", prefix=""):
    """Render site header."""
    nav_items_left = [
        (f"{prefix}index.html", "blog"),
    ]

    nav_items_right = [
        (f"{prefix}nownownow.html", "nownownow"),
    ]

    nav_left = "\n        ".join(
        f'<a href="{item}">{text}</a>' for item, text in nav_items_left
    )

    nav_right = "\n        ".join(
        f'<a href="{item}">{text}</a>' for item, text in nav_items_right
    )

    return f"""<header>
        <nav>
            <div class="nav-left">
                {nav_left}
            </div>
            <div class="nav-center">
                i am the singularity
            </div>
            <div class="nav-right">
                {nav_right}
            </div>
        </nav>
    </header>"""


def render_footer():
    """Render site footer."""
    return f"""<footer>
        <p>&copy; {datetime.now().year} {SITE_NAME}</p>
        <div class="footer-links">
            <a href="https://github.com/bhaskar1001101" target="_blank">GitHub</a>
            <a href="https://twitter.com/zyzyzynn" target="_blank">Twitter</a>
        </div>
    </footer>"""


def render_base_html(title, content, prefix=""):
    """Render complete HTML page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {SITE_NAME}</title>
    <link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
    {render_header(title, prefix)}
    <main>
        {content}
    </main>
    {render_footer()}
</body>
</html>"""


def render_post_list(posts):
    """Render list of all posts."""
    if not posts:
        return "<p>No posts yet.</p>"

    rant_items = []
    musing_items = []

    for post in posts:
        # Skip 'now' from main list
        if post.get("is_now"):
            continue

        tag_badges = ""
        if "type" in post:
            tag_class = post["type"].lower()
            tag_badges = f'<div class="post-tags"><span class="tag {tag_class}">{post["type"]}</span></div>'

        date_str = post["date"].strftime("%B %d, %Y") if post["date"] else ""
        item = f"""<li>
            <div class="post-meta">{date_str}</div>
            <a class="post-link" href="posts/{post["slug"]}.html">{post["title"]}</a>
            {tag_badges}
        </li>"""

        if post.get("type", "").lower() == "rant":
            rant_items.append(item)
        else:
            musing_items.append(item)

    return f"""<div class="post-list-container">
        <div class="post-list-column">
            <h2 class="post-list-heading">Rants</h2>
            <ul class="post-list">
                {"".join(rant_items)}
            </ul>
        </div>
        <div class="post-list-column">
            <h2 class="post-list-heading">Musings</h2>
            <ul class="post-list">
                {"".join(musing_items)}
            </ul>
        </div>
    </div>"""


def render_post(post):
    """Render individual post page."""
    tag_badges = ""
    if "type" in post and not post.get("is_now"):
        tag_class = post["type"].lower()
        tag_badges = f'<div class="post-tags"><span class="tag {tag_class}">{post["type"]}</span></div>'

    date_str = post["date"].strftime("%B %d, %Y") if post["date"] else ""

    content = f"""<article>
        <header class="post-header">
            <h1 class="post-title">{post["title"]}</h1>
            <p class="post-date">{date_str}</p>
            {tag_badges}
        </header>
        <div class="post-content">
            {post["html_content"]}
        </div>
    </article>"""

    return render_base_html(post["title"], content, prefix="../")


def render_now_page(post):
    """Render the /now page."""
    content = f"""<article>
        <header class="post-header">
            <h1 class="post-title">{post["title"]}</h1>
            <p class="post-date">Last updated: {post["date"].strftime("%B %d, %Y")}</p>
        </header>
        <div class="post-content">
            {post["html_content"]}
        </div>
    </article>"""

    return render_base_html(post["title"], content)


def load_posts():
    """Load all markdown files from posts directory."""
    posts = []

    if not POSTS_DIR.exists():
        print(f"Warning: {POSTS_DIR} directory not found.")
        return posts

    for md_file in POSTS_DIR.glob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter, body = parse_frontmatter(content)

        title = frontmatter.get("title", md_file.stem.replace("-", " "))
        date = parse_date(frontmatter.get("date"))
        post_type = frontmatter.get("type", "")
        is_now = md_file.stem == "now"

        post = {
            "title": title,
            "date": date,
            "type": post_type,
            "slug": slugify(title) if not is_now else "nownownow",
            "html_content": markdown.markdown(body),
            "source_file": md_file,
            "is_now": is_now,
        }

        posts.append(post)

    return posts


def build():
    """Build the entire site."""
    print(f"Building {SITE_NAME} blog...")

    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "posts").mkdir(exist_ok=True)

    # Load all posts
    posts = load_posts()

    if not posts:
        print("Warning: No posts found.")
        return

    # Sort by date (newest first)
    posts.sort(key=lambda x: x["date"], reverse=True)

    # Generate index.html
    index_content = render_post_list(posts)
    index_html = render_base_html(SITE_NAME, index_content)

    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"Generated index.html")

    # Generate individual post pages
    for post in posts:
        if post["is_now"]:
            # Generate nownownow.html in root
            now_html = render_now_page(post)
            with open(OUTPUT_DIR / "nownownow.html", "w", encoding="utf-8") as f:
                f.write(now_html)
            print(f"Generated nownownow.html")
        else:
            # Generate post page
            post_html = render_post(post)
            with open(
                OUTPUT_DIR / "posts" / f"{post['slug']}.html", "w", encoding="utf-8"
            ) as f:
                f.write(post_html)

    # Copy style.css to output
    if (Path("style.css")).exists():
        import shutil

        shutil.copy("style.css", OUTPUT_DIR / "style.css")
        print(f"Copied style.css")

    print(f"\nBuild complete! {len(posts)} pages generated in {OUTPUT_DIR}/")


if __name__ == "__main__":
    build()
