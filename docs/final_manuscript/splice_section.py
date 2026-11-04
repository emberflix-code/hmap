"""Replaces a block of build_chapters_final.py with the contents of a snippet file.

Usage: python splice_section.py <snippet> <start_marker> <end_marker>
The block runs from the line containing start_marker up to (not including) the
line containing end_marker.
"""
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("build_chapters_final.py")
snippet_path, start_marker, end_marker = sys.argv[1:4]

lines = SCRIPT.read_text(encoding="utf-8").splitlines(keepends=True)

def locate(marker, after):
    # "@123" means 1-based line 123; anything else is a substring to search for
    if marker.startswith("@") and marker[1:].isdigit():
        return int(marker[1:]) - 1
    return next(i for i in range(after, len(lines)) if marker in lines[i])


start = locate(start_marker, 0)
end = locate(end_marker, start + 1)
snippet = Path(snippet_path).read_text(encoding="utf-8")
if not snippet.endswith("\n"):
    snippet += "\n"
SCRIPT.write_text("".join(lines[:start]) + snippet + "\n" + "".join(lines[end:]),
                  encoding="utf-8")
print(f"replaced lines {start + 1}-{end} ({end - start} lines) with {snippet_path}")
