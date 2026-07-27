"""
Hermes Translate
================
Fully offline desktop translation tool.
Supports EN ↔ FR, EN ↔ DE, EN ↔ TR, FR ↔ DE.
Translates plain text, PDF, DOCX, and TXT files.

Install dependencies:
    pip install argostranslate pymupdf python-docx

Run:
    python hermes.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path


# ── language pairs ─────────────────────────────────────────────────────────────

LANGUAGE_PAIRS = [
    ("English",  "en", "French",  "fr"),
    ("French",   "fr", "English", "en"),
    ("English",  "en", "German",  "de"),
    ("German",   "de", "English", "en"),
    ("English",  "en", "Turkish", "tr"),
    ("Turkish",  "tr", "English", "en"),
    ("French",   "fr", "German",  "de"),
    ("German",   "de", "French",  "fr"),
]

PAIR_LABELS = [f"{src} → {tgt}" for src, _, tgt, __ in LANGUAGE_PAIRS]


# ── package guard ──────────────────────────────────────────────────────────────

def _require(module, pip_name=None):
    import importlib
    try:
        return importlib.import_module(module)
    except ImportError:
        name = pip_name or module
        messagebox.showerror(
            "Missing dependency",
            f"'{name}' is not installed.\n\nRun:\n  pip install {name}\n\nThen restart Hermes."
        )
        return None


# ── translation core ───────────────────────────────────────────────────────────

def translate_text(text: str, from_code: str, to_code: str) -> str:
    at = _require("argostranslate.translate", "argostranslate")
    if at is None:
        return ""
    installed = at.get_installed_languages()
    from_lang = next((l for l in installed if l.code == from_code), None)
    to_lang   = next((l for l in installed if l.code == to_code),   None)
    if from_lang is None or to_lang is None:
        raise RuntimeError(
            f"Language pack {from_code}→{to_code} is not installed.\n"
            "Open the Packages tab and install it first."
        )
    translation = from_lang.get_translation(to_lang)
    if translation is None:
        raise RuntimeError(
            f"No model found for {from_code}→{to_code}.\n"
            "Try reinstalling from the Packages tab."
        )
    return translation.translate(text)


def translate_chunks(text: str, from_code: str, to_code: str,
                     chunk_size: int = 2000) -> str:
    """Splits large text into paragraphs to avoid memory pressure."""
    paragraphs = text.split("\n")
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) + 1 > chunk_size:
            if current:
                chunks.append(current.strip())
            current = para + "\n"
        else:
            current += para + "\n"
    if current.strip():
        chunks.append(current.strip())
    return "\n".join(translate_text(c, from_code, to_code) for c in chunks)


# ── document I/O ───────────────────────────────────────────────────────────────

def extract_pdf(path: str) -> str:
    fitz = _require("fitz", "pymupdf")
    if fitz is None:
        return ""
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages)


def extract_docx(path: str) -> str:
    docx = _require("docx", "python-docx")
    if docx is None:
        return ""
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def save_as_txt(text: str, stem: str, out_dir: str, to_code: str) -> str:
    out = Path(out_dir) / f"{stem}_translated_{to_code}.txt"
    out.write_text(text, encoding="utf-8")
    return str(out)


def save_as_docx(text: str, stem: str, out_dir: str, to_code: str) -> str:
    docx = _require("docx", "python-docx")
    if docx is None:
        return ""
    doc = docx.Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    out = Path(out_dir) / f"{stem}_translated_{to_code}.docx"
    doc.save(str(out))
    return str(out)


EXTRACTORS = {".pdf": extract_pdf, ".docx": extract_docx, ".txt": extract_txt}


# ── package management ─────────────────────────────────────────────────────────

def pkg_update_index():
    m = _require("argostranslate.package", "argostranslate")
    if m:
        m.update_package_index()
    return m


def pkg_available():
    m = pkg_update_index()
    return m.get_available_packages() if m else []


def pkg_installed():
    m = _require("argostranslate.package", "argostranslate")
    return m.get_installed_packages() if m else []


def pkg_install(available_pkg):
    m = _require("argostranslate.package", "argostranslate")
    if m:
        m.install_from_path(available_pkg.download())


# ── GUI ────────────────────────────────────────────────────────────────────────

class HermesApp(tk.Tk):

    # Design tokens — dark indigo + violet accent
    BG      = "#13131f"
    SURFACE = "#1e1e30"
    CARD    = "#252538"
    ACCENT  = "#7c6af7"
    ACCENT2 = "#a78bfa"
    TEXT    = "#e2e2f0"
    MUTED   = "#7070a0"
    SUCCESS = "#4ade80"
    ERROR   = "#f87171"
    BORDER  = "#2e2e50"

    def __init__(self):
        super().__init__()
        self.title("Hermes Translate")
        self.geometry("900x720")
        self.minsize(720, 560)
        self.configure(bg=self.BG)
        self._apply_styles()
        self._build_ui()

    # ── style sheet ──

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("TNotebook",
                    background=self.BG, borderwidth=0, tabmargins=0)
        s.configure("TNotebook.Tab",
                    background=self.SURFACE, foreground=self.MUTED,
                    padding=[18, 9], font=("Segoe UI", 10), borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", self.BG)],
              foreground=[("selected", self.ACCENT2)])

        s.configure("TFrame",  background=self.BG)
        s.configure("TLabel",  background=self.BG, foreground=self.TEXT,
                    font=("Segoe UI", 10))

        s.configure("TButton",
                    background=self.ACCENT, foreground="#ffffff",
                    font=("Segoe UI", 10, "bold"),
                    borderwidth=0, relief="flat", padding=[14, 7])
        s.map("TButton",
              background=[("active", self.ACCENT2)],
              relief=[("pressed", "flat"), ("!pressed", "flat")])

        s.configure("Ghost.TButton",
                    background=self.CARD, foreground=self.TEXT,
                    font=("Segoe UI", 10), borderwidth=0, relief="flat", padding=[14, 7])
        s.map("Ghost.TButton",
              background=[("active", self.BORDER)])

        s.configure("TCombobox",
                    fieldbackground=self.CARD, background=self.CARD,
                    foreground=self.TEXT, borderwidth=0,
                    font=("Segoe UI", 10), arrowcolor=self.ACCENT2)
        s.map("TCombobox", fieldbackground=[("readonly", self.CARD)])

        s.configure("Treeview",
                    background=self.CARD, foreground=self.TEXT,
                    fieldbackground=self.CARD, rowheight=30,
                    font=("Segoe UI", 10), borderwidth=0)
        s.configure("Treeview.Heading",
                    background=self.BORDER, foreground=self.ACCENT2,
                    font=("Segoe UI", 10, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", self.ACCENT)])

        s.configure("TProgressbar",
                    troughcolor=self.SURFACE, background=self.ACCENT,
                    borderwidth=0, thickness=3)

        s.configure("TScrollbar",
                    background=self.CARD, troughcolor=self.BG,
                    borderwidth=0, arrowsize=11)

    # ── root layout ──

    def _build_ui(self):
        self._build_header()
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self._tab_text(nb)
        self._tab_document(nb)
        self._tab_packages(nb)
        self._build_footer()

    def _build_header(self):
        bar = tk.Frame(self, bg=self.SURFACE, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="  ⬡  Hermes Translate",
                 bg=self.SURFACE, fg=self.ACCENT2,
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=4)
        self._status_var = tk.StringVar(value="Ready")
        tk.Label(bar, textvariable=self._status_var,
                 bg=self.SURFACE, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="right", padx=20)

        def _build_footer(self):
        foot = tk.Frame(self, bg=self.SURFACE, height=28)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)
        link = tk.Label(foot, text="Crafted by Azmi Allusoglu",
                        bg=self.SURFACE, fg=self.MUTED,
                        font=("Segoe UI", 8), cursor="hand2")
        link.pack(side="right", padx=16)
        link.bind("<Button-1>", lambda e: __import__("webbrowser").open(
            "https://www.linkedin.com/in/azmi-a-9065647b/"))

    # ── helper widgets ──

    def _pair_combo(self, parent) -> ttk.Combobox:
        var = tk.StringVar(value=PAIR_LABELS[0])
        cb = ttk.Combobox(parent, textvariable=var, values=PAIR_LABELS,
                          state="readonly", width=28)
        cb._var = var
        return cb

    def _pair_codes(self, combo) -> tuple:
        idx = PAIR_LABELS.index(combo._var.get())
        return LANGUAGE_PAIRS[idx][1], LANGUAGE_PAIRS[idx][3]

    def _textbox(self, parent, label: str) -> scrolledtext.ScrolledText:
        tk.Label(parent, text=label, bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 2))
        box = scrolledtext.ScrolledText(
            parent, wrap="word",
            bg=self.CARD, fg=self.TEXT,
            insertbackground=self.ACCENT2,
            selectbackground=self.ACCENT,
            relief="flat", borderwidth=10,
            font=("Segoe UI", 10), undo=True
        )
        box.pack(fill="both", expand=True)
        return box

    def _progress(self, parent) -> ttk.Progressbar:
        pb = ttk.Progressbar(parent, mode="indeterminate")
        pb.pack(fill="x", padx=20, pady=(0, 10))
        return pb

    def _set_status(self, msg: str):
        self._status_var.set(msg)

    def _show_error(self, msg: str):
        messagebox.showerror("Error", msg)
        self._set_status("Error")

    # ── TEXT TAB ──────────────────────────────────────────────────────────────

    def _tab_text(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Text  ")

        ctrl = tk.Frame(f, bg=self.BG)
        ctrl.pack(fill="x", padx=20, pady=(16, 6))
        tk.Label(ctrl, text="Language pair", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        self._text_pair = self._pair_combo(ctrl)
        self._text_pair.pack(side="left", padx=(8, 0))
        ttk.Button(ctrl, text="Translate ▶",
                   command=self._do_text_translate).pack(side="right")
        ttk.Button(ctrl, text="Clear", style="Ghost.TButton",
                   command=self._clear_text).pack(side="right", padx=8)

        pane = tk.PanedWindow(f, orient="horizontal",
                              bg=self.BORDER, sashwidth=3, sashrelief="flat")
        pane.pack(fill="both", expand=True, padx=20, pady=(0, 4))

        left = tk.Frame(pane, bg=self.BG)
        self._src_box = self._textbox(left, "Source text")
        pane.add(left, minsize=280)

        right = tk.Frame(pane, bg=self.BG)
        self._dst_box = self._textbox(right, "Translation")
        pane.add(right, minsize=280)

        self._text_pb = self._progress(f)

    def _clear_text(self):
        self._src_box.delete("1.0", "end")
        self._dst_box.delete("1.0", "end")

    def _do_text_translate(self):
        text = self._src_box.get("1.0", "end").strip()
        if not text:
            return
        fc, tc = self._pair_codes(self._text_pair)
        self._text_pb.start(12)
        self._set_status("Translating…")

        def work():
            try:
                result = translate_chunks(text, fc, tc)
                self.after(0, lambda: (
                    self._dst_box.delete("1.0", "end"),
                    self._dst_box.insert("1.0", result),
                    self._set_status("Done")
                ))
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))
            finally:
                self.after(0, self._text_pb.stop)

        threading.Thread(target=work, daemon=True).start()

    # ── DOCUMENT TAB ─────────────────────────────────────────────────────────

    def _tab_document(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Documents  ")

        # Row 1: language pair + output format
        ctrl = tk.Frame(f, bg=self.BG)
        ctrl.pack(fill="x", padx=20, pady=(16, 4))
        tk.Label(ctrl, text="Language pair", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        self._doc_pair = self._pair_combo(ctrl)
        self._doc_pair.pack(side="left", padx=(8, 0))

        tk.Label(ctrl, text="  Output format", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(20, 0))
        self._save_as = tk.StringVar(value="txt")
        for val, label in [("txt", ".txt"), ("docx", ".docx")]:
            tk.Radiobutton(
                ctrl, text=label, variable=self._save_as, value=val,
                bg=self.BG, fg=self.TEXT, selectcolor=self.CARD,
                activebackground=self.BG, activeforeground=self.ACCENT2,
                font=("Segoe UI", 10)
            ).pack(side="left", padx=4)

        # Row 2: output folder selector
        folder_row = tk.Frame(f, bg=self.BG)
        folder_row.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(folder_row, text="Output folder", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        self._out_folder_var = tk.StringVar(value="Same as source file")
        self._out_folder_entry = tk.Entry(
            folder_row, textvariable=self._out_folder_var,
            bg=self.CARD, fg=self.TEXT, insertbackground=self.ACCENT2,
            relief="flat", font=("Segoe UI", 9), width=46,
            state="readonly", readonlybackground=self.CARD
        )
        self._out_folder_entry.pack(side="left", padx=(8, 6), ipady=4)
        ttk.Button(folder_row, text="Browse…", style="Ghost.TButton",
                   command=self._pick_output_folder).pack(side="left")
        ttk.Button(folder_row, text="Reset", style="Ghost.TButton",
                   command=self._reset_output_folder).pack(side="left", padx=4)

        # Drop zone / picker
        zone = tk.Frame(f, bg=self.SURFACE)
        zone.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(zone, text="Supported: PDF · DOCX · TXT",
                 bg=self.SURFACE, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(pady=(10, 4))
        ttk.Button(zone, text="Add files…", command=self._pick_files).pack(pady=(0, 10))

        # File list
        self._doc_tree = ttk.Treeview(
            f, columns=("name", "folder", "status"), show="headings", height=8
        )
        self._doc_tree.heading("name",   text="File")
        self._doc_tree.heading("folder", text="Source folder")
        self._doc_tree.heading("status", text="Status")
        self._doc_tree.column("name",   width=220)
        self._doc_tree.column("folder", width=320)
        self._doc_tree.column("status", width=220, anchor="center")
        self._doc_tree.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        btn_row = tk.Frame(f, bg=self.BG)
        btn_row.pack(fill="x", padx=20, pady=(0, 6))
        ttk.Button(btn_row, text="Translate all ▶",
                   command=self._do_doc_translate).pack(side="left")
        ttk.Button(btn_row, text="Clear list", style="Ghost.TButton",
                   command=lambda: [self._doc_tree.delete(i)
                                    for i in self._doc_tree.get_children()]
                   ).pack(side="left", padx=8)

        self._doc_pb = self._progress(f)

    def _pick_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self._out_folder_var.set(folder)

    def _reset_output_folder(self):
        self._out_folder_var.set("Same as source file")

    def _get_out_dir(self, source_path: str) -> str:
        val = self._out_folder_var.get()
        if val == "Same as source file":
            return str(Path(source_path).parent)
        return val

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Select documents to translate",
            filetypes=[("Documents", "*.pdf *.docx *.txt"), ("All files", "*.*")]
        )
        existing = set(self._doc_tree.get_children())
        for p in paths:
            if p not in existing:
                self._doc_tree.insert("", "end", iid=p,
                                      values=(
                                          os.path.basename(p),
                                          str(Path(p).parent),
                                          "Queued"
                                      ))

    def _do_doc_translate(self):
        items = self._doc_tree.get_children()
        if not items:
            return
        fc, tc = self._pair_codes(self._doc_pair)
        save_as = self._save_as.get()
        self._doc_pb.start(12)
        self._set_status("Translating documents…")

        def work():
            for path in items:
                self.after(0, lambda p=path:
                           self._doc_tree.set(p, "status", "⏳ Working…"))
                try:
                    ext = Path(path).suffix.lower()
                    extractor = EXTRACTORS.get(ext)
                    if extractor is None:
                        raise ValueError(f"Unsupported format: {ext}")
                    raw = extractor(path)
                    translated = translate_chunks(raw, fc, tc)
                    out_dir = self._get_out_dir(path)
                    stem = Path(path).stem
                    out = (save_as_docx if save_as == "docx" else save_as_txt)(
                        translated, stem, out_dir, tc
                    )
                    msg = f"✓ → {os.path.basename(out)}"
                    self.after(0, lambda p=path, m=msg:
                               self._doc_tree.set(p, "status", m))
                except Exception as e:
                    err = f"✗ {str(e)[:55]}"
                    self.after(0, lambda p=path, m=err:
                               self._doc_tree.set(p, "status", m))
            self.after(0, self._doc_pb.stop)
            self.after(0, lambda: self._set_status("All documents done"))

        threading.Thread(target=work, daemon=True).start()

    # ── PACKAGES TAB ─────────────────────────────────────────────────────────

    def _tab_packages(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Packages  ")

        info = tk.Frame(f, bg=self.SURFACE)
        info.pack(fill="x", padx=20, pady=(16, 0))
        tk.Label(
            info,
            text=(
                "Language packs are downloaded once and stored locally (100–300 MB each).\n"
                "Refresh and reinstall every few months to get updated translation models."
            ),
            bg=self.SURFACE, fg=self.MUTED,
            font=("Segoe UI", 9), justify="left"
        ).pack(anchor="w", padx=16, pady=12)

        ctrl = tk.Frame(f, bg=self.BG)
        ctrl.pack(fill="x", padx=20, pady=10)
        ttk.Button(ctrl, text="Refresh list",
                   command=self._refresh_packages).pack(side="left")
        ttk.Button(ctrl, text="Install / Update selected", style="Ghost.TButton",
                   command=self._install_selected).pack(side="left", padx=8)

        self._pkg_tree = ttk.Treeview(
            f, columns=("pair", "version", "status"),
            show="headings", height=13
        )
        self._pkg_tree.heading("pair",    text="Language Pair")
        self._pkg_tree.heading("version", text="Version")
        self._pkg_tree.heading("status",  text="Status")
        self._pkg_tree.column("pair",    width=400)
        self._pkg_tree.column("version", width=110, anchor="center")
        self._pkg_tree.column("status",  width=140, anchor="center")
        self._pkg_tree.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        self._pkg_pb  = self._progress(f)
        self._pkg_msg = tk.Label(f, text="", bg=self.BG, fg=self.MUTED,
                                  font=("Segoe UI", 9))
        self._pkg_msg.pack(anchor="w", padx=20, pady=(0, 8))

        self._load_installed()

    def _load_installed(self):
        for i in self._pkg_tree.get_children():
            self._pkg_tree.delete(i)
        for p in pkg_installed():
            self._pkg_tree.insert("", "end", values=(
                f"{p.from_name} → {p.to_name}",
                getattr(p, "package_version", "—"),
                "✓ Installed"
            ))

    def _refresh_packages(self):
        self._pkg_pb.start(12)
        self._pkg_msg.config(text="Fetching index (requires internet)…", fg=self.MUTED)

        def work():
            try:
                available = pkg_available()
                installed_codes = {
                    (p.from_code, p.to_code) for p in pkg_installed()
                }
                our_codes = {(fc, tc) for _, fc, _, tc in LANGUAGE_PAIRS}
                filtered = [p for p in available
                            if (p.from_code, p.to_code) in our_codes]
                self._pkg_tree._pkgs = filtered
                self.after(0, lambda: self._show_packages(filtered, installed_codes))
            except Exception as e:
                self.after(0, lambda: self._pkg_msg.config(
                    text=f"Error: {e}", fg=self.ERROR))
            finally:
                self.after(0, self._pkg_pb.stop)

        threading.Thread(target=work, daemon=True).start()

    def _show_packages(self, pkgs, installed_codes):
        for i in self._pkg_tree.get_children():
            self._pkg_tree.delete(i)
        for p in pkgs:
            status = ("✓ Installed"
                      if (p.from_code, p.to_code) in installed_codes
                      else "Not installed")
            self._pkg_tree.insert("", "end", values=(
                f"{p.from_name} → {p.to_name}",
                getattr(p, "package_version", "—"),
                status
            ))
        self._pkg_msg.config(
            text=f"{len(pkgs)} packs available for your language pairs.",
            fg=self.MUTED
        )

    def _install_selected(self):
        sel = self._pkg_tree.selection()
        pkgs = getattr(self._pkg_tree, "_pkgs", [])
        if not sel:
            self._pkg_msg.config(text="Select a row first.", fg=self.ERROR)
            return
        if not pkgs:
            self._pkg_msg.config(text="Refresh the list first.", fg=self.ERROR)
            return
        to_install = [pkgs[self._pkg_tree.index(s)]
                      for s in sel
                      if self._pkg_tree.index(s) < len(pkgs)]

        self._pkg_pb.start(12)

        def work():
            for p in to_install:
                self.after(0, lambda name=f"{p.from_name}→{p.to_name}":
                           self._pkg_msg.config(
                               text=f"Downloading {name}…", fg=self.MUTED))
                try:
                    pkg_install(p)
                except Exception as e:
                    self.after(0, lambda err=str(e):
                               self._pkg_msg.config(text=f"Failed: {err}", fg=self.ERROR))
            self.after(0, self._pkg_pb.stop)
            self.after(0, lambda: self._pkg_msg.config(
                text="Installation complete.", fg=self.SUCCESS))
            self.after(0, self._load_installed)

        threading.Thread(target=work, daemon=True).start()


# ── entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = HermesApp()
    app.mainloop()
