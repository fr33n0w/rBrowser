# rBrowser

Standalone NomadNet Browser — a modern, web-based UI for exploring **NomadNet** nodes and pages over the **Reticulum** network.

![rBrowser screenshot](https://github.com/user-attachments/assets/3f753eed-49c5-4d89-820b-e1dc1a8cb383)

---

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Reticulum](https://img.shields.io/badge/Reticulum-supported-yellow.svg)](https://github.com/markqvist/Reticulum)

---

## 🧭 Overview

**rBrowser** is a standalone web browser built to interact with the **NomadNet** distributed network running on **Reticulum**. It automatically discovers nearby NomadNet nodes, fetches their pages, and renders them using Micron markup.

It offers a familiar browser-like interface (with address bar, navigation buttons, favorites, and more) while connecting to the decentralized Reticulum network.

---

## 📑 Table of Contents

* [Features](#-features)
* [Requirements](#-requirements)
* [Installation](#-installation)

  * [Option 1 — Run from Terminal](#option-1--run-from-terminal)
  * [Option 2 — Run with Docker](#option-2--run-with-docker)
* [Running the Browser](#-running-the-browser)
* [Usage](#-usage)
* [Currently Implemented](#-currently-implemented)
* [Planned Improvements](#-planned-improvements)
* [Known Issues](#-known-issues)
* [Troubleshooting](#-troubleshooting)
* [License](#-license)
* [Contributing](#-contributing)
* [Screenshots](#-screenshots)

---

## ✨ Features

* 🔍 **Real-time node discovery** — detects NomadNet nodes as they announce
* 🌐 **Web interface** — modern UI served at `http://localhost:5000`
* 🧾 **Micron parser** — renders Micron markup properly
* 🔗 **URL navigation** — manual address bar input with back/forward buttons
* 🧭 **Dual view modes** — Rendered and Raw Micron source
* ⭐ **Favorites system** — bookmark nodes/pages
* 📦 **File download** — download content hosted on NomadNet
* 🧠 **Search engine** — optional local page cache and search
* 👤 **Node info** — view extended details and send identity/fingerprint
* 🧰 **Cross-platform** — Linux, macOS, Windows supported
* 🐳 **Docker-ready** — easy containerized deployment

---

## 🧰 Requirements

### System

* Python **3.7+**
* Linux / macOS / Windows
* Access to a **Reticulum** network (via radio, TCP, or local testnet)

### Python Dependencies

* `reticulum` (RNS >= 1.0.0)
* `flask` >= 2.0.0
* `waitress` *(Windows)* or `gunicorn` *(Linux)* — recommended for production

---

## ⚙️ Installation

You can run **rBrowser** either from your terminal or inside Docker.

### Option 1 — Run from Terminal

```bash
git clone https://github.com/fr33n0w/rBrowser.git
cd rBrowser
pip install -r requirements.txt
```

Ensure you have a **Reticulum** instance configured (with at least one `TCPClientInterface`) in `~/.reticulum/config`. The browser will automatically connect to it.

Then run:

```bash
python3 rBrowser.py
```

Visit `http://localhost:5000` in your web browser.

---

### Option 2 — Run with Docker

#### Prerequisites

Ensure you have Docker and Docker Compose installed:

```bash
docker --version
docker compose version
```

#### Quick Start

```bash
git clone https://github.com/fr33n0w/rBrowser.git
cd rBrowser
docker compose up -d
docker compose logs -f rbrowser
```

The web UI will be available at [http://localhost:5000](http://localhost:5000).

📌 Tip: Ensure your Reticulum config is available to the container. You can mount your local config:

```yaml
volumes:
  - ./config:/home/appuser/.reticulum/config:ro
```

---

## 🚀 Running the Browser

Once started, open your browser and visit:

```
http://localhost:5000
```

The app will:

* Listen for NomadNet node announces
* Display discovered nodes in the sidebar
* Let you navigate between nodes/pages

---

## 🧭 Usage

### Supported URLs

* `hash:/page/index.mu`
* `nomadnetwork://hash/page/index.mu`
* `hash` *(defaults to /page/index.mu)*

### Navigation Tools

* **Address bar** — type NomadNet URLs
* **Sidebar** — browse discovered nodes
* **Favorites** — save frequently visited nodes/pages
* **Search** — use built-in search engine (if enabled)
* **Toggle view** — switch between rendered and raw Micron

---

## ✅ Currently Implemented

* Full Reticulum integration
* Real-time node discovery
* Page fetching and Micron rendering
* URL navigation + history
* In-app notifications and logs
* Local caching + search engine
* Docker container build
* Cross-platform support

---

## 🧩 Planned Improvements

* Prebuilt executables for Windows/Linux/macOS
* Enhanced error handling and metrics
* Improved mobile UI

---

## ⚠️ Known Issues

* Some nodes may fail to handle input-box submissions if using non-standard Micron link formats.

---

## 🛠 Troubleshooting

### No nodes appearing

* Verify Reticulum config and connectivity
* Ensure NomadNet nodes are active

### Page loading fails

* Confirm target node is online
* Check Reticulum interface

### Rendering issues

* Check `micronparser.js` presence
* Switch to **Raw View** to debug

---

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions and pull requests are welcome! For bug reports, open an issue or contact via LXMF:

```
0d051f3b6f844380c3e0c5d14e37fac8
```

---

## 🖼 Screenshots

### Navigation Example

![navigation example](https://github.com/user-attachments/assets/9c5c4335-2ad9-4367-9c2f-2fcd5cc6693d)

### Node Information View

![node info](https://github.com/user-attachments/assets/5ede3dd3-9e39-433d-ac6d-19b87549ee3f)

### Search Engine Feature

![search engine](https://github.com/user-attachments/assets/c1636e8f-860b-4e0a-867f-568eacd186d7)

![search results](https://github.com/user-attachments/assets/f00b815a-ce6e-4831-aa53-b64ce3a36c73)

---

❤️ Developed with love by **Franky & Thomas** ❤️
