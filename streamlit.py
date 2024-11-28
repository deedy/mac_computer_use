"""Streamlit UI for computer use tools."""

import os
import sys
import asyncio
import base64
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import streamlit as st
from loguru import logger

from computer_use.tools.collection import ToolCollection
from computer_use.tools.bash import BashTool
from computer_use.tools.computer import ComputerTool
from computer_use.tools.edit import EditTool
from computer_use.tools.base_tool import ToolResult
from computer_use.tools.productivity import ProductivityManager
from computer_use.tools.cursor_integration import CursorIntegration


def format_duration(duration: timedelta) -> str:
    """Format timedelta into readable string."""
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def load_from_storage(key: str) -> Optional[str]:
    """Load value from storage."""
    try:
        storage_dir = Path.home() / ".config" / "mac_computer_use"
        if not storage_dir.exists():
            return None
            
        file_path = storage_dir / f"{key}.txt"
        if not file_path.exists():
            return None
            
        with open(file_path) as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Failed to load {key}: {e}")
        return None


def save_to_storage(key: str, value: str):
    """Save value to storage."""
    try:
        storage_dir = Path.home() / ".config" / "mac_computer_use"
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        with open(storage_dir / f"{key}.txt", "w") as f:
            f.write(value)
    except Exception as e:
        logger.error(f"Failed to save {key}: {e}")


