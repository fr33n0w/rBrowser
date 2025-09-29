# rBrowser
Standalone NomadNet Browser

![rBrowser screenshot](https://github.com/user-attachments/assets/3f753eed-49c5-4d89-820b-e1dc1a8cb383)

A standalone, web-based UI for exploring NomadNet nodes and pages over the Reticulum network. rBrowser automatically discovers NomadNet nodes via announces and provides a friendly interface for browsing distributed content with Micron markup support.

Table of contents
- Features
- Requirements
- Installation (Terminal / Docker)
- Running the browser
- Usage and navigation
- Currently implemented
- Next improvements
- Known issues & troubleshooting
- License & contributing

-----

## Features

- Real-time node discovery: automatically detects and lists NomadNet nodes as they announce on the network
- Web-based interface: modern, responsive UI served on http://localhost:5000
- Micron parser: renders NomadNet's Micron markup with proper formatting and styling
- URL navigation: address bar with back/forward navigation and manual URL input
- Dual view modes: toggle between rendered Micron content and raw source (Rendered / Raw)
- Link navigation: click links within Micron content to navigate between pages
- Connection status: real-time display of network status and discovered pages / announced nodes
- File download support: download files hosted on NomadNet nodes
- Local NomadNet search engine: search local auto-cached pages (if enabled)
- Favorites: add nodes/pages to favorites (star button synced across UI tabs)
- Node info: extended information for remote nodes in the node list
- Fingerprint/identify: send identity and LXMF address to a remote host
- Notifications & logs: in-UI notifications and full operational logs in the terminal

-----

## Requirements

### System

- Python 3.7 or higher
- Linux, macOS, or Windows
- Access to a Reticulum network (radio interfaces, internet gateways, or a local testnet)

### Python dependencies

- `reticulum` (rns >= 1.0.0) — Reticulum networking protocol stack for connection and NomadNet retrieval
- `flask` >= 2.0.0 — web framework used for the UI
- `waitress` — recommended for Windows deployment
- `gunicorn` — recommended for Linux deployment

-----

## Installation

There are two main ways to run rBrowser: directly from the terminal or inside Docker.

### Option 1 — Run from terminal

1. Clone the repository:

```bash
git clone https://github.com/fr33n0w/rBrowser.git
cd rBrowser
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Configure Reticulum:

Before launching the script you need a working Reticulum instance. Configure at least one TCPClientInterface in `./reticulum/config`. You don't need to run an RNS process manually—just ensure your Reticulum instance can connect to the network.

-----

### Option 2 — Docker & Docker Compose

This repository includes a `Dockerfile` and a `docker-compose.yaml` so you can run rBrowser in a container. The compose setup builds the image and exposes the web UI on port 5000.

Prerequisites: Docker and Docker Compose. Check versions:

```bash
docker --version
docker compose version
```

If you need to install Docker on Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install docker.io
```

To install Docker Compose (standalone):

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Quick start with Docker:

```bash
# Add current user to docker group (may require logout/login):
sudo usermod -aG docker $USER

git clone https://github.com/fr33n0w/rBrowser
cd rBrowser
docker compose up -d
docker compose logs -f rbrowser
docker compose build --no-cache rbrowser


# rBrowser v1.0 — Standalone NomadNet Browser

![rBrowser screenshot](https://github.com/user-attachments/assets/3f753eed-49c5-4d89-820b-e1dc1a8cb383)

<!-- Badges -->
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A standalone, web-based UI for exploring NomadNet nodes and pages over the Reticulum network. rBrowser automatically discovers NomadNet nodes via announces and provides a friendly interface for browsing distributed content with Micron markup support.

## Quick start

Use one of the two simplest ways to get running:

- Run locally (requires Python and Reticulum configured):

```bash
pip install -r requirements.txt
python3 rBrowser.py
```

- Run with Docker Compose (recommended for a contained environment):

```bash
docker compose up -d
docker compose logs -f rbrowser
```

## Table of contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Option 1 — Run from terminal](#option-1---run-from-terminal)
  - [Option 2 — Docker & Docker Compose](#option-2---docker--docker-compose)
- [Running the browser](#running-the-browser)
- [Usage](#usage)
- [Currently implemented](#currently-implemented)
- [Next implementations](#next-implementations)
- [Known issues](#known-issues)
- [Bug reports](#bug-reports)
- [Development notes](#development-notes)
- [Troubleshooting](#troubleshooting)
- [Warning](#warning)
- [License](#license)
- [Contributing](#contributing)
- [External dependencies](#external-dependencies)
- [Screenshots](#screenshots)

-----

## Features

- Real-time node discovery: automatically detects and lists NomadNet nodes as they announce on the network
- Web-based interface: modern, responsive UI served on http://localhost:5000
- Micron parser: renders NomadNet's Micron markup with proper formatting and styling
- URL navigation: address bar with back/forward navigation and manual URL input
- Dual view modes: toggle between rendered Micron content and raw source (Rendered / Raw)
- Link navigation: click links within Micron content to navigate between pages
- Connection status: real-time display of network status and discovered pages / announced nodes
- File download support: download files hosted on NomadNet nodes
- Local NomadNet search engine: search local auto-cached pages (if enabled)
- Favorites: add nodes/pages to favorites (star button synced across UI tabs)
- Node info: extended information for remote nodes in the node list
- Fingerprint/identify: send identity and LXMF address to a remote host
- Notifications & logs: in-UI notifications and full operational logs in the terminal

-----

## Requirements

### System

- Python 3.7 or higher
- Linux, macOS, or Windows
- Access to a Reticulum network (radio interfaces, internet gateways, or a local testnet)

### Python dependencies

- `reticulum` (rns >= 1.0.0) — Reticulum networking protocol stack for connection and NomadNet retrieval
- `flask` >= 2.0.0 — web framework used for the UI
- `waitress` — recommended for Windows deployment
- `gunicorn` — recommended for Linux deployment

-----

## Installation

There are two main ways to run rBrowser: directly from the terminal or inside Docker.

### Option 1 — Run from terminal

1. Clone the repository:

```bash
git clone https://github.com/fr33n0w/rBrowser.git
cd rBrowser
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Configure Reticulum:

Before launching the script you need a working Reticulum instance. Configure at least one TCPClientInterface in `./reticulum/config`. You don't need to run an RNS process manually—just ensure your Reticulum instance can connect to the network.

-----

### Option 2 — Docker & Docker Compose

This repository includes a `Dockerfile` and a `docker-compose.yaml` so you can run rBrowser in a container. The compose setup builds the image and exposes the web UI on port 5000.

Prerequisites: Docker and Docker Compose. Check versions:

```bash
docker --version
docker compose version
```

If you need to install Docker on Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install docker.io
```

To install Docker Compose (standalone):

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Quick start with Docker:

```bash
# Add current user to docker group (may require logout/login):
sudo usermod -aG docker $USER

git clone https://github.com/fr33n0w/rBrowser
cd rBrowser
docker compose up -d
docker compose logs -f rbrowser
```

Useful Docker commands:

```bash
docker compose build --no-cache rbrowser
docker compose up -d
docker compose down
docker ps
```

Notes:
- The `Dockerfile` copies a repository `config` file into the container at `/home/appuser/.reticulum/config`. Ensure you have a valid Reticulum config file named `config` in the repo root before building, or mount your own config at runtime, for example:

```yaml
volumes:
  - ./config:/home/appuser/.reticulum/config:ro
```

- Use `docker compose ps` to check service and healthcheck status. The compose file includes a basic HTTP healthcheck.

-----

## Running the browser

1. Start the browser (terminal installation):

```bash
python3 rBrowser.py
```

2. Open your web browser and go to:

```
http://localhost:5000
```

3. Wait for node discovery:

- The browser listens for NomadNet announces
- Discovered nodes appear in the left sidebar
- Click a node to browse its content and navigate pages
- You can paste an address in the address bar without waiting for announces
- Check the bottom-left status bar for connection information

-----

## Usage

### Supported URL formats

- `hash:/page/index.mu` — direct hash with page path
- `nomadnetwork://hash/page/index.mu` — full protocol URL
- `hash` — hash only (defaults to `/page/index.mu`)
- `:page/index.mu`field`content` — pages with input field in URL

### Navigation

- Address bar: enter NomadNet URLs manually
- Back/Forward: browsing history navigation
- Refresh: reload the current page
- Node sidebar: click any discovered node to browse
- Link clicking: navigate by clicking links within Micron content
- Add favorites: save favorite nodes/pages for quick access
- Search: use the built-in NomadNet search engine to discover content (if enabled)
- Identify remote nodes: send fingerprint (identity and LXMF address) to a remote node

### Page view modes

- Rendered view: displays Micron markup with formatting
- Raw view: shows the original Micron source

-----

## Currently implemented

- ✅ Reticulum network integration: full connection to the Reticulum mesh
- ✅ NomadNet node discovery: real-time announce monitoring and node listing
- ✅ Page fetching: request and receive pages from remote nodes
- ✅ Micron rendering: parse and display Micron markup
- ✅ Web interface: browser-style UI with navigation
- ✅ URL navigation: manual input via address bar
- ✅ Navigation history: back/forward buttons
- ✅ Link detection: automatic NomadNet URL detection in content
- ✅ Click navigation: follow links in rendered content
- ✅ Notification system: in-UI notifications and info box
- ✅ Multiple URL formats: enhanced parsing for various NomadNet URL conventions
- ✅ Page title extraction: display proper page titles in UI
- ✅ Navigation breadcrumbs: show current node and path
- ✅ Link preview: hover tooltips with destination URLs
- ✅ Dual view modes: rendered and raw text views
- ✅ Error handling: robust handling for network issues and timeouts
- ✅ Complete local usage: scripts, CSS and JS are included (no external CDN calls)
- ✅ Bookmark system: save frequently visited nodes and pages (Favorites bar)
- ✅ Multi-tab navigation: open links in new browser tabs
- ✅ Navigation shortcuts: keyboard shortcuts for tab navigation, new/close/reload
- ✅ Web UI servers: waitress and gunicorn production-ready; fallback to Flask if missing
- ✅ File download: download files hosted on NomadNet nodes with progress notification
- ✅ User input support: forms, URLs, and input boxes are supported
- ✅ Fingerprint: send identity and LXMF address to a host node
- ✅ NomadNet search engine: local page-caching search engine
- ✅ Optimized UI: responsive layout for mobile and tablet devices
- ✅ Docker version: containerized deployment with dependencies included

-----

## Next implementations

- Windows, Linux and macOS executable apps (planned)

-----

## Known issues

- Sometimes sending input box parameters fails on some nodes with non-standard NomadNet Micron link formats due to custom user fields. (Note: >95% of nodes pages work correctly.)

-----

## Bug reports

If you find bugs or other issues, contact the developer on Reticulum at LXMF address: `0d051f3b6f844380c3e0c5d14e37fac8`, or open a GitHub issue.

-----

## Development notes

- The browser creates an identity file (`nomadnet_browser_identity`) on first run
- Reticulum configuration is stored in the default location (`~/.reticulum/`)
- The application uses a single-page application with AJAX content loading
- A fallback Micron parser is included if the original parser fails to load
- Detailed logs are printed by the Python script in the terminal
- If the search engine is enabled (ON by default), NomadNet pages are cached locally in `/cache/nodes`

-----

## Troubleshooting

No nodes appearing:
- Verify Reticulum network connectivity and configuration
- Ensure NomadNet nodes are active on the network
- Check that your firewall allows Reticulum traffic

Page loading failures:
- Confirm the target node is online and reachable
- Verify network connectivity to the Reticulum network
- Ensure the requested page path exists on the target node

Micron rendering issues:
- Ensure `micron-parser_original.js` is present in the `script/` directory
- Check the browser console for JavaScript errors
- Toggle to Raw View to inspect source content

If disconnected:
- Check the bottom-left status bar for connection info
- Verify the Python script is running
- Verify your RNS/Reticulum config before running the script
- Check critical logs printed to the terminal from the Reticulum instance

Common errors:
- Failed to initialize: attempt to reinitialize Reticulum while it is already running — close other Reticulum processes
- Reticulum error logs: inspect `/youruser/.reticulum/config` for misconfiguration

-----

## Warning

The included search engine generates network traffic when enabled by requesting remote pages. By default it only requests `index.mu`, but you can enable fetching additional pages via the Search Engine settings.

IF YOU ARE USING LoRa INTERFACES, DISABLE THE SEARCH ENGINE TO AVOID CONSUMING AIRTIME AND GENERATING UNWANTED NETWORK TRAFFIC.

-----

## License

This project is open source. Use and share freely. Please refer to the `LICENSE` file for details.

-----

## Contributing

Contributions are welcome. Please submit pull requests or open issues for bugs and feature requests.

-----

## External dependencies

This project includes local copies of:

- `micronparser.js` — Micron rendering for NomadNet pages
- `DOMPurify.min.js` — HTML sanitization

The web UI is served by:

- Flask (developer server, fallback)
- waitress (production server for Windows)
- gunicorn (production server for Linux)

External software and their rights are owned by their respective developers.

-----

## Screenshots

Example of link navigation with input field requests:

![navigation example](https://github.com/user-attachments/assets/9c5c4335-2ad9-4367-9c2f-2fcd5cc6693d)

Example of extended node information:

![node info](https://github.com/user-attachments/assets/5ede3dd3-9e39-433d-ac6d-19b87549ee3f)

Example of the included search engine feature:

![search engine](https://github.com/user-attachments/assets/c1636e8f-860b-4e0a-867f-568eacd186d7)

![search results](https://github.com/user-attachments/assets/f00b815a-ce6e-4831-aa53-b64ce3a36c73)

-----

❤️ Developed with love by Franky & Thomas ❤️
