import os
import re
from pathlib import Path

# This pattern matches: ![anything](./images/filename.ext)
MARKDOWN_IMAGE_PATTERN = re.compile(
    r'!\[[^\]]*?\]\(\s*\.\/images\/([^)\s]+)\s*\)'
)

def convert_markdown_to_obsidian(match: re.Match) -> str:
    filename = match.group(1).strip()
    # Strip any path in case it sneaks in
    filename = os.path.basename(filename)
    return f"![[{filename}]]"

def process_markdown_file(path: Path) -> bool:
    original_text = path.read_text(encoding="utf-8")
    new_text = MARKDOWN_IMAGE_PATTERN.sub(convert_markdown_to_obsidian, original_text)
    if new_text != original_text:
        path.write_text(new_text, encoding="utf-8")
        print(f"[RESTORED] {path}")
        return True
    else:
        print(f"[SKIPPED] {path}")
        return False

def main():
    root = Path(__file__).resolve().parent
    for md_file in root.rglob("*.md"):
        if md_file.is_file():
            process_markdown_file(md_file)

if __name__ == "__main__":
    main()
