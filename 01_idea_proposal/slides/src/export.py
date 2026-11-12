#!/usr/bin/env python3
"""Build both decks and print them to PDF with headless Chrome.

    python export.py
    python export.py --frames-tr <dir> --frames-en <dir>

The PDFs go next to this folder, one page per slide with every element shown.
With --frames-tr or --frames-en it also saves every reveal step of every slide
as <slide>_<beat>.png at 1920x1080.
"""

import argparse
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import build_slides

HERE = Path(__file__).resolve().parent
PDF_NAME = {"tr": "Fatura_Dedektifi_Group14_Slides_TR.pdf", "en": "Fatura_Dedektifi_Group14_Slides_EN.pdf"}
BEATS = [4, 4, 4, 4, 3, 5, 6, 7, 5, 5, 5]
MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    if Path(MAC_CHROME).exists():
        return MAC_CHROME
    sys.exit("Chrome not found. Set CHROME to the browser executable.")


def run(args):
    subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--window-size=1920,1080",
                    "--virtual-time-budget=4000", *args],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build(lang):
    html = HERE / f"slides_{lang}.html"
    html.write_text(build_slides.build(lang), encoding="utf-8")
    return html


def pdf(lang, html):
    out = HERE.parent / PDF_NAME[lang]
    run(["--no-pdf-header-footer", f"--print-to-pdf={out}", f"{html.as_uri()}?b=99"])
    return out


def frames(html, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    jobs = [(s, b) for s, n in enumerate(BEATS, 1) for b in range(1, n + 1)]

    def shot(job):
        s, b = job
        run([f"--screenshot={folder / f'{s}_{b}.png'}", f"{html.as_uri()}?s={s}&b={b}"])

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(shot, jobs))
    return len(jobs)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--frames-tr", help="folder for the Turkish frames")
    ap.add_argument("--frames-en", help="folder for the English frames")
    ap.add_argument("--no-pdf", action="store_true", help="skip the PDFs")
    args = ap.parse_args()
    for lang in ("tr", "en"):
        html = build(lang)
        if not args.no_pdf:
            print(pdf(lang, html))
        folder = args.frames_tr if lang == "tr" else args.frames_en
        if folder:
            print(f"{frames(html, folder)} frames in {folder}")


if __name__ == "__main__":
    main()
