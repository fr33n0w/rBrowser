# rBrowser: Standalone NomadNet Browser

A modern, web-based UI for exploring **NomadNet** nodes and pages over the **Reticulum** network.

<img width="1920" height="1080" alt="1" src="https://github.com/user-attachments/assets/23771984-fc0c-454a-bb43-c6212cdc76a7" />

---

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![WebUI](https://img.shields.io/badge/Local-Web%20UI-green.svg)](http://localhost:5000)
[![Reticulum](https://img.shields.io/badge/Reticulum-supported-yellow.svg)](https://github.com/markqvist/Reticulum)
[![Developer Frank](https://img.shields.io/badge/Developer-Frank-blue.svg)](https://github.com/fr33n0w)
[![Developer neoemit](https://img.shields.io/badge/Developer-neoemit-blue.svg)](https://github.com/neoemit)
---

# 🧭 Overview

# rBrowser v1.0:

**rBrowser** is cross-platform, standalone, web-based UI Browser for exploring NomadNetwork Nodes over Reticulum Network. 

Automatically discovers NomadNet nodes through network announces and provides a user-friendly interface for browsing distributed content with Micron markup support.

It includes some exclusive features like: Automatic listening for announce, Add nodes to favorites, browse and render any kind of NomadNet links, download files from remote nodes, unique local **NomadNet Search Engine** and more...

**rBrowser** offers a familiar browser-like interface expereience (with address bar, navigation buttons, favorites, and more) while connecting to the decentralized Reticulum network.

Web-Based UI: the rBrowser interface is spawned via local web server (default host 0.0.0.0, default port 5000, both configurable).

-----

## 📑 Table of Contents

* [• 🧭 Overview](#-overview)
  * [✨ Features](#-features)
* [• 📋 Requirements](#-requirements)
  * [🧰 System Requirements](#-system-requirements)
  * [🐍 Python Dependencies](#-python-dependencies-included-in-requirementstxt)
* [• ⚙️ Installation](#️-installation)
  * [⚡ Prerequisites](#-prerequisites)
  * [💻 Install Option 1: Run from Terminal](#-install-option-1-run-from-terminal)
  * [🐳 Install Option 2: Docker & Docker Compose](#-install-option-2-docker--docker-compose)
  * [📱 Install Option 3: Termux on Android](#-install-option-3-termux-on-android)
* [• 🚀 Usage](#-usage)
  * [🔗 URL Formats Supported](#-url-formats-supported)
  * [🧭 Navigation](#-navigation)
  * [👁️ Pages View Mode](#️-pages-view-mode)
* [• ✅ Currently Implemented](#-currently-implemented)
* [• 🧩 Next Implementations](#-next-implementations)
* [• ⚠️ Known Issues](#️-known-issues)
* [• 🐛 Bug or Issues Report](#-bug-or-issues-report)
* [• 💡 Development Notes](#-development-notes)
* [• 🛠 Troubleshooting](#-troubleshooting)
* [• ⚠️ Traffic Usage Warning](#️-traffic-usage-warning)
* [• 📜 License](#-license)
* [• 🤝 Contributing](#-contributing)
* [• 📦 External Dependencies](#-external-dependencies)
* [• 🖼 Screenshots](#-screenshots)

-----

## ✨ Features:

- 📡 **Real-time Node Discovery**: Detects and lists NomadNetwork nodes as they announce on the network
- 🌐 **Web-based Interface**: Modern, responsive browser interface accessible at `localhost:5000`
- 📝 **Micron Parser**: Renders NomadNet's Micron markup language with proper formatting and styling
- 🧭 **URL Navigation**: Address bar with back/forward navigation and manual URL input
- 👁️ **Dual View Modes**: Toggle between Rendered Micron content and Raw page view
- 🔗 **Link Navigation**: Click on links within Micron content to navigate between pages
- 📊 **Connection Status**: Real-time display of network status and discovered pages / announced nodes
- 📥 **File Download Support**: Download files hosted on nomadnet nodes
- 🔍 **NomadNet Search Engine**: Unique search engine system to search in local auto-cached pages if enabled
- ⭐ **Add To Favorites**: Favorite system with star button synched across the whole UI tabs
- ℹ️ **Node Info**: Extended node info for remote node hosting page in the node list
- 🔐 **Fingerprint**: Allow to identify with identity and LXMF address to remote host with a button
- 🔔 **Notifications & Logs**: Comprehensive Notifications info box in the web ui + full operational log in the terminal 
- 🎉 **And more......**: Download rBrowser and try it now!!

## 📋 Requirements

### 🧰 System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Linux, macOS, or Windows
- **Network**: Access to a Reticulum network (radio interfaces, internet gateways, or local testnet)

### 🐍 Python Dependencies (included in requirements.txt)

- `reticulum` >= rns 1.0.0 - Reticulum networking protocol stack for connection and NomadNetwork retrival
- `flask` >= 2.0.0 - Base Web framework for the browser UI interface
- `waitress` >=2.1.2 - Web Server Framework


-----

## ⚙️ Installation

### ⚡ PREREQUISITES:

**Configure Reticulum:**
   
- Before launching the script or the Docker image, you need a full configured and working instance of Reticulum, 
- At least one TCPClientInterface in your ./reticulum/config file to access NomadNetwork 

NOTE: You don't need to run RNS manually, just make sure your instance is working and can connect to Reticulum Network!


## 💻 Install Option 1: Run from terminal

1. **Clone the repository:**

   ```bash
   git clone https://github.com/fr33n0w/rBrowser.git
   cd rBrowser
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start rBrowser:**
   ```bash
   python3 rBrowser.py [--host HOST] [--port PORT]
   ```

4. **Open your web browser and navigate to:**
   ```
   http://localhost:PORT
   ```
   (Default port is 5000, default host is 0.0.0.0 if not specified)

5. **Wait for node discovery:**

   - The browser will start listening for NomadNetwork announces
   - Discovered nodes will appear in the left sidebar
   - Click on any node to browse its content and navigate pages
   - or manually paste address in the bar without waiting for announces
   - Check bottom-left Status Bar for connection status info 


---

## 🐳 Install Option 2: Docker & Docker Compose

- This repository includes a Dockerfile and a docker-compose.yaml so you can run rBrowser in a container. 
- The compose setup builds the image and exposes the web UI on port 5000.

### Prerequisites

#### Install Docker and Docker Compose

```bash
# Check if already installed

docker --version
docker-compose --version

# If not installed on Debian/Ubuntu

# Install Docker

sudo apt-get update
sudo apt-get install docker.io

# Install Docker Compose (standalone)

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

```

### Quick Start (with Docker installed)

```bash
# Configure Docker User Permissions

# Add current user to docker group (if not already present)
sudo usermod -aG docker $USER

# IMPORTANT: Log out and log back in for the group change to take effect

# Clone repo
git clone https://github.com/fr33n0w/rBrowser

# Enter root repo directory
cd rBrowser

# Build and start in background
docker compose up -d

# Follow logs
docker compose logs -f rbrowser


# Useful Commands

# Rebuild image and restart
docker compose build --no-cache rbrowser
docker compose up -d

# Stop the container
docker compose down

# View running containers
docker ps

```

Notes:
- The Dockerfile copies a repository `config` file into the container at /home/appuser/.reticulum/config. Ensure you have a valid Reticulum config file named `config` in the repo root before building, or mount your config at runtime:
  - Example volume override in docker-compose.yaml:
    volumes:
      - ./config:/home/appuser/.reticulum/config:ro
- Use `docker compose ps` to check service and healthcheck status (compose file includes a basic HTTP healthcheck).
- Stop and remove containers with `docker compose down`

## At the end, open the rBrowser UI at: http://localhost:5000 (or your configured port)

## 📱 Install Option 3: Termux on Android

You can run rBrowser directly on Android by using [Termux](https://termux.dev/), which gives you a full Linux environment. This keeps the Python code unchanged but lets you browse the UI from the same handset.

1. **Install Termux**
   - Install the latest Termux build from [F-Droid](https://f-droid.org/packages/com.termux/) (Play Store builds are outdated).
   - Open Termux once so it completes its storage setup.

2. **Prepare the environment**
   ```bash
   pkg update && pkg upgrade
   pkg install python git clang rust binutils make cmake pkg-config libffi openssl libsodium

   # Optional but recommended
   pip install --upgrade pip
   ```
   - The `cryptography` dependency (pulled in by Reticulum) builds from source on Android, so Rust, clang, and common build tools must be installed.
   - Reticulum uses cryptography and libsodium; Termux packages provide the required native libraries.
   - If you plan to keep the session alive while the screen is off, run `termux-wake-lock`.

3. **Clone and install dependencies**
   ```bash
   git clone https://github.com/fr33n0w/rBrowser.git
   cd rBrowser
   pip install -r requirements.txt
   ```
   - If pip still exits with `Rust not found` or `Unsupported platform` errors, verify `rustc --version` runs inside Termux and rerun the install.

4. **Configure Reticulum**
   - Ensure your Reticulum config is available in `~/.reticulum/config` (Termux home is `/data/data/com.termux/files/home`).
   - You can copy an existing config or bootstrap Reticulum inside Termux following the [Reticulum docs](https://reticulum.network/).

5. **Run rBrowser**
   ```bash
   python3 rBrowser.py --host 127.0.0.1 --port 5000
   ```
   - `127.0.0.1` keeps the web UI bound to the phone. Use `--host 0.0.0.0` if you want to reach it from another device on the same network.

6. **Open the interface**
   - In Android’s browser (Chrome, Firefox, etc.), visit `http://127.0.0.1:5000`.
   - Keep Termux in the foreground or use `termux-wake-lock` + Android’s battery settings to prevent the OS from suspending the session.

7. **Stopping**
   - Press `Ctrl+C` in Termux to stop the server, then `termux-wake-unlock` if you enabled the wake lock.

> **Tip:** For quicker restarts, create a small shell script in Termux (e.g., `~/start-rbrowser.sh`) that activates a virtual environment, runs rBrowser, and acquires the wake lock before launching.

> **Please note:** The current UI is not fully optimized for small screen mobile devices, improvements will come soon.

### Termux Troubleshooting

- **“Permission denied / Address already in use” when starting Reticulum**  
  Reticulum tries to start a shared instance and bind the interfaces defined in `~/.reticulum/config`. On Android, the default Unix socket path (`/var/run/reticulum.sock`) is not writable, and a previous Reticulum session may still hold the network ports. Fix it by either:
  1. Stopping any old process: `pkill -f reticulum` (run inside Termux); or
  2. Editing your Reticulum config and disabling the shared instance (`share_instance: no`) or pointing `shared_path` to a writable directory inside Termux (e.g., `/data/data/com.termux/files/home/.reticulum/reticulum.sock`), and ensuring each `TCPServer`/`TCPClient` interface uses a free port.

- **Shared instance already running but unreachable**  
  If you intentionally run `rnsd` in the background, keep it active and start rBrowser in the same session without killing it. Otherwise, stop the daemon before running rBrowser so it can bring up its own embedded Reticulum node.


-----


## 🚀 Usage

### 🔗 URL Formats Supported

- `hash:/page/index.mu` - Direct hash with page path
- `nomadnetwork://hash/page/index.mu` - Full protocol URL
- `hash` - Hash only (defaults to `/page/index.mu`)
- `:page/index.mu`field`content` - Pages with input field in URL

### 🧭 Navigation

- 📍 **Address Bar**: Enter NomadNet URLs manually
- ⬅️➡️ **Back/Forward**: Navigate through browsing history
- 🔄 **Refresh**: Reload the current page
- 📋 **Node Sidebar**: Click any discovered node to browse
- 🖱️ **Link Clicking**: Click links within Micron content to navigate
- ⭐ **Add Favorites**: Save your favorite nodes and recall them later
- 🔍 **Search Page or Content**: Use the included NomadNet Search Engine to discover content
- 🔐 **Identify to remote nodes**: Send fingerprint to identify to remote nodes (send identity and LXMF address)

### 👁️ Pages View Mode:

- **Rendered View**: Displays Micron markup with proper formatting
- **Raw View**: Shows the original Micron source code

## ✅ Currently Implemented

- 🌐 **Reticulum Network Integration**: Full connection to Reticulum mesh network
- 📡 **NomadNet Node Discovery**: Real-time announce monitoring with:
  - Left sidebar for node listing with Node Name, Hash Address and Announce info
  - Automatic Node listing on received announces, sorting nodes with dropdown choices
  - Detailed node announce and extended node information button
  - Add Nodes to favorites directly from the List with the star button
  - Nodes sorting by announce time, most recent announce, most announced and alphabetical order
- 📄 **Page Fetching**: Request and receive pages from remote nodes
- 📝 **Micron Rendering**: Parse and display Micron markup language
- 🖥️ **Web Interface**: Complete browser-style interface with navigation
- 🧭 **URL Navigation**: Address bar with manual URL input support
- ⬅️➡️ **Navigation History**: Back/forward button functionality
- 🔗 **Link Detection**: Automatic detection of NomadNet URLs in content
- ⏱️  Timed pages Auto-reload function with form data persistence, per each single page
- 🖱️ **Click Navigation**: Navigate by clicking links in rendered content 
- 🔔 **Notification System**: Modern info box notifications when info are needed
- 🔀 **Multiple URL Formats**: Enhanced parsing for various NomadNet URL conventions
- 🏷️ **Page Title Extraction**: Parse and display proper page titles in all UI info text
- 🗺️ **Navigation Breadcrumbs**: Show current node name and url location path
- 👁️ **Link Preview**: Hover tooltips showing destination URLs
- 🔄 **Dual View Modes**: Toggle between rendered and raw text views
- ⚠️ **Error Handling**: Robust error handling for network issues and timeouts
- 💾 **Complete Local Usage**: incorporated scripts, css and js without external call to any CDN's
- ⭐ **Bookmark System**: Save frequently visited nodes and pages (Favorites Nodes Bar)
- 📑 **MultiTab Navigation**: Open multiple links in new browser tabs
- ⌨️ **Navigation Shortcuts**: Keyboards shortcuts for tab navigation / new / close / reload page
- 🌐 **Web UI**: Implemented waitress production ready web servers, fallback to flask if missing.
- 📥 **File Download**: Support download for files hosted on nomadnet nodes with progress notification!
- 📝 **User inputs support**: Form, URL, and input boxes sending user input are supported.
- 🔐 **Fingerprint**: Send identity and lxmf address to the host node
- 📊**Network Diagnostics**: 
  - 📡 Ping functionality to test remote node reachability and measure round-trip time
  - 🗺️ Hop count display showing network distance to destination nodes
  - ℹ️ Detailed node information including announce data and last seen timestamps
  - 🔗 Reticulum connection status bar
- 🔍 **NomadNet Search Engine**: Local NomadNet Nodes Exclusive Search Engine!
  - Cache index.mu pages locally, enabled by default, edit your preferences in the settings.
  - Search by node names or keywords inside cached pages
  - Double Search Mode: "All Results (includes partial matches)" and "Exact Words Only"  
  - Search Engine Statistic in the bottom bar with settings information
  - Page cache management, search result highlight, dynamic cache refresh with real-time status updates
  - Ping functionality in search results to check if node is available
- 📱 **Optimized UI**: Auto-adapt UI for small screen devices like mobiles and tablets
- 📄 **Text/ASCII ART Page Mode**: 
  - ℹ️ Intelligent algorithm for TEXT or ASCII ART pages detection, with automatic rendering optimization
- 🐳 **Docker Version**: Dependencies-free installation on docker


## 🧩 Next Implementations:
### The following features are planned for the next versions:

* Prebuilt executables for Windows/Linux/macOS
* Enhance error handling and metrics, improve terminal logs
* Improve mobile UI on small screens
* Improve overall performance
* Implement Dark / Light Themes
* Enhanced browser settings (log on terminal or file, disable logs, start script with arguments etc.)

-----


## ⚠️ Known Issues:

- None 🤷 😊

-----

## 🐛 Bug or issues report:

- If you find bugs or any other issue, feel free to contact the developer on Reticulum at:

```
- LXMF Address: 0d051f3b6f844380c3e0c5d14e37fac8
```

or directly open a github issue here!


-----

## 💡 Development Notes

- The browser creates an identity file (`nomadnet_browser_identity`) on first run
- Reticulum configuration is stored in the default location (`~/.reticulum/`)
- The application runs as a single-page application with AJAX content loading
- Fallback Micron parser is included if the original parser fails to load
- Detailed logs are printed by the python script in the terminal
- If Search Engine is enabled (ON by default), Nomadnet pages will be chached locally in /cache/nodes folder


-----

## 🛠 Troubleshooting

**No nodes appearing:**
- Verify Reticulum network connectivity and configuration!
- Check that NomadNetwork nodes are active on your network
- Ensure firewall allows Reticulum traffic

**Page loading failures:**
- Confirm the target node is online and reachable
- Check network connectivity to the Reticulum network
- Verify the page path exists on the target node

**Micron rendering issues:**
- Ensure `micron-parser_original.js` is in the `script/` directory
- Check browser console for JavaScript errors
- Try toggling to Raw View to see source content

**In case of disconnections from network**
- Chech the bottom left status bar for connection info and status
- If disconnected, verify that the python script is running
- Verify your RNS config carefully before running the script
- Check critical logs in terminal, logs are shown from the Reticulum instance log into the script terminal.

**Common Errors:**

- Failed to initialize: Attempt to reinitialise Reticulum when it was already running: make sure to close other running reticulum process or instances
- Reticulum error logs in terminal: check your Reticulum settings and interfaces configuration in /youruser/.reticulum/config file. 

-----

## ⚠️ Traffic Usage Warning:

The included Search Engine generates network traffic when enabled, by requesting remote pages. It requests by default only the index.mu page but you can try to fetch more pages with "Cache additional pages" in the Search Engine settings. 

**IF YOU ARE USING LORA INTERFACE, DISABLE THE SEARCH ENGINE** (TO AVOID CONSUMING ALL YOUR AIRTIME AND GENERATING UNWANTED NETWORK TRAFFIC!)

-----
## 📜 License

This project is open source. Use it and share freely. Please mention the official project link.

Please refer to the LICENSE file for details.

-----

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

-----

## 📦 External dependencies:

This project includes local available versions of:

- micronparser.js for NomadNet pages rendering 
- DOMPurify.min.js for html security
- fingerptint, go, ping, search and star icons from: flaticon.com

The Web UI is served by:

- Flask (developer web server, default in case waitress is missing)
- Waitress (Cross-platfrom, multithreaded, production web server)


External software and all their rights are owned by the respective developers. 

-----

## 🖼 Screenshots:

### Main Interface:
<img width="1920" height="1080" alt="-1 main interface" src="https://github.com/user-attachments/assets/fcca646f-a565-4579-8bf2-b22ee2dafe28" />


### Example of link navigation with input field requests:
<img width="1920" height="1080" alt="2" src="https://github.com/user-attachments/assets/4e2e4128-0b06-4363-aeff-32cd428dabc5" />


### Example of Extended Node Informations:
<img width="1920" height="1080" alt="3" src="https://github.com/user-attachments/assets/f2c16006-72ae-4c44-8f36-020a5eda56ab" />


### Example of the included Search Engine feature:
<img width="1920" height="1080" alt="4" src="https://github.com/user-attachments/assets/bcb49099-7d5e-45f2-b940-ebb381526085" />

<img width="1920" height="1080" alt="5" src="https://github.com/user-attachments/assets/0edc7f65-5397-4422-bd4c-c345fef76c83" />


-----

<div align="center">

# ❤️ Developed with love by Franky & neoemit ❤️

-----

### Thanks to: SudoIvan for his --host / --port arguments contribution & Casca for his excellent bug hunting skills! :)

</div>
