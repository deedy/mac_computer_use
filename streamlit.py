"""
Entrypoint for streamlit, see https://docs.streamlit.io/
"""

import asyncio
import base64
import os
import subprocess
from datetime import datetime
from enum import StrEnum
from functools import partial
from pathlib import PosixPath
from typing import cast, Any
import json

from anthropic import APIResponse
from anthropic.types import Message
from anthropic.types.beta import BetaMessage, BetaToolUseBlock
from anthropic.types.tool_use_block import ToolUseBlock
from dotenv import load_dotenv

import streamlit as st
from streamlit.components.v1 import html
from loop import (
    PROVIDER_TO_DEFAULT_MODEL_NAME,
    APIProvider,
    sampling_loop,
)
from streamlit.delta_generator import DeltaGenerator
from tools import ToolResult

load_dotenv()

# Rest of the file remains unchanged...

CONFIG_DIR = PosixPath("~/.anthropic").expanduser()
API_KEY_FILE = CONFIG_DIR / "api_key"

# Custom CSS for styling and animations
STREAMLIT_STYLE = """
<style>
    /* Hide chat input while agent loop is running */
    .stApp[data-teststate=running] .stChatInput textarea,
    .stApp[data-test-script-state=running] .stChatInput textarea {
        display: none;
    }
    /* Hide the streamlit deploy button */
    .stDeployButton {
        visibility: hidden;
    }
    /* Mouse tracker styles */
    #mouse-tracker {
        position: fixed;
        width: 20px;
        height: 20px;
        background: rgba(255, 0, 0, 0.3);
        border-radius: 50%;
        pointer-events: none;
        z-index: 9999;
        transition: all 0.1s ease;
        display: none;
    }
    /* Click animation */
    .click-animation {
        position: fixed;
        width: 40px;
        height: 40px;
        border: 2px solid red;
        border-radius: 50%;
        pointer-events: none;
        z-index: 9998;
        animation: clickRipple 0.5s ease-out;
    }
    @keyframes clickRipple {
        0% {
            transform: scale(0.5);
            opacity: 1;
        }
        100% {
            transform: scale(1.5);
            opacity: 0;
        }
    }
    /* Auto scroll container */
    .chat-container {
        height: calc(100vh - 200px);
        overflow-y: auto;
        scroll-behavior: smooth;
    }
</style>

<div id="mouse-tracker"></div>

<script>
    // Mouse tracking
    const tracker = document.getElementById('mouse-tracker');
    let lastX = 0;
    let lastY = 0;
    
    function updateMousePosition(x, y) {
        tracker.style.display = 'block';
        tracker.style.left = x + 'px';
        tracker.style.top = y + 'px';
        lastX = x;
        lastY = y;
    }
    
    // Click animation
    function createClickAnimation(x, y) {
        const clickEffect = document.createElement('div');
        clickEffect.className = 'click-animation';
        clickEffect.style.left = (x - 20) + 'px';
        clickEffect.style.top = (y - 20) + 'px';
        document.body.appendChild(clickEffect);
        
        setTimeout(() => {
            clickEffect.remove();
        }, 500);
    }
    
    // User controls toggle
    let controlsEnabled = true;
    document.addEventListener('keydown', (e) => {
        if (e.key === ' ' && e.metaKey) {  // Space + Cmd
            controlsEnabled = !controlsEnabled;
            const event = new CustomEvent('controlsToggle', { detail: controlsEnabled });
            window.dispatchEvent(event);
        }
    });
    
    // Auto scroll
    function scrollToBottom() {
        const container = document.querySelector('.chat-container');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    // Expose functions to Python
    window.streamlitFunctions = {
        updateMousePosition,
        createClickAnimation,
        scrollToBottom
    };
</script>
"""

WARNING_TEXT = ""


class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"


def setup_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_key" not in st.session_state:
        st.session_state.api_key = load_from_storage("api_key") or os.getenv(
            "ANTHROPIC_API_KEY", ""
        )
    if "provider" not in st.session_state:
        st.session_state.provider = (
            os.getenv("API_PROVIDER", "bricks") or APIProvider.BRICKS
        )
    if "provider_radio" not in st.session_state:
        st.session_state.provider_radio = st.session_state.provider
    if "model" not in st.session_state:
        _reset_model()
    if "auth_validated" not in st.session_state:
        st.session_state.auth_validated = False
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "tools" not in st.session_state:
        st.session_state.tools = {}
    if "only_n_most_recent_images" not in st.session_state:
        st.session_state.only_n_most_recent_images = 10
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = load_from_storage("system_prompt") or ""
    if "hide_images" not in st.session_state:
        st.session_state.hide_images = False
    if "controls_enabled" not in st.session_state:
        st.session_state.controls_enabled = True


def _reset_model():
    st.session_state.model = PROVIDER_TO_DEFAULT_MODEL_NAME[
        cast(APIProvider, st.session_state.provider)
    ]


