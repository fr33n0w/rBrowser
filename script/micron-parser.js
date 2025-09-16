/**
 * Custom Micron Parser Implementation for NomadNet
 * Based on the Micron markup specification from NomadNet
 */

function parseMicronSource(micronText) {
    if (!micronText) return '';
    
    let html = '';
    const lines = micronText.split('\n');
    let sectionLevel = 0;
    let alignment = '';
    let currentStyles = {
        bold: false,
        italic: false,
        underline: false,
        fg: '',
        bg: ''
    };
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function applyStyles(text, styles) {
        let result = text;
        let openTags = [];
        let closeTags = [];
        
        if (styles.bg) {
            openTags.push(`<span style="background-color: #${styles.bg};">`);
            closeTags.unshift('</span>');
        }
        if (styles.fg) {
            openTags.push(`<span style="color: #${styles.fg};">`);
            closeTags.unshift('</span>');
        }
        if (styles.bold) {
            openTags.push('<strong>');
            closeTags.unshift('</strong>');
        }
        if (styles.italic) {
            openTags.push('<em>');
            closeTags.unshift('</em>');
        }
        if (styles.underline) {
            openTags.push('<u>');
            closeTags.unshift('</u>');
        }
        
        return openTags.join('') + result + closeTags.join('');
    }
    
    function processLine(line) {
        // Skip comments
        if (line.trim().startsWith('#')) {
            return '';
        }
        
        // Handle literal blocks
        if (line.trim() === '`=') {
            return '<pre class="literal-block">';
        }
        if (line.trim() === '=`') {
            return '</pre>';
        }
        
        // Handle sections
        const sectionMatch = line.match(/^(>+)(.*)$/);
        if (sectionMatch) {
            const level = sectionMatch[1].length;
            const heading = sectionMatch[2].trim();
            
            let result = '';
            // Close previous sections if needed
            while (sectionLevel >= level) {
                result += '</div>';
                sectionLevel--;
            }
            
            // Open new section
            result += `<div class="section section-${level}">`;
            if (heading) {
                result += `<h${Math.min(level + 1, 6)} class="section-heading">${escapeHtml(heading)}</h${Math.min(level + 1, 6)}>`;
            }
            sectionLevel = level;
            return result;
        }
        
        // Handle alignment tags at start of line
        if (line.startsWith('`c')) {
            alignment = 'center';
            line = line.substring(2);
        } else if (line.startsWith('`l')) {
            alignment = 'left';
            line = line.substring(2);
        } else if (line.startsWith('`r')) {
            alignment = 'right';
            line = line.substring(2);
        } else if (line.startsWith('`a')) {
            alignment = '';
            line = line.substring(2);
        }
        
        // Handle dividers
        if (line.trim() === '-' || line.trim().startsWith('-∿') || line.trim() === '<') {
            return '<hr class="divider">';
        }
        
        // Process inline formatting
        let processedLine = line;
        
        // Handle color and formatting tags
        processedLine = processedLine.replace(/`F([0-9a-fA-F]{3})/g, (match, color) => {
            currentStyles.fg = color;
            return `<span style="color: #${color};">`;
        });
        
        processedLine = processedLine.replace(/`B([0-9a-fA-F]{3})/g, (match, color) => {
            currentStyles.bg = color;
            return `<span style="background-color: #${color};">`;
        });
        
        processedLine = processedLine.replace(/`f/g, () => {
            currentStyles.fg = '';
            return '</span>';
        });
        
        processedLine = processedLine.replace(/`b/g, () => {
            currentStyles.bg = '';
            return '</span>';
        });
        
        // Handle formatting tags
        processedLine = processedLine.replace(/`!/g, '<strong>');
        processedLine = processedLine.replace(/!/g, '</strong>');
        processedLine = processedLine.replace(/`\*/g, '<em>');
        processedLine = processedLine.replace(/\*/g, '</em>');
        processedLine = processedLine.replace(/`_/g, '<u>');
        processedLine = processedLine.replace(/_/g, '</u>');
        
        // Handle reset tag
        processedLine = processedLine.replace(/``/g, '</span></span></span></strong></em></u>');
        
        // Handle links
        processedLine = processedLine.replace(/`\[([^\]]*)`([^\]]+)\]/g, (match, label, url) => {
            return `<a href="#" class="micron-link" data-url="${escapeHtml(url)}">${label || url}</a>`;
        });
        
        processedLine = processedLine.replace(/`\[([^\]]+)\]/g, (match, url) => {
            return `<a href="#" class="micron-link" data-url="${escapeHtml(url)}">${url}</a>`;
        });
        
        // Handle input fields
        processedLine = processedLine.replace /<([^>]+)`([^>]*)>/g, (match, name, value) => {
            const escaped_name = escapeHtml(name);
            const escaped_value = escapeHtml(value);
            return `<input type="text" name="${escaped_name}" value="${escaped_value}" class="micron-input" />`;
        });
        
        // Apply alignment
        if (alignment) {
            processedLine = `<div style="text-align: ${alignment};">${processedLine}</div>`;
        } else if (processedLine.trim()) {
            processedLine = `<div>${processedLine}</div>`;
        }
        
        return processedLine;
    }
    
    // Process each line
    for (let i = 0; i < lines.length; i++) {
        const processedLine = processLine(lines[i]);
        if (processedLine) {
            html += processedLine + '\n';
        }
    }
    
    // Close any remaining sections
    while (sectionLevel > 0) {
        html += '</div>';
        sectionLevel--;
    }
    
    return html;
}

// Also expose it as a global function for compatibility
window.parseMicronSource = parseMicronSource;
window.parseMicron = parseMicronSource;  // Alternative name
window.MicronParser = parseMicronSource; // Another alternative

console.log('Custom Micron parser loaded successfully!');