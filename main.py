"""
Website Citation Generator
Generates citations in APA, MLA, Chicago, Harvard, and IEEE formats from a URL.
Requires: requests, beautifulsoup4
Install: pip install requests beautifulsoup4
Build exe: pyinstaller --onefile --windowed cite_generator.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import datetime
import re
import urllib.parse

try:
    import requests
    from bs4 import BeautifulSoup
    LIBS_OK = True
except ImportError:
    LIBS_OK = False


# ─────────────────────────────────────────────
#  Metadata scraper
# ─────────────────────────────────────────────

def scrape_metadata(url: str) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=12)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    def meta(name=None, prop=None):
        if prop:
            tag = soup.find("meta", property=prop)
            if tag and tag.get("content"):
                return tag["content"].strip()
        if name:
            tag = soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                return tag["content"].strip()
        return ""

    # Title
    title = (
        meta(prop="og:title")
        or meta(name="twitter:title")
        or (soup.title.string.strip() if soup.title else "")
        or "Untitled"
    )

    # Authors – try multiple signals
    authors = []
    for sel in [
        ("meta", {"name": "author"}),
        ("meta", {"property": "article:author"}),
        ("meta", {"name": "article:author"}),
        ("a", {"rel": "author"}),
    ]:
        tag = soup.find(sel[0], sel[1])
        if tag:
            val = tag.get("content") or tag.get_text(strip=True)
            if val and val not in authors:
                authors.append(val)
    # JSON-LD
    import json
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            for field in ("author", "creator"):
                entry = data.get(field)
                if isinstance(entry, dict):
                    n = entry.get("name", "")
                    if n and n not in authors:
                        authors.append(n)
                elif isinstance(entry, list):
                    for e in entry:
                        n = (e.get("name", "") if isinstance(e, dict) else str(e))
                        if n and n not in authors:
                            authors.append(n)
        except Exception:
            pass

    # Published date
    pub_date = (
        meta(prop="article:published_time")
        or meta(name="pubdate")
        or meta(name="date")
        or meta(name="DC.date")
        or ""
    )
    if pub_date:
        # Trim to YYYY-MM-DD if ISO format
        pub_date = pub_date[:10]

    # Site / publisher name
    site_name = (
        meta(prop="og:site_name")
        or meta(name="publisher")
        or urllib.parse.urlparse(url).netloc.replace("www.", "")
    )

    # Description
    description = (
        meta(prop="og:description")
        or meta(name="description")
        or meta(name="twitter:description")
        or ""
    )

    return {
        "url": url,
        "title": title,
        "authors": authors,
        "pub_date": pub_date,
        "site_name": site_name,
        "description": description,
        "access_date": datetime.date.today().isoformat(),
    }


# ─────────────────────────────────────────────
#  Citation formatters
# ─────────────────────────────────────────────

def _format_author_apa(name: str) -> str:
    """Smith, J. or just the name if unparseable."""
    parts = name.strip().split()
    if len(parts) >= 2:
        last = parts[-1]
        initials = " ".join(p[0].upper() + "." for p in parts[:-1])
        return f"{last}, {initials}"
    return name

def _format_author_mla(name: str) -> str:
    """Last, First for first author."""
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    return name

def _format_year(date_str: str) -> str:
    return date_str[:4] if date_str else "n.d."

def _format_date_mla(date_str: str) -> str:
    """DD Mon. YYYY"""
    if not date_str:
        return ""
    try:
        d = datetime.date.fromisoformat(date_str)
        months = ["Jan.","Feb.","Mar.","Apr.","May","June",
                  "July","Aug.","Sept.","Oct.","Nov.","Dec."]
        return f"{d.day} {months[d.month-1]} {d.year}"
    except Exception:
        return date_str

def _access_date_mla(date_str: str) -> str:
    try:
        d = datetime.date.fromisoformat(date_str)
        months = ["Jan.","Feb.","Mar.","Apr.","May","June",
                  "July","Aug.","Sept.","Oct.","Nov.","Dec."]
        return f"{d.day} {months[d.month-1]} {d.year}"
    except Exception:
        return date_str

def _access_date_chicago(date_str: str) -> str:
    try:
        d = datetime.date.fromisoformat(date_str)
        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        return f"{months[d.month-1]} {d.day}, {d.year}"
    except Exception:
        return date_str


def cite_apa(m: dict) -> str:
    authors = m["authors"]
    year = _format_year(m["pub_date"])
    title = m["title"]
    site = m["site_name"]
    url = m["url"]
    access = m["access_date"]

    if authors:
        if len(authors) == 1:
            auth_str = _format_author_apa(authors[0])
        elif len(authors) <= 20:
            fmt = [_format_author_apa(a) for a in authors]
            auth_str = ", ".join(fmt[:-1]) + ", & " + fmt[-1]
        else:
            fmt = [_format_author_apa(a) for a in authors[:19]]
            auth_str = ", ".join(fmt) + ", ... " + _format_author_apa(authors[-1])
        return (
            f"{auth_str} ({year}). {title}. {site}. "
            f"Retrieved {access}, from {url}"
        )
    else:
        return (
            f"{title}. ({year}). {site}. "
            f"Retrieved {access}, from {url}"
        )


def cite_mla(m: dict) -> str:
    authors = m["authors"]
    title = m["title"]
    site = m["site_name"]
    pub = _format_date_mla(m["pub_date"])
    access = _access_date_mla(m["access_date"])
    url = m["url"]

    if authors:
        if len(authors) == 1:
            auth_str = _format_author_mla(authors[0]) + "."
        elif len(authors) == 2:
            auth_str = (
                _format_author_mla(authors[0]) + ", and "
                + authors[1] + "."
            )
        else:
            auth_str = _format_author_mla(authors[0]) + ", et al."
    else:
        auth_str = ""

    parts = []
    if auth_str:
        parts.append(auth_str)
    parts.append(f'"{title}."')
    parts.append(f"*{site}*,")
    if pub:
        parts.append(pub + ",")
    parts.append(url + ".")
    parts.append(f"Accessed {access}.")
    return " ".join(parts)


def cite_chicago(m: dict) -> str:
    authors = m["authors"]
    title = m["title"]
    site = m["site_name"]
    pub = _access_date_chicago(m["pub_date"]) if m["pub_date"] else ""
    access = _access_date_chicago(m["access_date"])
    url = m["url"]

    if authors:
        if len(authors) == 1:
            auth_str = _format_author_mla(authors[0]) + "."
        elif len(authors) <= 3:
            parts_a = [_format_author_mla(authors[0])]
            parts_a += authors[1:]
            auth_str = ", ".join(parts_a) + "."
        else:
            auth_str = _format_author_mla(authors[0]) + " et al."
    else:
        auth_str = ""

    parts = []
    if auth_str:
        parts.append(auth_str)
    parts.append(f'"{title}."')
    parts.append(f"{site}.")
    if pub:
        parts.append(f"Published {pub}.")
    parts.append(f"Accessed {access}.")
    parts.append(url + ".")
    return " ".join(parts)


def cite_harvard(m: dict) -> str:
    authors = m["authors"]
    year = _format_year(m["pub_date"])
    title = m["title"]
    site = m["site_name"]
    access = m["access_date"]
    url = m["url"]

    if authors:
        fmt = [_format_author_apa(a) for a in authors]
        if len(fmt) == 1:
            auth_str = fmt[0]
        elif len(fmt) == 2:
            auth_str = " and ".join(fmt)
        else:
            auth_str = ", ".join(fmt[:-1]) + " and " + fmt[-1]
        return (
            f"{auth_str} ({year}) '{title}', *{site}*. "
            f"Available at: {url} (Accessed: {access})."
        )
    else:
        return (
            f"{site} ({year}) '{title}'. "
            f"Available at: {url} (Accessed: {access})."
        )


def cite_ieee(m: dict) -> str:
    authors = m["authors"]
    title = m["title"]
    site = m["site_name"]
    year = _format_year(m["pub_date"])
    access = m["access_date"]
    url = m["url"]

    def ieee_name(name):
        parts = name.strip().split()
        if len(parts) >= 2:
            initials = " ".join(p[0].upper() + "." for p in parts[:-1])
            return f"{initials} {parts[-1]}"
        return name

    if authors:
        if len(authors) <= 3:
            auth_str = ", ".join(ieee_name(a) for a in authors)
        else:
            auth_str = ieee_name(authors[0]) + " et al."
        return (
            f"{auth_str}, \"{title},\" *{site}*. "
            f"[Online]. Available: {url}. [Accessed: {access}]."
        )
    else:
        return (
            f"\"{title},\" *{site}*, {year}. "
            f"[Online]. Available: {url}. [Accessed: {access}]."
        )


STYLES = {
    "APA 7th": cite_apa,
    "MLA 9th": cite_mla,
    "Chicago 17th": cite_chicago,
    "Harvard": cite_harvard,
    "IEEE": cite_ieee,
}


# ─────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────

DARK_BG   = "#0f0f13"
CARD_BG   = "#1a1a24"
ACCENT    = "#7c6af7"
ACCENT2   = "#a78bfa"
TEXT_PRI  = "#e8e8f0"
TEXT_SEC  = "#8888aa"
BORDER    = "#2a2a3a"
SUCCESS   = "#4ade80"
ERROR_CLR = "#f87171"
INPUT_BG  = "#13131c"


class CitationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CiteIt — Website Citation Generator")
        self.geometry("860x700")
        self.minsize(700, 560)
        self.configure(bg=DARK_BG)
        self.resizable(True, True)

        # Fonts
        self.f_display = font.Font(family="Georgia", size=20, weight="bold")
        self.f_sub     = font.Font(family="Georgia", size=11, slant="italic")
        self.f_label   = font.Font(family="Courier New", size=9, weight="bold")
        self.f_mono    = font.Font(family="Courier New", size=10)
        self.f_body    = font.Font(family="Georgia", size=11)
        self.f_btn     = font.Font(family="Courier New", size=10, weight="bold")

        self._build_ui()
        self._metadata = None

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────
        hdr = tk.Frame(self, bg=DARK_BG, pady=24)
        hdr.pack(fill="x", padx=36)

        tk.Label(
            hdr, text="CiteIt", font=self.f_display,
            fg=ACCENT2, bg=DARK_BG
        ).pack(side="left")

        tk.Label(
            hdr, text="  website citation generator",
            font=self.f_sub, fg=TEXT_SEC, bg=DARK_BG
        ).pack(side="left", pady=6)

        # ── URL input card ───────────────────────────────────
        url_card = tk.Frame(self, bg=CARD_BG, padx=24, pady=20)
        url_card.pack(fill="x", padx=36, pady=(0, 10))

        tk.Label(
            url_card, text="WEBSITE URL",
            font=self.f_label, fg=TEXT_SEC, bg=CARD_BG
        ).pack(anchor="w")

        row = tk.Frame(url_card, bg=CARD_BG)
        row.pack(fill="x", pady=(6, 0))

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            row, textvariable=self.url_var,
            font=self.f_body, bg=INPUT_BG, fg=TEXT_PRI,
            insertbackground=ACCENT2, relief="flat",
            bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT
        )
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=8, ipadx=10)
        self.url_entry.bind("<Return>", lambda e: self._generate())

        self.gen_btn = tk.Button(
            row, text="GENERATE →", font=self.f_btn,
            bg=ACCENT, fg="#ffffff", relief="flat",
            padx=16, pady=8, cursor="hand2",
            activebackground=ACCENT2, activeforeground="#fff",
            command=self._generate
        )
        self.gen_btn.pack(side="left", padx=(10, 0))

        # ── Status bar ──────────────────────────────────────
        self.status_var = tk.StringVar(value="Paste a URL above and press Generate.")
        self.status_lbl = tk.Label(
            self, textvariable=self.status_var,
            font=self.f_label, fg=TEXT_SEC, bg=DARK_BG
        )
        self.status_lbl.pack(anchor="w", padx=40, pady=(0, 6))

        # ── Citation cards ──────────────────────────────────
        self.cite_frame = tk.Frame(self, bg=DARK_BG)
        self.cite_frame.pack(fill="both", expand=True, padx=36, pady=(0, 24))

        self.cite_widgets = {}
        styles = list(STYLES.keys())
        for i, style in enumerate(styles):
            self._build_cite_card(style, i)

        # ── Metadata strip ─────────────────────────────────
        self.meta_var = tk.StringVar()
        tk.Label(
            self, textvariable=self.meta_var,
            font=font.Font(family="Courier New", size=8),
            fg=TEXT_SEC, bg=DARK_BG, wraplength=800, justify="left"
        ).pack(anchor="w", padx=40, pady=(0, 10))

    def _build_cite_card(self, style: str, idx: int):
        outer = tk.Frame(self.cite_frame, bg=CARD_BG, padx=18, pady=14)
        outer.pack(fill="x", pady=4)

        hdr_row = tk.Frame(outer, bg=CARD_BG)
        hdr_row.pack(fill="x")

        badge = tk.Label(
            hdr_row, text=style,
            font=self.f_label, fg=ACCENT2, bg=CARD_BG
        )
        badge.pack(side="left")

        copy_btn = tk.Button(
            hdr_row, text="COPY", font=self.f_label,
            bg=DARK_BG, fg=TEXT_SEC, relief="flat",
            padx=8, pady=2, cursor="hand2",
            activebackground=BORDER, activeforeground=TEXT_PRI,
            command=lambda s=style: self._copy(s)
        )
        copy_btn.pack(side="right")

        txt = tk.Text(
            outer, font=self.f_mono, bg=INPUT_BG, fg=TEXT_PRI,
            relief="flat", bd=0, wrap="word",
            height=3, padx=10, pady=8,
            highlightthickness=0,
            state="disabled"
        )
        txt.pack(fill="x", pady=(8, 0))

        self.cite_widgets[style] = (txt, copy_btn)

    def _set_status(self, msg: str, color: str = TEXT_SEC):
        self.status_var.set(msg)
        self.status_lbl.configure(fg=color)

    def _generate(self):
        url = self.url_var.get().strip()
        if not url:
            self._set_status("⚠  Please enter a URL.", ERROR_CLR)
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_var.set(url)

        if not LIBS_OK:
            messagebox.showerror(
                "Missing Libraries",
                "Please install required packages:\n\npip install requests beautifulsoup4"
            )
            return

        self._set_status("⏳  Fetching page metadata…", ACCENT2)
        self.gen_btn.configure(state="disabled", text="loading…")
        for style, (txt, _) in self.cite_widgets.items():
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            txt.insert("end", "Fetching…")
            txt.configure(state="disabled")

        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            meta = scrape_metadata(url)
            self.after(0, self._populate, meta)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _populate(self, meta: dict):
        self._metadata = meta
        for style, fn in STYLES.items():
            txt_widget, _ = self.cite_widgets[style]
            try:
                citation = fn(meta)
            except Exception as ex:
                citation = f"[Error generating {style} citation: {ex}]"
            txt_widget.configure(state="normal")
            txt_widget.delete("1.0", "end")
            txt_widget.insert("end", citation)
            txt_widget.configure(state="disabled")

        authors = ", ".join(meta["authors"]) if meta["authors"] else "—"
        self.meta_var.set(
            f"Title: {meta['title'][:80]}  │  Authors: {authors[:60]}  "
            f"│  Published: {meta['pub_date'] or '—'}  │  Site: {meta['site_name']}"
        )
        self._set_status("✓  Citations generated successfully.", SUCCESS)
        self.gen_btn.configure(state="normal", text="GENERATE →")

    def _on_error(self, msg: str):
        self._set_status(f"✗  Error: {msg}", ERROR_CLR)
        self.gen_btn.configure(state="normal", text="GENERATE →")
        for style, (txt, _) in self.cite_widgets.items():
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            txt.insert("end", "Could not fetch page. Check the URL and try again.")
            txt.configure(state="disabled")

    def _copy(self, style: str):
        txt_widget, btn = self.cite_widgets[style]
        content = txt_widget.get("1.0", "end").strip()
        if content and "Fetching" not in content and "Could not" not in content:
            self.clipboard_clear()
            self.clipboard_append(content)
            original = btn.cget("text")
            btn.configure(text="✓ COPIED", fg=SUCCESS)
            self.after(1500, lambda: btn.configure(text=original, fg=TEXT_SEC))


if __name__ == "__main__":
    app = CitationApp()
    app.mainloop()