def toggle_controls():
    st.session_state.controls_enabled = not st.session_state.controls_enabled


async def main():
    """Render loop for streamlit"""
    setup_state()

    st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)

    st.title("Claude Computer Use for Mac")

    # User controls toggle button (only visible to users)
    col1, col2 = st.columns([3, 1])
    with col2:
        st.button("Toggle Controls (⌘ + Space)", on_click=toggle_controls)
        if st.session_state.controls_enabled:
            st.success("Controls Enabled")
        else:
            st.error("Controls Disabled")

    st.markdown(
        """This is from [Mac Computer Use](https://github.com/deedy/mac_computer_use), a fork of [Anthropic Computer Use](https://github.com/anthropics/anthropic-quickstarts/blob/main/computer-use-demo/README.md) to work natively on Mac."""
    )

    with st.sidebar:

        def _reset_api_provider():
            if st.session_state.provider_radio != st.session_state.provider:
                _reset_model()
                st.session_state.provider = st.session_state.provider_radio
                st.session_state.auth_validated = False

        provider_options = [option.value for option in APIProvider]
        st.radio(
            "API Provider",
            options=provider_options,
            key="provider_radio",
            format_func=lambda x: x.title(),
            on_change=_reset_api_provider,
        )

        st.text_input("Model", key="model")

        if st.session_state.provider in [APIProvider.ANTHROPIC, APIProvider.BRICKS]:
            api_key_label = (
                "BricksAI Secret Key"
                if st.session_state.provider == APIProvider.BRICKS
                else "Anthropic API Key"
            )
            st.text_input(
                api_key_label,
                type="password",
                key="api_key",
                on_change=lambda: save_to_storage("api_key", st.session_state.api_key),
            )

        st.number_input(
            "Only send N most recent images",
            min_value=0,
            key="only_n_most_recent_images",
            help="To decrease the total tokens sent, remove older screenshots from the conversation",
        )
        st.text_area(
            "Custom System Prompt Suffix",
            key="custom_system_prompt",
            help="Additional instructions to append to the system prompt. see computer_use_demo/loop.py for the base system prompt.",
            on_change=lambda: save_to_storage(
                "system_prompt", st.session_state.custom_system_prompt
            ),
        )
        st.checkbox("Hide screenshots", key="hide_images")

        if st.button("Reset", type="primary"):
            with st.spinner("Resetting..."):
                st.session_state.clear()
                setup_state()

                subprocess.run("pkill Xvfb; pkill tint2", shell=True, check=True)  # noqa: ASYNC221
                await asyncio.sleep(1)
                subprocess.run("./start_all.sh", shell=True)  # noqa: ASYNC221

    if not st.session_state.auth_validated:
        if auth_error := validate_auth(
            st.session_state.provider, st.session_state.api_key
        ):
            st.warning(f"Please resolve the following auth issue:\n\n{auth_error}")
            return
        else:
            st.session_state.auth_validated = True

    chat, http_logs = st.tabs(["Chat", "HTTP Exchange Logs"])
    new_message = st.chat_input(
        "Type a message to send to Claude to control the computer..."
    )

    with chat:
        # Create a container for auto-scrolling
        chat_container = st.container()
        with chat_container:
            # render past chats
            for message in st.session_state.messages:
                if isinstance(message["content"], str):
                    _render_message(message["role"], message["content"])
                elif isinstance(message["content"], list):
                    for block in message["content"]:
                        if isinstance(block, dict) and block["type"] == "tool_result":
                            _render_message(
                                Sender.TOOL,
                                st.session_state.tools[block["tool_use_id"]],
                            )
                        else:
                            _render_message(
                                message["role"],
                                cast(Any, block),
                            )

            # render past http exchanges
            for identity, response in st.session_state.responses.items():
                _render_api_response(response, identity, http_logs)

            # render new message
            if new_message:
                st.session_state.messages.append(
                    {
                        "role": Sender.USER,
                        "content": [{"type": "text", "text": new_message}],
                    }
                )
                _render_message(Sender.USER, new_message)

            try:
                most_recent_message = st.session_state["messages"][-1]
            except IndexError:
                return

            if most_recent_message["role"] is not Sender.USER:
                return

            with st.spinner("Running Agent..."):
                st.session_state.messages = await sampling_loop(
                    system_prompt_suffix=st.session_state.custom_system_prompt,
                    model=st.session_state.model,
                    provider=st.session_state.provider,
                    messages=st.session_state.messages,
                    output_callback=partial(_render_message, Sender.BOT),
                    tool_output_callback=partial(
                        _tool_output_callback, tool_state=st.session_state.tools
                    ),
                    api_response_callback=partial(
                        _api_response_callback,
                        tab=http_logs,
                        response_state=st.session_state.responses,
                    ),
                    api_key=st.session_state.api_key,
                    only_n_most_recent_images=st.session_state.only_n_most_recent_images,
                )

        # Auto scroll after rendering
        html("""
            <script>
                window.streamlitFunctions.scrollToBottom();
            </script>
        """)


