# rBrowser v1.0 - Standalone Nomadnet Browser

-----


<img width="1920" height="1080" alt="lastv1" src="https://github.com/user-attachments/assets/3f753eed-49c5-4d89-820b-e1dc1a8cb383" />


---

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Reticulum](https://img.shields.io/badge/Reticulum-supported-yellow.svg)](https://github.com/markqvist/Reticulum)
[![Developer: Frank](https://img.shields.io/badge/Dev:-Frank-blue.svg)](https://github.com/fr33n0w)
[![Developer: Thomas](https://img.shields.io/badge/Dev:-Thomas-blue.svg)](https://github.com/neoemit)
---

# rBrowser: Standalone NomadNet Browser

A standalone web-based UI browser for exploring NomadNetwork Nodes and Pages over Reticulum Network. 

This browser automatically discovers NomadNet nodes through network announces and provides a user-friendly interface for browsing distributed content with Micron markup support.

It includes some exclusive features like: Automatic listening for announce, Add nodes to favorites, browse and render any kind of NomadNet links, download files from remote nodes, unique local NomadNet Search Engine and more...

-----

## Some Features:

- **Real-time Node Discovery**: Detects and lists NomadNetwork nodes as they announce on the network
- **Web-based Interface**: Modern, responsive browser interface accessible at `localhost:5000`
- **Micron Parser**: Renders NomadNet's Micron markup language with proper formatting and styling
- **URL Navigation**: Address bar with back/forward navigation and manual URL input
- **Dual View Modes**: Toggle between Rendered Micron content and Raw page view
- **Link Navigation**: Click on links within Micron content to navigate between pages
- **Connection Status**: Real-time display of network status and discovered pages / announced nodes
- **File download support**: Download files hosted on nomadnet nodes
- **NomadNet Search Endinge**: Unique search engine system to search in local auto-cached pages if enabled
- **Add To Favorites**: Favorite system with star button synched across the whole UI tabs
- **Node Info**: Extended node info for remote node hosting page in the node list
- **Fingerprint**: Allow to identify with identity and LXMF address to remote host with a button
- **Notifications & Logs**: Comprehensive Notifications info box in the web ui + full operational log in the terminal 
- **And more......**: Download rBrowser and try it now!!

## Requirements

### System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Linux, macOS, or Windows
- **Network**: Access to a Reticulum network (radio interfaces, internet gateways, or local testnet)

### Python Dependencies (included in requirements.txt)

- `reticulum` >= rns 1.0.0 - Reticulum networking protocol stack for connection and NomadNetwork retrival
- `flask` >= 2.0.0 - Base Web framework for the browser UI interface
- `waitress` >=2.1.2 - Web Server Framework


-----

## Installation

### PREREQUISITES:

**Configure Reticulum:**
   
- Before launching the script or the Docker image, you need a full configured and working instance of Reticulum, 
- At least one TCPClientInterface in your ./reticulum/config file to access NomadNetwork 

NOTE: You don't need to run RNS manually, just make sure your instance is working and can connect to Reticulum Network!


## Install Option 1: Run from terminal

1. **Clone the repository:**

   ```bash
   git clone https://github.com/fr33n0w/rBrowser.git
   cd rBrowser
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start rBbrowser:**
   ```bash
   python3 rBrowser.py
   ```

4. **Open your web browser and navigate to:**
   ```
   http://localhost:5000
   ```

5. **Wait for node discovery:**

   - The browser will start listening for NomadNetwork announces
   - Discovered nodes will appear in the left sidebar
   - Click on any node to browse its content and navigate pages
   - or manually paste address in the bar without waiting for announces
   - Check bottom-left Status Bar for connection status info 


---

## Install Option 2: Docker & Docker Compose

- This repository includes a Dockerfile and a docker-compose.yaml so you can run rBrowser in a container. 
- The compose setup builds the image and exposes the web UI on port 5000.

## Docker Setup Guide

### Prerequisites

#### 1. Install Docker and Docker Compose

Check if already installed:
```bash
docker --version
docker-compose --version


If not installed on Debian/Ubuntu:

# Install Docker
sudo apt-get update
sudo apt-get install docker.io

# Install Docker Compose (standalone)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

```


Quick start with Docker installed:
```bash

Configure Docker User Permissions:

# add current user to docker group (if not already present):
sudo usermod -aG docker $USER 
Important: Log out and log back in for the group change to take effect.

# clone repo:
git clone https://github.com/fr33n0w/rBrowser

# enter root repo directory:
cd rBrowser

# build and start in background
docker compose up -d

# follow logs
docker compose logs -f rbrowser


Useful Commands:

# rebuild image and restart
docker compose build --no-cache rbrowser
docker compose up -d

# Stop the container:
docker compose down

# View running containers:
docker ps

```

Notes:
- The Dockerfile copies a repository `config` file into the container at /home/appuser/.reticulum/config. Ensure you have a valid Reticulum config file named `config` in the repo root before building, or mount your config at runtime:
  - Example volume override in docker-compose.yaml:
    volumes:
      - ./config:/home/appuser/.reticulum/config:ro
- Use `docker compose ps` to check service and healthcheck status (compose file includes a basic HTTP healthcheck).
- Stop and remove containers with:
```bash
docker compose down
```

## At the end, open the rBrowser UI at: http://localhost:5000


-----


## Usage

### URL Formats Supported

- `hash:/page/index.mu` - Direct hash with page path
- `nomadnetwork://hash/page/index.mu` - Full protocol URL
- `hash` - Hash only (defaults to `/page/index.mu`)
- `:page/index.mu`field`content` - Pages with input field in URL

### Navigation

- **Address Bar**: Enter NomadNet URLs manually
- **Back/Forward**: Navigate through browsing history
- **Refresh**: Reload the current page
- **Node Sidebar**: Click any discovered node to browse
- **Link Clicking**: Click links within Micron content to navigate
- **Add Favorites**: Save your favorite nodes and recall them later
- **Search Page or Content**: Use the included NomadNet Search Engine to discover content
- **Identify to remote nodes**: Send fingerprint to identify to remote nodes (send identity and LXMF address)

### Pages View Mode:

- **Rendered View**: Displays Micron markup with proper formatting
- **Raw View**: Shows the original Micron source code


## Currently Implemented

- ✅ **Reticulum Network Integration**: Full connection to Reticulum mesh network
- ✅ **NomadNet Node Discovery**: Real-time announce monitoring and node listing
- ✅ **Page Fetching**: Request and receive pages from remote nodes
- ✅ **Micron Rendering**: Parse and display Micron markup language
- ✅ **Web Interface**: Complete browser-style interface with navigation
- ✅ **URL Navigation**: Address bar with manual URL input support
- ✅ **Navigation History**: Back/forward button functionality
- ✅ **Link Detection**: Automatic detection of NomadNet URLs in content
- ✅ **Click Navigation**: Navigate by clicking links in rendered content 
- ✅ **Notification System**: Modern info box notifications when info are needed
- ✅ **Multiple URL Formats**: Enhanced parsing for various NomadNet URL conventions
- ✅ **Page Title Extraction**: Parse and display proper page titles in all UI info text
- ✅ **Navigation Breadcrumbs**: Show current node name and url location path
- ✅ **Link Preview**: Hover tooltips showing destination URLs
- ✅ **Dual View Modes**: Toggle between rendered and raw text views
- ✅ **Error Handling**: Robust error handling for network issues and timeouts
- ✅ **Complete Local Usage**: incorporated scripts, css and js without external call to any CDN's
- ✅ **Bookmark System**: Save frequently visited nodes and pages (Favorites Nodes Bar)
- ✅ **MultiTab Navigation**: Open multiple links in new browser tabs
- ✅ **Navigation Shortcuts**: Keyboards shortcuts for tab navigation / new / close / reload page
- ✅ **Web UI**: Implemented waitress production ready web servers, fallback to flask if missing.
- ✅ **File Download**: Support download for files hosted on nomadnet nodes with progress notification!
- ✅ **User inputs support**: Form, URL, and input boxes sending user input are supported.
- ✅ **Fingerprint**: Send identity and lxmf address to the host node
- ✅ **NomadNet Search Engine** : Local NomadNet Nodes page-caching Search Engine
- ✅ **Optimized UI** : Auto-adapt UI for small screen devices like mobiles and tablets
- ✅ **Docker Version**: Dependencies-free installation on docker


## Next Implementations:
### The following features are planned for the next versions:

- Windows , Linux and MacOs Executable App, probably.


-----


## Known Issues:

- Sometimes Input box parameter sending is failing on nodes with non-standard nomadnet micron link format, due to unique fields customization  (BTW >95% of pages are perfectly working!)

-----

## Bug or issues report:

- If you find bugs or any other issue, feel free to contact the developer on Reticulum at: LXMF Address: 0d051f3b6f844380c3e0c5d14e37fac8 or open a github issue

-----

## Development Notes

- The browser creates an identity file (`nomadnet_browser_identity`) on first run
- Reticulum configuration is stored in the default location (`~/.reticulum/`)
- The application runs as a single-page application with AJAX content loading
- Fallback Micron parser is included if the original parser fails to load
- Detailed logs are printed by the python script in the terminal
- If Search Engine is enabled (ON by default), Nomadnet pages will be chached locally in /cache/nodes folder


-----

## Troubleshooting

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

## Traffic Usage Warning:

The included Search Engine generates network traffic when enabled, by requesting remote pages. It requests by default only the index.mu page but you can try to fetch more pages with "Cache additional pages" in the Search Engine settings. 

**IF YOU ARE USING LORA INTERFACE, DISABLE THE SEARCH ENGINE** (TO AVOID CONSUMING ALL YOUR AIRTIME AND GENERATING UNWANTED NETWORK TRAFFIC!)

-----
## License

This project is open source. Use it and share freely. Please mention the official project link.

Please refer to the LICENSE file for details.

-----

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

-----

## External dependencies:

This project includes local available versions of:

- micronparser.js for NomadNet pages rendering 
- DOMPurify.min.js for html security
- fingerptint, go and star icons from flaticon.com

The Web UI is served by:

- Flask (developer web server, default in case waitress is missing)
- Waitress (Production web server for windows / linux)


External software and all their rights are owned by the respective developers. 

-----

# rBrowser v1.0

##Screenshots:

### Example of link navigation with input field requests:
<img width="1920" height="1080" alt="lastv1_2" src="https://github.com/user-attachments/assets/9c5c4335-2ad9-4367-9c2f-2fcd5cc6693d" />

### Example of Extended Node Informations:
<img width="1920" height="1080" alt="lastv1_3" src="https://github.com/user-attachments/assets/5ede3dd3-9e39-433d-ac6d-19b87549ee3f" />

### Example of the included Search Engine feature:
<img width="1920" height="1080" alt="lastv1_4" src="https://github.com/user-attachments/assets/c1636e8f-860b-4e0a-867f-568eacd186d7" />
<img width="1920" height="1080" alt="search" src="https://github.com/user-attachments/assets/f00b815a-ce6e-4831-aa53-b64ce3a36c73" />

-----

# ❤️ Developed with love by Franky & Thomas ❤️
