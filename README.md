# rBrowser v1.0

-----

<img width="1920" height="1080" alt="screen3" src="https://github.com/user-attachments/assets/104c5923-c22d-4622-b932-8b583afd4fbd" />


-----

# rBrowser: Reticulum Standalone NomadNet Browser

A standalone web-based UI browser for exploring NomadNetwork Nodes and Pages over Reticulum Network. 

This browser automatically discovers NomadNet nodes through network announces and provides a user-friendly interface for browsing distributed content with Micron markup support.

-----

## Features

- **Real-time Node Discovery**: Automatically detects and lists NomadNetwork nodes as they announce on the network
- **Web-based Interface**: Modern, responsive browser interface accessible at `localhost:5000`
- **Micron Parser**: Renders NomadNet's Micron markup language with proper formatting and styling
- **URL Navigation**: Address bar with back/forward navigation and manual URL input
- **Dual View Modes**: Toggle between rendered Micron content and raw text view (top-right Rendered / Raw button)
- **Link Navigation**: Click on links within Micron content to navigate between pages
- **Connection Status**: Real-time display of network status and discovered pages / announced nodes

## Requirements

### System Requirements
- **Python**: 3.7 or higher
- **Operating System**: Linux, macOS, or Windows
- **Network**: Access to a Reticulum network (radio interfaces, internet gateways, or local testnet)

### Python Dependencies
- `flask` >= 2.0.0 - Web framework for the browser UI interface
- `reticulum` >= rns 1.0.0 - Reticulum networking protocol stack for connection and NomadNetwork retrival

-----

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/fr33n0w/rBrowser.git
   cd rBrowser
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Reticulum:**
   
   Before launching the script you need a full working instance of Reticulum, so you need to configure at least a TCPClientInterface in your ./reticulum/config file. Don't need to run rns manually, just make sure your instance is working and can connect to Reticulum Network!

-----

## Running the Browser

1. **Start the browser:**
   ```bash
   python3 rBrowser.py
   ```

2. **Open your web browser and navigate to:**
   ```
   http://localhost:5000
   ```

3. **Wait for node discovery:**
   - The browser will start listening for NomadNetwork announces
   - Discovered nodes will appear in the left sidebar
   - Click on any node to browse its content and navigate pages

## Usage

### URL Formats Supported
- `hash:/page/index.mu` - Direct hash with page path
- `nomadnetwork://hash/page/index.mu` - Full protocol URL
- `hash` - Hash only (defaults to `/page/index.mu`)

### Navigation
- **Address Bar**: Enter NomadNet URLs manually
- **Back/Forward**: Navigate through browsing history
- **Refresh**: Reload the current page
- **Node Sidebar**: Click any discovered node to browse
- **Link Clicking**: Click links within Micron content to navigate

### View Modes
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

## Next Implementations:
### The following features are planned for the next version:

- ✖️ **File Download**: download files hosted on nomadnet, coming soon!
- ✖️ **Form and input boxes**: sending user input in nomad pages, work in progress!
- ✖️ **Fingerprint**: Send identity and lxmf address to the host node, coming soon!
- ✖️ **Loading Indicators**: Progress bars for page loading (optional)

-----

## Development Notes

- The browser creates an identity file (`nomadnet_browser_identity`) on first run
- Reticulum configuration is stored in the default location (`~/.reticulum/`)
- The application runs as a single-page application with AJAX content loading
- Fallback Micron parser is included if the original parser fails to load

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

## License

This project is open source. Please refer to the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## External dependencies:

This project includes micronparser.js and DOMPurify.min.js in local folders to avoid external url calls.

This software and all their rights are owned by the respective developers. 

-----

# rBrowser v1.0

# Developed with love by Franky & Thomas 
