"""
Debug module for the SA query language.

Provides a singleton Debugger class to track execution parts and logs
in a hierarchical structure for debugging query language operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import time
from datetime import datetime
import pytz
import inspect
import os


@dataclass
class LogEntry:
    """Represents a single log entry with timestamp and class."""
    message: str
    timestamp: float
    log_class: str = "INFO"
    file_location: Optional[str] = None
    
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
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    combined_count: int = 0
    
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
        self._total_overhead_time: float = 0.0
        self._enabled: bool = False
    
    def enable(self) -> None:
        """Enable the debugger. When disabled, all methods are no-ops for performance."""
        self._enabled = True
    
    def _get_caller_location(self) -> Optional[str]:
        """Get the file:line location of the caller."""
        try:
            # Get the frame that called the debugger method (skip internal frames)
            # Frame 0 is _get_caller_location itself
            # Frame 1 is the debugger method (log, start_part, end_part)
            # Frame 2 is the actual caller we want
            frame = inspect.currentframe()
            if frame is None:
                return None
            
            # Skip to the caller frame (2 levels up from here)
            caller_frame = frame.f_back
            if caller_frame is None:
                return None
            caller_frame = caller_frame.f_back
            if caller_frame is None:
                return None
            
            filename = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno
            
            # Get relative path from workspace or absolute path
            # Try to get relative path, fall back to basename if not in workspace
            try:
                # Get workspace path - assume it's the parent directory of 'sa'
                workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if filename.startswith(workspace_root):
                    rel_path = os.path.relpath(filename, workspace_root)
                    return f"{rel_path}:{lineno}"
            except (ValueError, OSError):
                pass
            
            # Fallback to basename if relative path doesn't work
            return f"{os.path.basename(filename)}:{lineno}"
        except Exception:
            return None
    
    def start_part(self, part_class: str, part_name: str) -> None:
        """
        Start a new execution part.
        
        Args:
            part_class: Class/category of the part (e.g., "EXECUTION", "OPERATOR", "QUERY")
            part_name: Name of the part being started
            
        Raises:
            ValueError: If a subpart with the same part_class already exists
        """
        if not self._enabled:
            return
        start_time = time.time()
        location = self._get_caller_location()
        
        # Check for existing subpart with the same class
        # Allow duplicates only if they are all contiguous at the end of the subparts list
        subparts = self.current_part.subparts
        if subparts:
            # Find the last index where the class is different from the new one
            # This tells us where the contiguous block of same-class subparts ends
            last_different_index = -1
            for i in range(len(subparts) - 1, -1, -1):
                if subparts[i].part_class != part_class:
                    last_different_index = i
                    break
            
            # Check if there's a subpart with the same class before the contiguous block at the end
            # If we found a different class subpart, check if any same-class subparts exist before it
            if last_different_index >= 0:
                for i in range(last_different_index + 1):
                    if subparts[i].part_class == part_class:
                        # Found a non-contiguous duplicate - error!
                        existing_subpart = subparts[i]
                        existing_location = existing_subpart.start_location or "unknown location"
                        new_location = location or "unknown location"
                        raise ValueError(
                            f"Cannot add subpart with class '{part_class}' to part '{self.current_part.name}'. "
                            f"Found a non-contiguous duplicate: a subpart with class '{part_class}' exists "
                            f"but is not at the end of the subparts list.\n"
                            f"  Non-contiguous subpart: name='{existing_subpart.name}', "
                            f"class='{existing_subpart.part_class}', location={existing_location}\n"
                            f"  New subpart: name='{part_name}', class='{part_class}', location={new_location}\n"
                            f"  Parent part: name='{self.current_part.name}', "
                            f"class='{self.current_part.part_class}', "
                            f"has {len(subparts)} existing subpart(s)\n"
                            f"  Note: Duplicates are only allowed if they are all contiguous at the end."
                        )
        
        new_part = Part(name=part_name, part_class=part_class, parent=self.current_part, 
                       start_time=time.time(), start_location=location)
        self.current_part.subparts.append(new_part)
        self.current_part = new_part
        self._total_overhead_time += time.time() - start_time

    def end_part_if_current(self, part_name: str) -> None:
        """
        End the current execution part if it is the one being ended.
        """
        if not self._enabled:
            return
        if self.current_part.name == part_name:
            self.end_part(part_name)
    
    def end_part(self, part_name: str) -> None:
        """
        End the current execution part.
        
        Args:
            part_name: Name of the part being ended (must match current part)
            
        Raises:
            RuntimeError: If the part_name doesn't match the current part
        """
        if not self._enabled:
            return
        start_time = time.time()
        if self.current_part.name != part_name:
            raise RuntimeError(
                f"Part mismatch: trying to end '{part_name}' but current part is "
                f"'{self.current_part.name}'. This indicates "
                "a missing end_part() call or incorrect nesting."
                f"Current part: {self.current_part.name}"
            )

        # Check if we should combine with the previous part (detect loops)
        if self.current_part.parent is not None and len(self.current_part.parent.subparts) >= 2:
            # Get the last 5 subparts (excluding current, which is the last one)
            last_5_subparts = self.current_part.parent.subparts[-6:-1]  # Exclude current part
            if len(last_5_subparts) >= 5:
                name_set = set([part.name for part in last_5_subparts])
                if len(name_set) == 1 and self.current_part.name in name_set:
                    # We have a loop - combine with the previous part
                    # Record current part's end time
                    current_end_time = time.time()
                    current_end_location = self._get_caller_location()
                    
                    # Get the previous part (the one before current in parent's subparts)
                    previous_part = self.current_part.parent.subparts[-2]
                    
                    # Remove current part from parent's subparts
                    self.current_part.parent.subparts.pop()
                    
                    # Combine with previous part:
                    # - Increment combined_count
                    previous_part.combined_count += 1
                    # - Set end_time to current part's end_time
                    previous_part.end_time = current_end_time
                    # - Keep previous part's name the same (it already matches)
                    # - Delete current part's subparts (we don't keep them)
                    #   (current part will be garbage collected)
                    
                    # Move back to parent part
                    self._move_to_parent()
                    self._total_overhead_time += time.time() - start_time
                    return
        
        # Record end time and location
        self.current_part.end_time = time.time()
        self.current_part.end_location = self._get_caller_location()
        
        # Move back to parent part
        self._move_to_parent()
        self._total_overhead_time += time.time() - start_time
    
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
        if not self._enabled:
            return
        start_time = time.time()
        location = self._get_caller_location()
        log_entry = LogEntry(message=message, timestamp=time.time(), log_class=log_class, file_location=location)
        self.current_part.logs.append(log_entry)
        self._total_overhead_time += time.time() - start_time
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Convert Unix timestamp to readable date in Chicago timezone."""
        chicago_tz = pytz.timezone('America/Chicago')
        dt = datetime.fromtimestamp(timestamp, tz=chicago_tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Remove last 3 digits for milliseconds
    
    def _format_duration(self, duration: float) -> str:
        """Format duration in a human-readable way."""
        if duration < 0.001:
            return f"{duration*1000:.3f}ms"
        elif duration < 1:
            return f"{duration*1000:.1f}ms"
        else:
            return f"{duration:.3f}s"

    def _to_text(self, part: Part, indent: int = 0) -> str:
        """Convert debugger state to plain text format."""
        lines = []
        indent_str = "  " * indent
        
        # Format location string
        location_str = ""
        if part.start_location:
            if part.end_location and part.end_location != part.start_location:
                location_str = f" [{part.start_location} -> {part.end_location}]"
            else:
                location_str = f" [{part.start_location}]"
        
        # Format duration
        duration_str = ""
        if part.duration > 0:
            if part.duration < 0.001:
                duration_str = f" ({part.duration*1000:.3f}ms)"
            elif part.duration < 1:
                duration_str = f" ({part.duration*1000:.1f}ms)"
            else:
                duration_str = f" ({part.duration:.3f}s)"
        
        # Format timestamp
        timestamp_str = ""
        if part.start_time > 0:
            timestamp_str = f" @ {self._format_timestamp(part.start_time)}"
        
        # Format combined count
        combined_str = ""
        if part.combined_count > 0:
            combined_str = f" (ran {part.combined_count} more times...)"
        
        # Part header
        lines.append(f"{indent_str}[{part.part_class}] {part.name}{combined_str}{location_str}{duration_str}{timestamp_str}")
        
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
        
        # Generate text for events in chronological order
        for timestamp, event_type, event_data in events:
            if event_type == 'log':
                log_timestamp = self._format_timestamp(event_data.timestamp)
                location_str = f" [{event_data.file_location}]" if event_data.file_location else ""
                lines.append(f"{indent_str}  [{event_data.log_class}] @ {log_timestamp}{location_str}")
                # Format message with indentation for multi-line
                message_lines = str(event_data.message).split('\n')
                for msg_line in message_lines:
                    lines.append(f"{indent_str}    {msg_line}")
            elif event_type == 'part':
                lines.append(self._to_text(event_data, indent + 1))
        
        return "\n".join(lines)
    
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
        .location { 
            color: #9b59b6; 
            font-size: 0.75em;
            background: #f4ecf7;
            padding: 3px 6px;
            border-radius: 4px;
            white-space: nowrap;
            font-family: monospace;
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
        .text-output {
            background: #f8f9fa;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            padding: 20px;
            margin: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            word-break: break-word;
            overflow-x: auto;
            max-height: none;
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
        
        # Generate text output for text mode
        text_output = self._to_text(self.root_part)
        # Escape for HTML (basic escaping)
        import html as html_module
        text_output_escaped = html_module.escape(text_output)
        
        html.append("""
        <script>
        // Check if ?text is in URL
        const urlParams = new URLSearchParams(window.location.search);
        const isTextMode = urlParams.has('text');
        </script>
        """)
        
        # Format overhead time
        overhead_str = self._format_duration(self._total_overhead_time)
        
        # Text mode output (hidden by default, shown via JS)
        html.append(f'<div id="text-mode-output" style="display: none;">')
        html.append('<div class="container">')
        html.append('<div class="header">')
        html.append('<h1><span class="icon">🐛</span> SA Query Debug Output (Text Mode)</h1>')
        html.append(f'<div style="margin-top: 10px; font-size: 0.9em; opacity: 0.9;">Debugger overhead: {overhead_str}</div>')
        html.append('</div>')
        html.append('<div class="global-controls">')
        html.append('<button onclick="window.location.href=window.location.pathname">View HTML Mode</button>')
        html.append('</div>')
        html.append(f'<div class="text-output"><pre>{text_output_escaped}</pre></div>')
        html.append('</div>')
        html.append('</div>')
        
        # HTML mode output (hidden by default, shown via JS)
        html.append('<div id="html-mode-output" style="display: none;">')
        html.append('<div class="container">')
        html.append('<div class="header">')
        html.append('<h1><span class="icon">🐛</span> SA Query Debug Output</h1>')
        html.append(f'<div style="margin-top: 10px; font-size: 0.9em; opacity: 0.9;">Debugger overhead: {overhead_str}</div>')
        html.append('</div>')
        html.append('<div class="global-controls">')
        html.append('<button onclick="window.location.href=window.location.pathname + \'?text\'">View Text Mode</button>')
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
        html.append('</div>')
        
        # Generate JavaScript data for HTML mode
        debug_data = self._to_js_data(self.root_part)
        
        # JavaScript to show/hide the appropriate mode
        html.append(f"""
        <script>
        if (isTextMode) {{
            document.getElementById('text-mode-output').style.display = 'block';
        }} else {{
            document.getElementById('html-mode-output').style.display = 'block';
            
            // Only load JavaScript for HTML mode
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
            const locationStr = logData.file_location || '';
            
            return `
                <div class="log">
                    <div class="log-header">
                        <div class="log-header-left">
                            <span class="icon">${{logIcon}}</span>
                            <span class="log-class ${{logData.log_class}}">[${{logData.log_class}}]</span>
                        </div>
                        <div class="log-header-right">
                            ${{locationStr ? `<span class="location">${{escapeHtml(locationStr)}}</span>` : ''}}
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
            const startLocationStr = partData.start_location || '';
            const endLocationStr = partData.end_location || '';
            const locationStr = startLocationStr ? (endLocationStr && endLocationStr !== startLocationStr ? 
                `${{startLocationStr}} -> ${{endLocationStr}}` : startLocationStr) : '';
            const combinedStr = partData.combined_count > 0 ? 
                ` <span style="color: white; font-weight: bold; background: #a53c6b; padding: 2px; border-radius: 5px;">(ran ${{partData.combined_count}} more times...)</span>` : '';
            
            return `
                <div class="part" data-part-id="${{partData.id}}">
                    <div class="part-header">
                        <div class="part-header-left">
                            <span class="icon">${{icon}}</span>
                            <span class="part-class ${{partData.part_class}}">[${{partData.part_class}}]</span>
                            <span>${{escapeHtml(partData.name)}}</span>${{combinedStr}}
                        </div>
                        <div class="part-header-right">
                            ${{locationStr ? `<span class="location">${{escapeHtml(locationStr)}}</span>` : ''}}
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
        
        # Format location string
        location_str = ""
        if part.start_location:
            if part.end_location and part.end_location != part.start_location:
                location_str = f"{part.start_location} -> {part.end_location}"
            else:
                location_str = part.start_location
        
        # Format combined count
        combined_str = ""
        if part.combined_count > 0:
            combined_str = f' <span style="color: white; font-weight: bold; background: #a53c6b; padding: 2px; border-radius: 5px;">(ran {part.combined_count} more times...)</span>'
        
        html.append(f'<div class="part">')
        html.append(f'<div class="part-header">')
        html.append(f'<div class="part-header-left">')
        html.append(f'<span class="icon">{icon}</span>')
        html.append(f'<span class="part-class {part.part_class}">[{part.part_class}]</span>')
        html.append(f'<span>{part.name}</span>{combined_str}')
        html.append('</div>')
        html.append(f'<div class="part-header-right">')
        if location_str:
            html.append(f'<span class="location">{location_str}</span>')
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
                
                location_str = event_data.file_location or ""
                html.append(f'<div class="log">')
                html.append(f'<div class="log-header">')
                html.append(f'<div class="log-header-left">')
                html.append(f'<span class="icon">{log_icon}</span>')
                html.append(f'<span class="log-class {event_data.log_class}">[{event_data.log_class}]</span>')
                html.append('</div>')
                html.append(f'<div class="log-header-right">')
                if location_str:
                    html.append(f'<span class="location">{location_str}</span>')
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
        
        # Format location string
        location_str = ""
        if part.start_location:
            if part.end_location and part.end_location != part.start_location:
                location_str = f"{part.start_location} -> {part.end_location}"
            else:
                location_str = part.start_location
        
        # Format combined count
        combined_str = ""
        if part.combined_count > 0:
            combined_str = f' <span style="color: white; font-weight: bold; background: #a53c6b; padding: 2px; border-radius: 5px;">(ran {part.combined_count} more times...)</span>'
        
        html.append(f'<div class="part" data-part-id="{part_id}">')
        html.append(f'<div class="part-header">')
        html.append(f'<div class="part-header-left">')
        html.append(f'<span class="icon">{icon}</span>')
        html.append(f'<span class="part-class {part.part_class}">[{part.part_class}]</span>')
        html.append(f'<span>{part.name}</span>{combined_str}')
        html.append('</div>')
        html.append(f'<div class="part-header-right">')
        if location_str:
            html.append(f'<span class="location">{location_str}</span>')
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
                'start_location': safe_str(p.start_location),
                'end_location': safe_str(p.end_location),
                'combined_count': int(p.combined_count) if p.combined_count else 0,
                'logs': [
                    {
                        'message': safe_str(log.message),
                        'timestamp': float(log.timestamp) if log.timestamp else 0.0,
                        'log_class': safe_str(log.log_class),
                        'file_location': safe_str(log.file_location)
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
        self._total_overhead_time = 0.0


# Global debugger instance
debugger = Debugger()
