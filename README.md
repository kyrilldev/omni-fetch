# ⚡️ OmniFetch

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/powered_by-Playwright-2EAD33.svg)](https://playwright.dev/)

**Stop writing brittle scraping scripts. Treat the entire web like an API.**

OmniFetch is a highly concurrent, locally deployable micro-service that seamlessly converts complex, JavaScript-heavy websites into clean, structured JSON. It handles the messy parts of web extraction—browser management, bot-bypassing, network idling, and data normalization—so you can just ask for the data you need.

---

## ✨ Key Features

* **🚀 Blazing Fast:** Maintains a warm pool of headless Chromium contexts. Aggressively blocks trackers, fonts, and images to load pages up to 10x faster than standard browsers.
* **🧠 Two Extraction Modes:**
    * **Precision Mode:** Pass in a dictionary of CSS selectors for lightning-fast, traditional data extraction.
    * **Semantic Mode (AI):** Just describe what you want (e.g., `"Get the main article text and author"`). OmniFetch uses a local LLM or heuristic engine to map your prompt to the DOM automatically.
* **🛡️ Stealth & Anti-Bot Native:** Built-in fingerprint patching to bypass common anti-bot protections like Cloudflare.
* **⏳ Smart Waits:** No more `time.sleep()`. OmniFetch explicitly waits for network idle states or specific DOM mutations before attempting extraction.
* **📦 Easily Shippable:** Run it locally as a Python package or spin it up in seconds using our pre-configured Docker container.

---

## 🏗️ How it Works

Instead of launching a browser every time you write a script, OmniFetch runs as a persistent local server. You send it a URL and a **Schema**, and it returns JSON.

1.  **Request:** Your app sends a POST request with a target URL and the data schema.
2.  **Navigate:** OmniFetch's background engine navigates to the site using a cloaked, optimized browser instance.
3.  **Distill:** It strips away the visual noise (CSS, Ads, Scripts) leaving only the raw data tree.
4.  **Extract:** It matches your schema to the tree, normalizes the data types, and returns a clean JSON response.

---

## 💻 Quick Start

### 1. Start the OmniFetch Engine
Run the local server (this keeps the browser engine warm in the background).
```bash
# Clone and run the server
git clone [https://github.com/yourusername/omnifetch.git](https://github.com/yourusername/omnifetch.git)
cd omnifetch
python server.py 
# Engine running on [http://127.0.0.1:8000](http://127.0.0.1:8000) 🚀
