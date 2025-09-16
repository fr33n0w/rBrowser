# rBrowser v1.0
<img width="1920" height="996" alt="v1screenshot" src="https://github.com/user-attachments/assets/d7f14680-0dbe-4c9f-b326-802ffd8946ce" />

-----

# rBrowser: Reticulum Standalone NomadNet Browser

A standalone web-based browser for exploring NomadNetwork nodes and pages over the Reticulum mesh network. This browser automatically discovers NomadNet nodes through network announces and provides a user-friendly interface for browsing distributed content with Micron markup support.

Script and Web UI Preview Coming Soon on rmap.world

## Features

- **Real-time Node Discovery**: Automatically detects and lists NomadNetwork nodes as they announce on the network
- **Web-based Interface**: Modern, responsive browser interface accessible at `localhost:5000`
- **Micron Parser**: Renders NomadNet's Micron markup language with proper formatting and styling
- **URL Navigation**: Address bar with back/forward navigation and manual URL input
- **Dual View Modes**: Toggle between rendered Micron content and raw text view
- **Link Navigation**: Click on links within Micron content to navigate between pages (COMING SOON!)
- **Connection Status**: Real-time display of network status and discovered pages / announced nodes

## Requirements

### System Requirements
- **Python**: 3.7 or higher
- **Operating System**: Linux, macOS, or Windows
- **Network**: Access to a Reticulum network (radio interfaces, internet gateways, or local testnet)

### Python Dependencies
- `flask` >= 2.0.0 - Web framework for the browser interface
- `reticulum` >= rns 1.0.0 - Mesh networking library for NomadNetwork protocol

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

5. **Verify file structure:**
   ```
   nomadnet-browser/
   ├── nomadnet_browser.py
   ├── templates/
   │   └── index.html
   └── script/
       └── micron-parser_original.js
   ```

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
   - Click on any node to browse its content

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
- **Link Clicking**: Click links within Micron content to navigate (Coming Soon!)

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
- ✖️ **Click Navigation**: Navigate by clicking links in rendered content
- ✅ **Dual View Modes**: Toggle between rendered and raw text views
- ✅ **Error Handling**: Robust error handling for network issues and timeouts

## Next Implementation: Enhanced Link Navigation

The following features are planned for the next version:

### 1. Improved Link Parser
- **Relative Path Resolution**: Support for relative links like `../index.mu` or `posts/latest.mu`
- **Multiple URL Formats**: Enhanced parsing for various NomadNet URL conventions
- **Link Validation**: Verify link format before navigation attempts

### 2. Enhanced Navigation Features
- **Link Preview**: Hover tooltips showing destination URLs
- **New Tab/Window**: Option to open links in new browser tabs
- **Bookmark System**: Save frequently visited nodes and pages
- **Navigation Breadcrumbs**: Show current location path

### 3. Advanced Micron Support
- **Table Support**: Proper rendering of Micron table markup
- **Advanced Formatting**: Support for more complex Micron elements

### 4. User Experience Improvements
- **Loading Indicators**: Progress bars for page loading
- **Cache System**: Local caching of frequently accessed pages
- **Search Functionality**: Search within page content and across nodes
- **Page Title Extraction**: Parse and display proper page titles

## Development Notes

- The browser creates an identity file (`nomadnet_browser_identity`) on first run
- Reticulum configuration is stored in the default location (`~/.reticulum/`)
- The application runs as a single-page application with AJAX content loading
- Fallback Micron parser is included if the original parser fails to load

## Troubleshooting

**No nodes appearing:**
- Verify Reticulum network connectivity
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
