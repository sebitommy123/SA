"""
Debug module for the SA query language.

Provides a singleton Debugger class to track execution parts and logs
in a hierarchical structure for debugging query language operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import time
from datetime import datetime
import pytz


@dataclass
class LogEntry:
    """Represents a single log entry with timestamp and class."""
    message: str
    timestamp: float
    log_class: str = "INFO"
    
    def __str__(self) -> str:
        return f"[{self.log_class}] {self.message}"

@dataclass
class Part:
    """Represents a single execution part with its logs and subparts."""
    name: str
    part_class: str = "INFO"
    logs: List[LogEntry] = field(default_factory=list)
    subparts: List[Part] = field(default_factory=list)
    parent: 'Part | None' = None
    start_time: float = 0.0
    end_time: float = 0.0
    
    @property
    def duration(self) -> float:
        """Calculate the duration of this part in seconds."""
        if self.end_time > 0 and self.start_time > 0:
            return self.end_time - self.start_time
        return 0.0


class Debugger:
    """
    Debugger for tracking query language execution.
    
    Maintains a hierarchical structure of execution parts and their logs,
    allowing for detailed debugging of query language operations.
    """
    
    def __init__(self):
        """Initialize the debugger state."""
        self.root_part: Part = Part(name="root")
        self.current_part: Part = self.root_part
    
    def start_part(self, part_class: str, part_name: str) -> None:
        """
        Start a new execution part.
        
        Args:
            part_class: Class/category of the part (e.g., "EXECUTION", "OPERATOR", "QUERY")
            part_name: Name of the part being started
        """
        new_part = Part(name=part_name, part_class=part_class, parent=self.current_part, start_time=time.time())
        self.current_part.subparts.append(new_part)
        self.current_part = new_part
    
    def end_part(self, part_name: str) -> None:
        """
        End the current execution part.
        
        Args:
            part_name: Name of the part being ended (must match current part)
            
        Raises:
            RuntimeError: If the part_name doesn't match the current part
        """
        if self.current_part.name != part_name:
            raise RuntimeError(
                f"Part mismatch: trying to end '{part_name}' but current part is "
                f"'{self.current_part.name}'. This indicates "
                "a missing end_part() call or incorrect nesting."
                f"Current part: {self.current_part.name}"
            )
        
        # Record end time
        self.current_part.end_time = time.time()
        
        # Move back to parent part
        self._move_to_parent()
    
    def _move_to_parent(self) -> None:
        """Move current_part back to its parent."""
        if self.current_part.parent is not None:
            self.current_part = self.current_part.parent
    
    def log(self, log_class: str, message: str) -> None:
        """
        Add a log message to the current part.
        
        Args:
            log_class: The class/category of the log (e.g., "INFO", "ERROR", "DEBUG")
            message: The log message to add
        """
        log_entry = LogEntry(message=message, timestamp=time.time(), log_class=log_class)
        self.current_part.logs.append(log_entry)
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Convert Unix timestamp to readable date in Chicago timezone."""
        chicago_tz = pytz.timezone('America/Chicago')
        dt = datetime.fromtimestamp(timestamp, tz=chicago_tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Remove last 3 digits for milliseconds

    def to_html(self) -> str:
        """Generate HTML representation of the debugger state."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html><head>")
        html.append("<title>SA Query Debug Output</title>")
        html.append("<meta charset='UTF-8'>")
        html.append("<style>")
        html.append("""
        body { 
            font-family: monospace; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: none;
            margin: 0;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .content {
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .part { 
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            background: #f8f9fa;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .part-header {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 4px 7px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
        }
        .part-header-left {
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
        }
        .part-header-right {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .part-content {
            padding: 9px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .log { 
            padding: 4px 7px;
            background: white;
            border-left: 4px solid #3498db;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .log-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
        }
        .log-header-left {
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
            min-width: 0;
        }
        .log-header-right {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }
        .log-content {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 8px 12px;
            font-family: monospace;
            color: #000;
            white-space: pre-wrap;
            word-break: break-word;
            font-size: 0.8em;
            display: none; /* Collapsed by default */
        }
        .log.expanded .log-content {
            display: block;
        }
        .log.expanded .log-collapse-btn::after {
            content: "▼";
        }
        .log-collapse-btn::after {
            content: "▶";
        }
        .duration { 
            color: #27ae60; 
            font-size: 0.9em; 
            font-weight: bold;
            background: #d5f4e6;
            padding: 4px 8px;
            border-radius: 4px;
            white-space: nowrap;
        }
        .timestamp { 
            color: #7f8c8d; 
            font-size: 0.8em;
            background: #ecf0f1;
            padding: 4px 8px;
            border-radius: 4px;
            white-space: nowrap;
        }
        .log-class { 
            font-weight: bold;
            padding: 2px 4px;
            border-radius: 4px;
            white-space: nowrap;
            font-size: 0.7em;
        }
        .part-class { 
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            white-space: nowrap;
            font-size: 0.9em;
        }
        /* Dynamic log class styling based on substrings */
        .log-class { background: #e8f4fd; color: #2980b9; } /* Default styling */
        
        /* Dynamic part class styling based on substrings */
        .part-class { background: #e8f4fd; color: #2980b9; } /* Default styling */
        .current-part {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 12px 16px;
            margin-top: 20px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
        }
        .icon {
            font-size: 1.2em;
        }
        .log-message {
            flex: 1;
            min-width: 0;
            word-break: break-word;
        }
        .collapse-btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8em;
            transition: all 0.2s ease;
        }
        .collapse-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .global-controls {
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
            padding: 15px 20px;
            text-align: center;
            border-bottom: 1px solid #34495e;
        }
        .global-controls button {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            margin: 0 5px;
            font-family: monospace;
            font-size: 0.9em;
            transition: all 0.2s ease;
        }
        .global-controls button:hover {
            background: rgba(255,255,255,0.3);
        }
        .part > .part-content {
            display: none !important; /* Collapsed by default - only direct children */
        }
        .part.expanded > .part-content {
            display: flex !important; /* Expanded - only direct children */
        }
        .part.expanded .collapse-btn::after {
            content: "▼";
        }
        .part:not(.expanded) .collapse-btn::after {
            content: "▶";
        }
        @media (max-width: 768px) {
            .part-header {
                flex-direction: column;
                align-items: flex-start;
            }
            .part-header-right {
                width: 100%;
                justify-content: flex-start;
            }
            .log-header {
                flex-direction: column;
                align-items: flex-start;
            }
            .log-header-right {
                width: 100%;
                justify-content: flex-start;
            }
        }
        """)
        html.append("</style>")
        html.append("</head><body>")
        html.append('<div class="container">')
        html.append('<div class="header">')
        html.append('<h1><span class="icon">🐛</span> SA Query Debug Output</h1>')
        html.append('</div>')
        html.append('<div class="global-controls">')
        html.append('<button onclick="collapseAll()">Collapse All</button>')
        html.append('<button onclick="expandAll()">Expand All</button>')
        html.append('<button onclick="collapseAllLogs()">Collapse All Logs</button>')
        html.append('<button onclick="expandAllLogs()">Expand All Logs</button>')
        html.append('</div>')
        html.append('<div class="content">')
        html.append(self._to_html_minimal(self.root_part, 0))
        html.append(f'<div class="current-part"><span class="icon">📍</span> Current part: {self.current_part.name}</div>')
        html.append('</div>')
        html.append('</div>')
        
        # Generate JavaScript data
        debug_data = self._to_js_data(self.root_part)
        html.append(f"""
        <script>
        const debugData = {debug_data};
        
        function toggleCollapse(element) {{
            const part = element.closest('.part');
            const partId = part.dataset.partId;
            
            console.log('Toggle collapse clicked, part:', part, 'expanded:', part.classList.contains('expanded'));
            
            if (part.classList.contains('expanded')) {{
                // Collapsing - just remove the expanded class
                console.log('Collapsing part');
                part.classList.remove('expanded');
            }} else {{
                // Expanding - add expanded class and load content if needed
                console.log('Expanding part');
                part.classList.add('expanded');
                if (!part.dataset.loaded) {{
                    loadPartContent(partId);
                    part.dataset.loaded = 'true';
                }}
            }}
        }}
        
        function toggleLogCollapse(element) {{
            const log = element.closest('.log');
            log.classList.toggle('expanded');
        }}
        
        function collapseAll() {{
            const parts = document.querySelectorAll('.part');
            parts.forEach(part => part.classList.remove('expanded'));
        }}
        
        function expandAll() {{
            const parts = document.querySelectorAll('.part');
            parts.forEach(part => {{
                part.classList.add('expanded');
                const partId = part.dataset.partId;
                if (!part.dataset.loaded) {{
                    loadPartContent(partId);
                    part.dataset.loaded = 'true';
                }}
            }});
        }}
        
        function collapseAllLogs() {{
            const logs = document.querySelectorAll('.log');
            logs.forEach(log => log.classList.remove('expanded'));
        }}
        
        function expandAllLogs() {{
            const logs = document.querySelectorAll('.log');
            logs.forEach(log => log.classList.add('expanded'));
        }}
        
        function loadPartContent(partId) {{
            const part = document.querySelector(`[data-part-id="${{partId}}"]`);
            if (!part) return;
            
            const partData = findPartData(debugData, partId);
            if (!partData) return;
            
            const contentDiv = part.querySelector('.part-content');
            if (!contentDiv) return;
            
            contentDiv.innerHTML = renderPartContent(partData);
        }}
        
        function findPartData(data, partId) {{
            if (data.id === partId) return data;
            for (const subpart of data.subparts || []) {{
                const found = findPartData(subpart, partId);
                if (found) return found;
            }}
            return null;
        }}
        
        function renderPartContent(partData) {{
            let html = '';
            
            // Create a list of all events (logs and subparts) with their timestamps
            const events = [];
            
            // Add logs
            for (const log of partData.logs || []) {{
                events.push({{timestamp: log.timestamp, type: 'log', data: log}});
            }}
            
            // Add subparts
            for (const subpart of partData.subparts || []) {{
                events.push({{timestamp: subpart.start_time, type: 'part', data: subpart}});
            }}
            
            // Sort by timestamp
            events.sort((a, b) => a.timestamp - b.timestamp);
            
            // Generate HTML for events in chronological order
            for (const event of events) {{
                if (event.type === 'log') {{
                    html += renderLog(event.data);
                }} else if (event.type === 'part') {{
                    html += renderPartMinimal(event.data);
                }}
            }}
            
            return html;
        }}
        
        function renderLog(logData) {{
            const logTimestamp = formatTimestamp(logData.timestamp);
            const logIcon = getLogIcon(logData.log_class);
            
            return `
                <div class="log">
                    <div class="log-header">
                        <div class="log-header-left">
                            <span class="icon">${{logIcon}}</span>
                            <span class="log-class ${{logData.log_class}}">[${{logData.log_class}}]</span>
                        </div>
                        <div class="log-header-right">
                            <span class="timestamp">${{logTimestamp}}</span>
                            <button class="log-collapse-btn" onclick="toggleLogCollapse(this)"></button>
                        </div>
                    </div>
                    <div class="log-content">${{escapeHtml(logData.message)}}</div>
                </div>
            `;
        }}
        
        function renderPartMinimal(partData) {{
            const icon = getPartIcon(partData.part_class);
            const durationStr = formatDuration(partData.duration);
            const timestampStr = formatTimestamp(partData.start_time);
            
            return `
                <div class="part" data-part-id="${{partData.id}}">
                    <div class="part-header">
                        <div class="part-header-left">
                            <span class="icon">${{icon}}</span>
                            <span class="part-class ${{partData.part_class}}">[${{partData.part_class}}]</span>
                            <span>${{partData.name}}</span>
                        </div>
                        <div class="part-header-right">
                            ${{durationStr ? `<span class="duration">${{durationStr}}</span>` : ''}}
                            ${{timestampStr ? `<span class="timestamp">${{timestampStr}}</span>` : ''}}
                            <button class="collapse-btn" onclick="toggleCollapse(this)"></button>
                        </div>
                    </div>
                    <div class="part-content"></div>
                </div>
            `;
        }}
        
        function getLogIcon(logClass) {{
            if (logClass.includes('SUCCESS')) return '✅';
            if (logClass.includes('FAILED') || logClass.includes('ERROR')) return '❌';
            if (logClass.includes('DOWNLOAD')) return '⬇️';
            if (logClass.includes('OPERATOR')) return '⚙️';
            if (logClass.includes('INFO')) return 'ℹ️';
            return '📝';
        }}
        
        function getPartIcon(partClass) {{
            if (partClass.includes('EXECUTION')) return '🚀';
            if (partClass.includes('GET_BY_ID')) return '🔍';
            if (partClass.includes('FILTER')) return '🔧';
            if (partClass.includes('EQUALS')) return '⚖️';
            if (partClass.includes('COUNT')) return '🔢';
            if (partClass.includes('QUERY')) return '🔍';
            if (partClass.includes('OPERATOR')) return '⚙️';
            if (partClass.includes('SCOPE')) return '🌐';
            if (partClass.includes('DOWNLOAD')) return '⬇️';
            if (partClass.includes('PARSE')) return '📝';
            if (partClass.includes('RENDER')) return '🎨';
            return '⚙️';
        }}
        
        function formatDuration(duration) {{
            if (!duration || duration <= 0) return '';
            if (duration < 0.001) return `${{(duration * 1000).toFixed(3)}}ms`;
            if (duration < 1) return `${{(duration * 1000).toFixed(1)}}ms`;
            return `${{duration.toFixed(3)}}s`;
        }}
        
        function formatTimestamp(timestamp) {{
            if (!timestamp || timestamp <= 0) return '';
            const date = new Date(timestamp * 1000);
            return date.toLocaleString('en-US', {{timeZone: 'America/Chicago'}}) + '.' + 
                   Math.floor((timestamp % 1) * 1000).toString().padStart(3, '0');
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        </script>
        """)
        html.append("</body></html>")
        return "\n".join(html)
    
    def _to_html_recursive(self, part: Part, indent_level: int) -> str:
        """
        Recursively generate HTML for parts and their logs.
        
        Args:
            part: Part to convert to HTML
            indent_level: Current indentation level
            
        Returns:
            HTML string for this part and its children
        """
        html = []
        
        # Format duration for display
        duration_str = ""
        if part.duration > 0:
            if part.duration < 0.001:
                duration_str = f"{part.duration*1000:.3f}ms"
            elif part.duration < 1:
                duration_str = f"{part.duration*1000:.1f}ms"
            else:
                duration_str = f"{part.duration:.3f}s"
        
        # Format timestamp for display
        timestamp_str = ""
        if part.start_time > 0:
            timestamp_str = self._format_timestamp(part.start_time)
        
        # Choose icon based on part class
        icon = "⚙️"
        if "EXECUTION" in part.part_class:
            icon = "🚀"
        elif "GET_BY_ID" in part.part_class:
            icon = "🔍"
        elif "FILTER" in part.part_class:
            icon = "🔧"
        elif "EQUALS" in part.part_class:
            icon = "⚖️"
        elif "COUNT" in part.part_class:
            icon = "🔢"
        elif "QUERY" in part.part_class:
            icon = "🔍"
        elif "OPERATOR" in part.part_class:
            icon = "⚙️"
        elif "SCOPE" in part.part_class:
            icon = "🌐"
        elif "DOWNLOAD" in part.part_class:
            icon = "⬇️"
        elif "PARSE" in part.part_class:
            icon = "📝"
        elif "RENDER" in part.part_class:
            icon = "🎨"
        
        html.append(f'<div class="part">')
        html.append(f'<div class="part-header">')
        html.append(f'<div class="part-header-left">')
        html.append(f'<span class="icon">{icon}</span>')
        html.append(f'<span class="part-class {part.part_class}">[{part.part_class}]</span>')
        html.append(f'<span>{part.name}</span>')
        html.append('</div>')
        html.append(f'<div class="part-header-right">')
        if duration_str:
            html.append(f'<span class="duration">{duration_str}</span>')
        if timestamp_str:
            html.append(f'<span class="timestamp">{timestamp_str}</span>')
        html.append('<button class="collapse-btn" onclick="toggleCollapse(this)"></button>')
        html.append('</div>')
        html.append('</div>')
        html.append('<div class="part-content">')
        
        # Create a list of all events (logs and subparts) with their timestamps
        events = []
        
        # Add logs
        for log in part.logs:
            events.append((log.timestamp, 'log', log))
        
        # Add subparts
        for subpart in part.subparts:
            events.append((subpart.start_time, 'part', subpart))
        
        # Sort by timestamp
        events.sort(key=lambda x: x[0])
        
        # Generate HTML for events in chronological order
        for timestamp, event_type, event_data in events:
            if event_type == 'log':
                log_timestamp = self._format_timestamp(event_data.timestamp)
                # Choose icon based on log class
                log_icon = "📝"
                if "SUCCESS" in event_data.log_class:
                    log_icon = "✅"
                elif "FAILED" in event_data.log_class or "ERROR" in event_data.log_class:
                    log_icon = "❌"
                elif "DOWNLOAD" in event_data.log_class:
                    log_icon = "⬇️"
                elif "OPERATOR" in event_data.log_class:
                    log_icon = "⚙️"
                elif "INFO" in event_data.log_class:
                    log_icon = "ℹ️"
                
                html.append(f'<div class="log">')
                html.append(f'<div class="log-header">')
                html.append(f'<div class="log-header-left">')
                html.append(f'<span class="icon">{log_icon}</span>')
                html.append(f'<span class="log-class {event_data.log_class}">[{event_data.log_class}]</span>')
                html.append('</div>')
                html.append(f'<div class="log-header-right">')
                html.append(f'<span class="timestamp">{log_timestamp}</span>')
                html.append('<button class="log-collapse-btn" onclick="toggleLogCollapse(this)"></button>')
                html.append('</div>')
                html.append('</div>')
                html.append(f'<div class="log-content">{event_data.message}</div>')
                html.append('</div>')
            elif event_type == 'part':
                html.append(self._to_html_recursive(event_data, indent_level + 1))
        
        html.append('</div>')
        html.append('</div>')
        return "\n".join(html)
    
    def _to_html_minimal(self, part: Part, indent_level: int) -> str:
        """Generate minimal HTML for parts (only headers, no content)."""
        html = []
        
        # Format duration for display
        duration_str = ""
        if part.duration > 0:
            if part.duration < 0.001:
                duration_str = f"{part.duration*1000:.3f}ms"
            elif part.duration < 1:
                duration_str = f"{part.duration*1000:.1f}ms"
            else:
                duration_str = f"{part.duration:.3f}s"
        
        # Format timestamp for display
        timestamp_str = ""
        if part.start_time > 0:
            timestamp_str = self._format_timestamp(part.start_time)
        
        # Choose icon based on part class
        icon = "⚙️"
        if "EXECUTION" in part.part_class:
            icon = "🚀"
        elif "GET_BY_ID" in part.part_class:
            icon = "🔍"
        elif "FILTER" in part.part_class:
            icon = "🔧"
        elif "EQUALS" in part.part_class:
            icon = "⚖️"
        elif "COUNT" in part.part_class:
            icon = "🔢"
        elif "QUERY" in part.part_class:
            icon = "🔍"
        elif "OPERATOR" in part.part_class:
            icon = "⚙️"
        elif "SCOPE" in part.part_class:
            icon = "🌐"
        elif "DOWNLOAD" in part.part_class:
            icon = "⬇️"
        elif "PARSE" in part.part_class:
            icon = "📝"
        elif "RENDER" in part.part_class:
            icon = "🎨"
        
        # Generate unique ID for this part
        part_id = f"part_{id(part)}"
        
        html.append(f'<div class="part" data-part-id="{part_id}">')
        html.append(f'<div class="part-header">')
        html.append(f'<div class="part-header-left">')
        html.append(f'<span class="icon">{icon}</span>')
        html.append(f'<span class="part-class {part.part_class}">[{part.part_class}]</span>')
        html.append(f'<span>{part.name}</span>')
        html.append('</div>')
        html.append(f'<div class="part-header-right">')
        if duration_str:
            html.append(f'<span class="duration">{duration_str}</span>')
        if timestamp_str:
            html.append(f'<span class="timestamp">{timestamp_str}</span>')
        html.append('<button class="collapse-btn" onclick="toggleCollapse(this)"></button>')
        html.append('</div>')
        html.append('</div>')
        html.append('<div class="part-content"></div>')
        html.append('</div>')
        
        return "\n".join(html)
    
    def _to_js_data(self, part: Part) -> str:
        """Convert part data to JavaScript object for lazy loading."""
        import json
        
        def safe_str(obj):
            """Convert any object to a safe string representation."""
            if obj is None:
                return None
            try:
                # Try to convert to string first
                return str(obj)
            except Exception:
                # If that fails, use repr
                return repr(obj)
        
        def part_to_dict(p: Part) -> dict:
            return {
                'id': f"part_{id(p)}",
                'name': safe_str(p.name),
                'part_class': safe_str(p.part_class),
                'start_time': float(p.start_time) if p.start_time else 0.0,
                'end_time': float(p.end_time) if p.end_time else 0.0,
                'duration': float(p.duration) if p.duration else 0.0,
                'logs': [
                    {
                        'message': safe_str(log.message),
                        'timestamp': float(log.timestamp) if log.timestamp else 0.0,
                        'log_class': safe_str(log.log_class)
                    }
                    for log in p.logs
                ],
                'subparts': [part_to_dict(subpart) for subpart in p.subparts]
            }
        
        data = part_to_dict(part)
        return json.dumps(data, indent=2)
    
    def reset(self) -> None:
        """Reset the debugger state (useful for testing)."""
        self.root_part = Part(name="root")
        self.current_part = self.root_part


# Global debugger instance
debugger = Debugger()
