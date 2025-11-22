import os
import re
from pathlib import Path

# Folder that contains all your images, relative to the repo root
IMAGES_DIR = "images"   # change this if needed, e.g. "assets/images"

# Regex to match Obsidian image embeds: ![[...]]
OBSIDIAN_IMAGE_PATTERN = re.compile(r'!\[\[([^\]]+?)\]\]')

def convert_obsidian_image(match: re.Match) -> str:
    """
    Convert an Obsidian-style image embed:
        ![[filename.png]]
    to a GitHub-flavoured Markdown image:
        ![filename](./images/filename.png)
    """
    inner = match.group(1).strip()           # e.g. "Pasted image 20251105125239.png"
    filename = os.path.basename(inner)       # in case a path sneaks in
    alt_text, _ = os.path.splitext(filename) # use filename (without extension) as alt text

    # Build relative path to images/ directory
    markdown_path = f"./{IMAGES_DIR}/{filename}"
    return f"![{alt_text}]({markdown_path})"


def process_markdown_file(path: Path) -> bool:
    """
    Reads a .md file, replaces Obsidian image embeds if present,
    and writes back only if changes were made.
    Returns True if file was modified, False otherwise.
    """
    original_text = path.read_text(encoding="utf-8")

    new_text = OBSIDIAN_IMAGE_PATTERN.sub(convert_obsidian_image, original_text)

    if new_text != original_text:
        path.write_text(new_text, encoding="utf-8")
        print(f"[UPDATED] {path}")
        return True
    else:
        print(f"[SKIPPED] {path} (no Obsidian image embeds found)")
        return False


def walk_repo_and_fix_markdown(root: Path):
    """
    Walk through all subdirectories starting at root,
    processing every .md file.
    """
    md_files = list(root.rglob("*.md"))

    if not md_files:
        print("No .md files found. Make sure you're running this from the repo root.")
        return

    print(f"Found {len(md_files)} Markdown files. Processing...\n")

    changed_count = 0
    for md_file in md_files:
        if md_file.is_file():
            if process_markdown_file(md_file):
                changed_count += 1

    print("\nDone.")
    print(f"Total files modified: {changed_count} / {len(md_files)}")


if __name__ == "__main__":
    # Assume script is run from the repo root
    repo_root = Path(__file__).resolve().parent
    walk_repo_and_fix_markdown(repo_root)
