<div align="center">

# ⬡ Hermes Translate

**Fully offline desktop translation — no API keys, no cloud, no data leaving your machine.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Powered by Argos](https://img.shields.io/badge/Engine-Argos%20Translate-7c6af7)](https://github.com/argosopentech/argos-translate)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()

![Hermes Translate screenshot placeholder](https://placehold.co/860x480/13131f/a78bfa?text=Hermes+Translate)

</div>

---

## What it does

Hermes Translate is a local-first translation tool that runs entirely on your machine using [Argos Translate](https://github.com/argosopentech/argos-translate) neural models. No internet connection is needed after the initial setup, and no text is ever sent to a third party.

**Supported language pairs**

| Pair | Direction |
|---|---|
| English ↔ French | Both ways |
| English ↔ German | Both ways |
| English ↔ Turkish | Both ways |
| French ↔ German | Both ways |

**Supported document formats**

- PDF (text-based; scanned PDFs require OCR pre-processing)
- Word documents (`.docx`)
- Plain text (`.txt`)

---

## Installation

### Prerequisites

- Python 3.10 or higher — [python.org](https://python.org)
- `pip` (bundled with Python)
- ~2 GB disk space for all language models

### Windows

```bat
git clone https://github.com/YOUR_USERNAME/hermes-translate.git
cd hermes-translate
setup_windows.bat
```

The script installs Python dependencies, downloads all language packs, and creates a desktop shortcut.

### macOS / Linux

```bash
git clone https://github.com/YOUR_USERNAME/hermes-translate.git
cd hermes-translate
bash setup_unix.sh
```

### Manual install

```bash
pip install -r requirements.txt
python hermes.py
```

Then use the **Packages** tab inside the app to download language models.

---

## Usage

### Text translation

1. Open the **Text** tab
2. Select a language pair from the dropdown
3. Paste or type your source text
4. Click **Translate ▶**

### Document translation

1. Open the **Documents** tab
2. Select your language pair and output format (`.txt` or `.docx`)
3. Click **Add files…** and pick one or more PDF / DOCX / TXT files
4. Click **Translate all ▶**

Translated files are saved in the **same folder** as the originals, with `_translated_XX` appended to the filename (e.g. `report_translated_fr.docx`).

### Managing language packs

Language packs are stored locally in your OS app-data directory and persist between sessions.

| Platform | Storage path |
|---|---|
| Windows | `%APPDATA%\argos-translate\packages` |
| macOS / Linux | `~/.local/share/argos-translate/packages` |

Each pack is approximately 100–300 MB. Eight pairs total ≈ 1–2 GB.

---

## Quarterly update process

Argos Translate periodically releases improved models. To update:

1. Open Hermes Translate → **Packages** tab
2. Click **Refresh list** (requires internet for a few seconds)
3. Select the pairs you want to update
4. Click **Install / Update selected**

Alternatively, re-run the setup script — it overwrites older packs automatically.

---

## Project structure

```
hermes-translate/
├── hermes.py           # Main application
├── requirements.txt    # Python dependencies
├── setup_windows.bat   # Windows one-click setup
├── setup_unix.sh       # macOS / Linux setup
├── .gitignore
└── README.md
```

---

## Dependencies

| Package | Purpose | License |
|---|---|---|
| [argostranslate](https://github.com/argosopentech/argos-translate) | Neural translation engine | MIT |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | PDF text extraction | AGPL-3.0 / commercial |
| [python-docx](https://github.com/python-openxml/python-docx) | Word document handling | MIT |

> **Note on PyMuPDF licensing:** PyMuPDF is AGPL-3.0 for open-source use. If you intend to distribute Hermes Translate commercially, replace PyMuPDF with `pdfminer.six` (MIT) or obtain a commercial PyMuPDF licence.

---

## Known limitations

- **Scanned PDFs** (image-only) produce no extracted text. Use an OCR tool such as [Tesseract](https://github.com/tesseract-ocr/tesseract) first.
- **DOCX output** preserves paragraph structure but not rich formatting (tables, headers, styles).
- Translation quality depends on Argos Translate model versions; results are best for EN↔FR and EN↔DE.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a pull request

---

## License

MIT — see [LICENSE](LICENSE) for details.
