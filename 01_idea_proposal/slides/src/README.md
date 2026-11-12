# Slide source

`build_slides.py` writes `slides_tr.html` and `slides_en.html` from the text and the data in `../../analysis`: run `python build_slides.py` for Turkish and `python build_slides.py --lang en` (or `DECK_LANG=en`) for English.
Open a file with `?s=3&b=2` to see slide 3 at its second reveal step, or with no parameters to see every slide.
`python export.py` builds both languages and prints `Fatura_Dedektifi_Group14_Slides_TR.pdf` and `Fatura_Dedektifi_Group14_Slides_EN.pdf` into the folder above with headless Chrome (set `CHROME` if it is not found), and `--frames-tr <dir>` or `--frames-en <dir>` also saves every reveal step as a PNG.
The fonts in `fonts/` are Jost and Karla under the SIL Open Font License, so the slides render offline.
