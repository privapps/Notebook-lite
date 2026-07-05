# Notebook Lite

A lightweight, read-only PrivateBin reader. Only decrypts and displays encrypted content.

## Features

- **Small size**: ~144KB total (source), ~106KB (minified bundle)
- **No dependencies**: Vanilla JavaScript
- **Static hosting**: Works on any HTTP server (GitHub Pages, Netlify, etc.)
- **Password support**: Integrated password prompt for protected pastes
- **Markdown rendering**: Renders decrypted content as markdown
- **Syntax Highlighting**: Prism.js integration for code blocks (JS, Python, JSON)
- **Inline Data**: Support for loading content directly from the URL hash
- **Easy sharing**: Auto-updates URL for simple copy-pasting (hides password)
- **Dark mode**: Toggle between light and dark themes (persisted to localStorage)
- **GitHub link**: Quick access to the source repository from the content header

## Usage

### Manual Input
1. Open `index.html` in a browser
2. Enter a PrivateBin URL (e.g., `https://privatebin.net/?abc123#key`)
3. Enter password if required
4. Click "Decrypt"

### Direct URL (auto-decrypt)

**Query params:**
```
index.html?url=https://privatebin.net/p/epppa&key=abc
```

**Hash format:**
```
index.html#abc@https://privatebin.net/p/epppa
```

**Inline Data format:**
```
index.html#key@base64data
```

**Sample URL:**
```
https://privapps.github.io/Notebook-lite/#Hj84nE4pQW4iBXhXhGf3wNeHqtYzGsupFFZHYgDDffjw@https://privapps.github.io/notebook/data/peppa
```

## File Structure

```
notebook-lite/
├── index.html               # Main application
├── prism-tomorrow.min.css   # Syntax highlighting theme
├── base-x-3.0.7.js          # Base58 encoding
├── rawinflate-0.3.js        # JS inflate
├── marked.min.js            # Markdown parser
├── prism.min.js             # Syntax highlighting core
├── prism-javascript.min.js  # JS syntax support
├── prism-python.min.js      # Python syntax support
├── prism-json.min.js        # JSON syntax support
├── dompurify.min.js         # HTML sanitization
├── build.py                 # Build & Minification script
└── README.md
```

## Size Comparison

| Version | Size |
|---------|------|
| Original (Angular) | ~2MB+ |
| notebook-lite (source) | ~144KB (all files) |
| notebook-lite (bundle) | ~106KB (single minified file) |

## Build

To bundle all dependencies into a single, portable, and minified HTML file:

```bash
uv run python3 build.py
```

This will create `build/index.html` (~106KB), which contains all CSS and JS inlined and minified.

## Requirements

- Modern browser with Web Crypto API support
- JavaScript enabled

## Hosting

Simply serve the files with any static HTTP server:

```bash
# Python
python3 -m http.server 8080

# Node.js
npx serve .
```
