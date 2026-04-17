# CiteIt — Website Citation Generator

A lightweight desktop app that generates properly formatted citations from any URL — no account, no internet subscription, no fuss.

---

## Features

- **5 citation formats** — APA 7th, MLA 9th, Chicago 17th, Harvard, and IEEE
- **One-click copy** for each citation style
- **Auto-extracts metadata** — title, authors, publish date, and publisher from Open Graph tags, JSON-LD, and standard meta tags
- **Runs offline** after the initial page fetch
- Packages into a single `.exe` (Windows) or `.app` (macOS) — no Python required for end users

---

## Screenshots

> Paste a URL → press Generate → copy your citation.

---

## Installation (run from source)

**Prerequisites:** Python 3.8+

```bash
# 1. Clone or download the project
# 2. Install dependencies
pip install requests beautifulsoup4

# 3. Run the app
python cite_generator.py
```

---

## Building the Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Windows / macOS — single file, no console window
pyinstaller --onefile --windowed --name "CiteIt" cite_generator.py
```

Output will be at `dist/CiteIt.exe` (Windows) or `dist/CiteIt` (macOS).

> **Note:** Some antivirus software may flag PyInstaller-built executables as suspicious. This is a known false positive. You can whitelist the file safely.

---

## Citation Formats

| Format | Example output style |
|---|---|
| **APA 7th** | Smith, J. (2024). *Title*. Site Name. Retrieved 2024-01-01, from https://… |
| **MLA 9th** | Smith, John. "Title." *Site Name*, 1 Jan. 2024, https://… |
| **Chicago 17th** | Smith, John. "Title." Site Name. Published January 1, 2024. Accessed… |
| **Harvard** | Smith, J. (2024) 'Title', *Site Name*. Available at: https://… |
| **IEEE** | J. Smith, "Title," *Site Name*. [Online]. Available: https://… |

---

## How It Works

1. You paste a URL and press **Generate**
2. The app fetches the page HTML in a background thread
3. Metadata is extracted in priority order:
   - Open Graph tags (`og:title`, `og:site_name`, `article:published_time`, …)
   - JSON-LD structured data (`@type: Article`, `author`, …)
   - Standard `<meta>` tags (`author`, `date`, `description`, …)
   - Fallback to `<title>` tag and domain name
4. Each citation format is rendered and displayed with a **COPY** button

---

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | Fetching page HTML |
| `beautifulsoup4` | Parsing HTML and extracting metadata |
| `tkinter` | GUI (included with Python) |
| `pyinstaller` | Building the `.exe` / `.app` (build-time only) |

---

## Limitations

- Some sites block automated requests or require JavaScript to render content — metadata may be incomplete for these
- Author detection works best on news articles and blog posts with proper meta tags
- Paywalled or login-required pages cannot be accessed

---

## License

MIT — do whatever you want with it.
