"""Export a .pptx to PDF through the real PowerPoint app (macOS).

This is the step that actually matters: python-pptx writes XML, but PowerPoint
is what resolves fonts, rasterises shapes and decides image compression. Any
font or colour regression shows up here, not at build time.

Only touches the file it is given — it opens that presentation, exports it, and
closes it without saving, leaving any other open presentation alone.

Run:  .venv/bin/python presentation/export_pdf.py [path/to/deck.pptx]
"""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

APPLESCRIPT = '''
on run argv
    set pptxPath to item 1 of argv
    set pdfPath to item 2 of argv
    set pptxName to do shell script "basename " & quoted form of pptxPath
    tell application "Microsoft PowerPoint"
        activate
        -- `open` returns no value in PowerPoint's AppleScript; do not assign it,
        -- and do NOT coerce the path `as alias` (raises -2763).
        open POSIX file pptxPath
        delay 2
        set thePres to presentation pptxName
        -- `in` MUST be a POSIX file object. Handing it a plain POSIX path
        -- string makes PowerPoint silently write nothing and report success.
        save thePres in (POSIX file pdfPath) as save as PDF
        delay 2
        close thePres saving no
    end tell
    return "ok"
end run
'''


def export(pptx: Path) -> Path:
    pdf = pptx.with_suffix(".pdf")
    if pdf.exists():
        pdf.unlink()
    proc = subprocess.run(
        ["osascript", "-", str(pptx), str(pdf)],
        input=APPLESCRIPT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"PowerPoint export failed:\n{proc.stderr.strip()}")
    if not pdf.exists():
        raise SystemExit(f"PowerPoint reported success but {pdf} is missing")
    print(f"exported {pdf} ({pdf.stat().st_size/1024:.0f} KB)")
    return pdf


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "mock" / "mock-deck.pptx"
    export(target.resolve())
