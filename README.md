# rBrowser v1.0 - Standalone Nomadnet Browser

-----

<img width="1920" height="1080" alt="screen3" src="https://github.com/user-attachments/assets/104c5923-c22d-4622-b932-8b583afd4fbd" />


-----

# rBrowser: Standalone NomadNet Browser

A standalone web-based UI browser for exploring NomadNetwork Nodes and Pages over Reticulum Network. 

This browser automatically discovers NomadNet nodes through network announces and provides a user-friendly interface for browsing distributed content with Micron markup support.

-----

## Some Features:

- **Real-time Node Discovery**: Automatically detects and lists NomadNetwork nodes as they announce on the network
- **Web-based Interface**: Modern, responsive browser interface accessible at `localhost:5000`
- **Micron Parser**: Renders NomadNet's Micron markup language with proper formatting and styling
- **URL Navigation**: Address bar with back/forward navigation and manual URL input
- **Dual View Modes**: Toggle between rendered Micron content and raw text view (top-right Rendered / Raw button)
- **Link Navigation**: Click on links within Micron content to navigate between pages
- **Connection Status**: Real-time display of network status and discovered pages / announced nodes
- **File download support**: Download files hosted on nomadnet nodes

## Requirements

### System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Linux, macOS, or Windows
- **Network**: Access to a Reticulum network (radio interfaces, internet gateways, or local testnet)

### Python Dependencies

- `reticulum` >= rns 1.0.0 - Reticulum networking protocol stack for connection and NomadNetwork retrival
- `flask` >= 2.0.0 - Base Web framework for the browser UI interface
- `waitress` - Web Server Framework for windows os
- `gunicorn` - Web Server Framework for Linux


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
   
   Before launching the script you need a full working instance of Reticulum, so you need to configure at least one TCPClientInterface in your ./reticulum/config file. 

   You don't need to run rns manually, just make sure your instance is working and can connect to Reticulum Network!

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
   - Manually paste address in the bar without waiting for announces

## Usage

### URL Formats Supported

- `hash:/page/index.mu` - Direct hash with page path
- `nomadnetwork://hash/page/index.mu` - Full protocol URL
- `hash` - Hash only (defaults to `/page/index.mu`)
- `:page/index.mu`field`content` - Pages with input field in URL (some unique customized urls can not always work)

### Navigation

- **Address Bar**: Enter NomadNet URLs manually
- **Back/Forward**: Navigate through browsing history
- **Refresh**: Reload the current page
- **Node Sidebar**: Click any discovered node to browse
- **Link Clicking**: Click links within Micron content to navigate
- **Add Favorites**: Save your favorite nodes and recall them later

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
- ✅ **Web UI**: Implemented waitress and gunicorn production ready web servers, fallback to flask if missing.
- ✅ **File Download**: Support download for files hosted on nomadnet nodes with progress notification!
- ✅ **User inputs support**: Form, URL, and input boxes sending user input are supported.
- ✅ **Fingerprint**: Send identity and lxmf address to the host node
- ✅ **NomadNet Search Engine** : Automatic caching on first announce for index.mu if enabled for a local search engine.

## Next Implementations:
### The following features are planned for the next versions:

- Docker Version, Windows Executable version, Linux Executable Appimage 


## Known Issues:

- Input box parameter sending is failing on some nodes with non-standard nomadnet micron format. due to the user fields customization  (95% of the nodes are perfectly working!)

If you find bugs, feel free to contact the developer on Reticulum at: LXMF Address: 0d051f3b6f844380c3e0c5d14e37fac8

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

This project includes local available versions of:

- micronparser.js for NomadNet pages rendering 
- DOMPurify.min.js for html security

The Web UI is served by:

- Flask (developer web server, default if others are missing)
- waitress (Production web server for windows)
- gunicorn (Production web server for linux) 


External software and all their rights are owned by the respective developers. 

-----

# rBrowser v1.0

## Developed with love by Franky & Thomas 