def validate_auth(provider: APIProvider, api_key: str | None):
    if provider in [APIProvider.ANTHROPIC, APIProvider.BRICKS]:
        if not api_key:
            key_type = (
                "BricksAI Secret Key"
                if provider == APIProvider.BRICKS
                else "Anthropic API Key"
            )
            return f"Enter your {key_type} in the sidebar to continue."
    if provider == APIProvider.BEDROCK:
        import boto3

        if not boto3.Session().get_credentials():
            return "You must have AWS credentials set up to use the Bedrock API."
    if provider == APIProvider.VERTEX:
        import google.auth
        from google.auth.exceptions import DefaultCredentialsError

        if not os.environ.get("CLOUD_ML_REGION"):
            return "Set the CLOUD_ML_REGION environment variable to use the Vertex API."
        try:
            google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        except DefaultCredentialsError:
            return "Your google cloud credentials are not set up correctly."


def load_from_storage(filename: str) -> str | None:
    """Load data from a file in the storage directory."""
    try:
        file_path = CONFIG_DIR / filename
        if file_path.exists():
            data = file_path.read_text().strip()
            if data:
                return data
    except Exception as e:
        st.write(f"Debug: Error loading {filename}: {e}")
    return None


def save_to_storage(filename: str, data: str) -> None:
    """Save data to a file in the storage directory."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        file_path = CONFIG_DIR / filename
        file_path.write_text(data)
        # Ensure only user can read/write the file
        file_path.chmod(0o600)
    except Exception as e:
        st.write(f"Debug: Error saving {filename}: {e}")


def _api_response_callback(
    response: APIResponse[BetaMessage],
    tab: DeltaGenerator,
    response_state: dict[str, APIResponse[BetaMessage]],
):
    """Handle an API response by storing it to state and rendering it."""
    response_id = datetime.now().isoformat()
    response_state[response_id] = response
    _render_api_response(response, response_id, tab)


def _tool_output_callback(
    tool_output: ToolResult, tool_id: str, tool_state: dict[str, ToolResult]
):
    """Handle a tool output by storing it to state and rendering it."""
    tool_state[tool_id] = tool_output
    _render_message(Sender.TOOL, tool_output)

    # Update mouse tracker for mouse movements
    if hasattr(tool_output, "output") and "cliclick m:" in str(tool_output.output):
        coords = str(tool_output.output).split("m:")[1].strip().split(",")
        if len(coords) == 2:
            html(f"""
                <script>
                    window.streamlitFunctions.updateMousePosition({coords[0]}, {coords[1]});
                </script>
            """)

    # Show click animation for clicks
    if hasattr(tool_output, "output") and any(
        cmd in str(tool_output.output) for cmd in ["c:", "rc:", "dc:", "mc:"]
    ):
        # Get current mouse position from tracker
        html("""
            <script>
                const tracker = document.getElementById('mouse-tracker');
                if (tracker) {
                    window.streamlitFunctions.createClickAnimation(
                        parseInt(tracker.style.left),
                        parseInt(tracker.style.top)
                    );
                }
            </script>
        """)


def _render_api_response(
    response: APIResponse[BetaMessage], response_id: str, tab: DeltaGenerator
):
    """Render an API response to a streamlit tab"""
    with tab:
        with st.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            st.markdown(
                f"`{response.http_request.method} {response.http_request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.http_request.headers.items())}"
            )
            st.json(response.http_request.read().decode())
            st.markdown(
                f"`{response.http_response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}"
            )
            st.json(response.http_response.text)


def _render_message(
    sender: Sender,
    message: str | dict | BetaToolUseBlock | ToolResult,
):
    """Convert input from the user or output from the agent to a streamlit message."""
    is_tool_result = not isinstance(message, str) and (
        isinstance(message, ToolResult)
        or message.__class__.__name__ == "ToolResult"
        or message.__class__.__name__ == "CLIResult"
    )
    if not message or (
        is_tool_result
        and st.session_state.hide_images
        and not hasattr(message, "error")
        and not hasattr(message, "output")
    ):
        return
    with st.chat_message(sender):
        if is_tool_result:
            message = cast(ToolResult, message)
            if message.output:
                if message.__class__.__name__ == "CLIResult":
                    st.code(message.output)
                else:
                    st.markdown(message.output)
            if message.error:
                st.error(message.error)
            if message.base64_image and not st.session_state.hide_images:
                st.image(base64.b64decode(message.base64_image))
        elif isinstance(message, dict) and message.get("type") == "text":
            st.write(message.get("text", ""))
        elif isinstance(message, BetaToolUseBlock) or isinstance(message, ToolUseBlock):
            st.code(f"Tool Use: {message.name}\nInput: {message.input}")
        else:
            st.markdown(message)


if __name__ == "__main__":
    asyncio.run(main())