def init_session_state():
    """Initialize session state with default values."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    if "session_id" not in st.session_state:
        st.session_state.session_id = base64.urlsafe_b64encode(os.urandom(9)).decode()
    if "tools" not in st.session_state:
        st.session_state.tools = None
    if "api_key" not in st.session_state:
        st.session_state.api_key = load_from_storage("api_key") or os.getenv("ANTHROPIC_API_KEY", "")
    if "start_time" not in st.session_state:
        st.session_state.start_time = datetime.now()
    if "productivity_manager" not in st.session_state:
        st.session_state.productivity_manager = ProductivityManager()
    if "cursor" not in st.session_state:
        st.session_state.cursor = CursorIntegration()


async def initialize_session():
    """Initialize session components and managers."""
    if not st.session_state.initialized:
        try:
            # Initialize tools collection
            st.session_state.tools = ToolCollection()
            
            # Create tool instances
            bash_tool = BashTool()
            computer_tool = ComputerTool()
            edit_tool = EditTool()
            
            # Add tools to collection
            st.session_state.tools.registry.register(bash_tool)
            st.session_state.tools.registry.register(computer_tool)
            st.session_state.tools.registry.register(edit_tool)
            
            # Initialize tools
            await st.session_state.tools.initialize()
            
            st.session_state.initialized = True
            logger.info(f"Session initialized with ID: {st.session_state.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            st.error("Failed to initialize session. Please refresh the page.")


def render_sidebar():
    """Render sidebar with configuration and session info."""
    with st.sidebar:
        st.markdown('<h1 style="color: #00cf86; margin-bottom: 2rem;">⚙️ Configuration</h1>', unsafe_allow_html=True)
        
        # API Key input
        st.markdown('<div class="api-key">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🔑 API Key</div>', unsafe_allow_html=True)
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=st.session_state.api_key,
            help="Enter your Anthropic API key"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            save_to_storage("api_key", api_key)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Session Information
        st.markdown('<div class="session-stats">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📊 Session Information</div>', unsafe_allow_html=True)
        
        current_time = datetime.now()
        last_saved = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Session ID", st.session_state.session_id[:8])
            st.metric("Status", "Active" if st.session_state.initialized else "Initializing")
        with col2:
            st.metric("Last Active", last_saved)
            st.metric("Duration", format_duration(current_time - st.session_state.start_time))
        st.markdown('</div>', unsafe_allow_html=True)


def render_productivity_sidebar():
    with st.sidebar:
        st.markdown("## 📊 Productivity Stats")
        
        stats = st.session_state.productivity_manager.get_productivity_stats()
        
        # Active Windows
        st.markdown("### 🪟 Window Activity")
        for window, percentage in stats['active_windows'].items():
            st.progress(percentage / 100, text=f"{window}: {percentage}%")
            
        # Time Tracking
        st.markdown("### ⏱️ Time Tracking")
        st.metric("Total Active Time (mins)", stats['total_active_time'])
        st.metric("Current Window", stats['current_window'])
        
        # Clipboard
        st.markdown("### 📋 Clipboard History")
        st.metric("Saved Items", stats['clipboard_items'])
        
        # Controls
        st.markdown("### ⚙️ Controls")
        if st.button("Clear History"):
            st.session_state.productivity_manager.clear_history()
            st.rerun()
            
        break_interval = st.number_input(
            "Break Interval (mins)",
            min_value=15,
            max_value=120,
            value=45
        )
        if st.button("Schedule Breaks"):
            st.session_state.productivity_manager.schedule_breaks(break_interval)
            st.success(f"Breaks scheduled every {break_interval} minutes")


def render_cursor_controls():
    """Render Cursor-specific controls"""
    st.markdown("## 🖱️ Cursor Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Launch GUI"):
            with st.spinner("Launching Cursor..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(st.session_state.cursor.launch_gui())
                finally:
                    loop.close()
                
    with col2:
        if st.button("Launch CLI"):
            with st.spinner("Launching Cursor..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(st.session_state.cursor.launch_cli())
                finally:
                    loop.close()
                
    # Cursor Settings
    st.markdown("### ⚙️ Cursor Settings")
    cursor_width = st.slider("Cursor Width", 1, 10, 2)
    cursor_color = st.color_picker("Cursor Color", "#00cf86")
    
    if st.button("Apply Settings"):
        settings = {
            "cursor_width": cursor_width,
            "cursor_color": cursor_color
        }
        with st.spinner("Applying settings..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    st.session_state.cursor.configure_cursor(settings)
                )
            finally:
                loop.close()


def apply_custom_css():
    """Apply custom CSS styling."""
    st.markdown("""
        <style>
        /* Dark theme enhancements */
        .stApp {
            background-color: #0E1117;
            color: #E0E0E0;
        }
        
        /* Command input styling */
        .command-input {
            background-color: #1E1E1E;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .command-input textarea {
            background-color: #2E2E2E;
            color: #E0E0E0;
            font-family: 'Monaco', monospace;
            border: 1px solid #3E3E3E;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #00cf86;
            color: #0E1117;
            font-weight: bold;
            border-radius: 5px;
            padding: 0.5rem 2rem;
            border: none;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: #00b876;
            transform: translateY(-1px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        /* Success/Error message styling */
        .success-message {
            background-color: #1a472a;
            color: #98ff98;
            padding: 1rem;
            border-radius: 5px;
            border-left: 5px solid #2ecc71;
            margin: 1rem 0;
        }
        
        .error-message {
            background-color: #4a1919;
            color: #ffb3b3;
            padding: 1rem;
            border-radius: 5px;
            border-left: 5px solid #e74c3c;
            margin: 1rem 0;
        }
        
        /* Help text styling */
        .help-text {
            background-color: #1E1E1E;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
            border-left: 5px solid #3498db;
        }
        
        /* Image output styling */
        .screenshot {
            border: 2px solid #3E3E3E;
            border-radius: 5px;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)


def render_help():
    """Render help section with example commands."""
    st.markdown("""
        <div class="help-text">
        <h3>📝 Example Commands</h3>
        <ul>
            <li><code>open safari and take a screenshot</code> - Opens Safari and captures the screen</li>
            <li><code>take a screenshot</code> - Captures the current screen</li>
            <li><code>ls -la</code> - Lists files in the current directory</li>
            <li><code>pwd</code> - Shows current working directory</li>
        </ul>
        <p><em>Tip: You can combine multiple commands using "and"</em></p>
        </div>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Apply custom styling
    apply_custom_css()
    
    # Initialize session state
    init_session_state()
    
    # Initialize session components
    if not st.session_state.initialized:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(initialize_session())
        finally:
            loop.close()
    
    # Render sidebar
    render_sidebar()
    
    # Render productivity sidebar
    render_productivity_sidebar()
    
    # Render cursor controls
    render_cursor_controls()
    
    # Main content
    st.title("💻 Computer Use")
    st.markdown("""
        Control your computer using natural language commands. 
        Type your command below and press Execute.
    """)
    
    # Command input section
    st.markdown('<div class="command-input">', unsafe_allow_html=True)
    command = st.text_area(
        "Enter your command:",
        height=100,
        placeholder="Example: open safari and take a screenshot"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        execute = st.button("⚡ Execute", use_container_width=True)
    with col2:
        if st.button("❓ Show Examples", use_container_width=True):
            render_help()
    st.markdown('</div>', unsafe_allow_html=True)
    
    if execute:
        if not command:
            st.markdown(
                '<div class="error-message">⚠️ Please enter a command.</div>',
                unsafe_allow_html=True
            )
            return
            
        if not st.session_state.initialized:
            st.markdown(
                '<div class="error-message">⚠️ Session not initialized. Please wait...</div>',
                unsafe_allow_html=True
            )
            return
            
        try:
            # Execute command asynchronously
            with st.spinner("🔄 Executing command..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        st.session_state.tools.execute("ComputerTool", command)
                    )
                finally:
                    loop.close()
                
                if not result:
                    st.markdown(
                        '<div class="error-message">❌ Command execution failed</div>',
                        unsafe_allow_html=True
                    )
                    return
                    
                if result.error:
                    st.markdown(
                        f'<div class="error-message">❌ {result.error}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div class="success-message">✅ Command executed successfully!</div>',
                        unsafe_allow_html=True
                    )
                    if result.output:
                        st.code(result.output, language="bash")
                    if result.base64_image:
                        try:
                            import base64
                            import io
                            from PIL import Image
                            
                            # Decode base64 string to image
                            img_data = base64.b64decode(result.base64_image)
                            img = Image.open(io.BytesIO(img_data))
                            
                            st.markdown('<div class="screenshot">', unsafe_allow_html=True)
                            st.image(img)
                            st.markdown('</div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error displaying image: {str(e)}")
                        
        except KeyboardInterrupt:
            st.warning("Operation cancelled by user")
            return
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            st.markdown(
                f'<div class="error-message">❌ An error occurred: {str(e)}</div>',
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        st.warning("Application shutting down...")
    except Exception as e:
        st.error(f"Application error: {str(e)}")
