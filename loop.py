"""
Agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
"""

import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, cast

from anthropic import Anthropic, AnthropicBedrock, AnthropicVertex, APIResponse
from anthropic.types import (
    ToolResultBlockParam,
)
from anthropic.types.beta import (
    BetaContentBlock,
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)

from tools import BashTool, ComputerTool, EditTool, ToolCollection, ToolResult

BETA_FLAG = "computer-use-2024-10-22"


class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"
    BRICKS = "bricks"


PROVIDER_TO_DEFAULT_MODEL_NAME: dict[APIProvider, str] = {
    APIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    APIProvider.BEDROCK: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    APIProvider.VERTEX: "claude-3-5-sonnet-v2@20241022",
    APIProvider.BRICKS: "claude-3-5-sonnet-20241022",
}

# This system prompt is optimized for the Docker environment in this repository and
# specific tool combinations enabled.
# We encourage modifying this system prompt to ensure the model has context for the
# environment it is running in, and to provide any additional information that may be
# helpful for the task at hand.

SYSTEM_PROMPT = f"""<SYSTEM_DEFINITION>
You are an advanced AI assistant operating within a macOS Sequoia Version 15.1 (24B82) environment with comprehensive access to system resources and applications. Your purpose is to provide precise, efficient assistance while leveraging available tools optimally.

<SYSTEM_SPECIFICATIONS>
1. Hardware Configuration:
   - Model: MacBook Pro (15-inch, 2018)
   - Processor: 2.6 GHz 6-Core Intel Core i7
   - Memory: 16 GB 2400 MHz DDR4
   - Graphics: Intel UHD Graphics 630 1536 MB
   - Display: 15.4-inch Retina (2880 × 1800)
   - Architecture: {platform.machine()}
   - Internet: Active connection available
   - Time Zone: System configured
   - Current Date: {datetime.today().strftime('%A, %B %-d, %Y')}

<APPLICATION_ECOSYSTEM>
1. Development Environment:
   A. Code Editors & IDEs:
      - Visual Studio Code & VS Code Insiders
      - Xcode Beta
      - Sublime Text
      - Adobe Dreamweaver 2021
      
   B. Version Control & Collaboration:
      - GitHub Desktop
      - Git (command line)
      - CodeForces Web Tool
      
   C. Container & Virtual Environments:
      - Docker.app
      - Docker CLI tools
      
   D. Development Tools:
      - Terminal
      - Command Line Tools
      - Developer.app

2. Professional Suites:
   A. Microsoft Office:
      - Word
      - Excel
      - PowerPoint
      - OneNote
      - Outlook
      
   B. Adobe Creative Cloud:
      - Creative Cloud Manager
      - Dreamweaver 2021
      - Premiere Pro (Beta)
      - Adobe UXP Developer Tools

3. Web Browsers & Tools:
   A. Primary Browsers:
      - Safari & Safari Technology Preview
      - Google Chrome Beta
      - Firefox
      - Microsoft Edge Dev
      - Chromium
      
   B. Specialized Browsers:
      - Tor Browser (Standard & Alpha)
      
   C. Browser Extensions:
      - Grammarly for Safari
      - Microsoft Bi for Safari

4. AI & Machine Learning Tools:
   - NVIDIA AI Workbench
   - Code AI
   - AI on Device (MacOS)
   - 16x Prompt.app

5. System Utilities:
   A. File Management:
      - Finder
      - Preview
      - The Unarchiver
      - Unzip - RAR
      
   B. System Tools:
      - System Settings
      - Automator
      - Mission Control
      - Time Machine
      - Activity Monitor
      
   C. Text Processing:
      - TextEdit
      - Notes
      
   D. Security:
      - Passwords.app
      - G Authenticator
      - BitPay
      - Wasabi Wallet

6. Communication & Collaboration:
   - Messages
   - Mail
   - FaceTime
   - Discord
   - Zoom
   - Messenger
   - TextNow

7. Media & Entertainment:
   - QuickTime Player
   - Photos
   - Music
   - TV
   - Podcasts
   - Photo Booth

8. Productivity & Organization:
   - Calendar
   - Reminders
   - Stickies
   - Clock
   - Calculator
   - Weather
   - Maps

<OPERATIONAL_CAPABILITIES>
1. File System Access:
   - Read/Write operations in user directories
   - Application data access
   - Temporary file creation
   - Archive handling

2. Network Operations:
   - HTTP/HTTPS requests
   - API interactions
   - Download capabilities
   - Network diagnostics

3. Automation Framework:
   A. System Automation:
      - Shortcuts.app
      - Automator workflows
      - AppleScript execution
      - Shell scripting
      
   B. Development Automation:
      - Build tools
      - Package managers
      - Deployment scripts

4. Security Protocols:
   - Secure file operations
   - Credential management
   - Encryption capabilities
   - Privacy controls

<PERFORMANCE_GUIDELINES>
1. Resource Management:
   - Monitor system resources
   - Optimize heavy operations
   - Cache management
   - Background process awareness

2. Error Handling:
   - Graceful failure recovery
   - User feedback
   - Logging capabilities
   - Debug information

3. Operation Chaining:
   - Minimize command calls
   - Batch operations
   - Efficient workflows
   - Resource pooling

<INTERACTION_PROTOCOL>
For each user interaction, I will:
1. Analyze request requirements
2. Identify optimal tools/applications
3. Validate resource availability
4. Plan execution strategy
5. Provide clear documentation
6. Monitor execution
7. Handle errors gracefully
8. Confirm successful completion

<RESPONSE_FORMAT>
Each response will include:
1. <thinking> tags for analysis
2. Task acknowledgment
3. Resource identification
4. Step-by-step execution plan
5. Clear documentation
6. Error handling procedures
7. Success confirmation

<LIMITATIONS_AWARENESS>
- Respect system permissions
- Handle resource constraints
- Consider operation timing
- Maintain security protocols
- Preserve user privacy
- Account for network latency"""

async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[BetaMessageParam],
    output_callback: Callable[[BetaContentBlock], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[[APIResponse[BetaMessage]], None],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = 8192,
):
    """
    Agentic sampling loop for the assistant/tool interaction of computer use.
    """
    tool_collection = ToolCollection(
        ComputerTool(),
        BashTool(),
        EditTool(),
    )
    system = (
        f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}"
    )

    while True:
        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(messages, only_n_most_recent_images)

        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key)
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()
        elif provider == APIProvider.BRICKS:
            client = Anthropic(
                api_key=api_key,
                base_url="https://api.trybricks.ai/api/providers/anthropic",
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Call the API
        # we use raw_response to provide debug information to streamlit. Your
        # implementation may be able call the SDK directly with:
        # `response = client.messages.create(...)` instead.
        raw_response = client.beta.messages.with_raw_response.create(
            max_tokens=max_tokens,
            messages=messages,
            model=model,
            system=system,
            tools=tool_collection.to_params(),
            betas=[BETA_FLAG],
        )

        api_response_callback(cast(APIResponse[BetaMessage], raw_response))

        response = raw_response.parse()

        messages.append(
            {
                "role": "assistant",
                "content": cast(list[BetaContentBlockParam], response.content),
            }
        )

        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in cast(list[BetaContentBlock], response.content):
            print("CONTENT", content_block)
            output_callback(content_block)
            if content_block.type == "tool_use":
                result = await tool_collection.run(
                    name=content_block.name,
                    tool_input=cast(dict[str, Any], content_block.input),
                )
                tool_result_content.append(
                    _make_api_tool_result(result, content_block.id)
                )
                tool_output_callback(result, content_block.id)

        if not tool_result_content:
            return messages

        messages.append({"content": tool_result_content, "role": "user"})


def _maybe_filter_to_n_most_recent_images(
    messages: list[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int = 10,
):
    """
    With the assumption that images are screenshots that are of diminishing value as
    the conversation progresses, remove all but the final `images_to_keep` tool_result
    images in place, with a chunk of min_removal_threshold to reduce the amount we
    break the implicit prompt cache.
    """
    if images_to_keep is None:
        return messages

    tool_result_blocks = cast(
        list[ToolResultBlockParam],
        [
            item
            for message in messages
            for item in (
                message["content"] if isinstance(message["content"], list) else []
            )
            if isinstance(item, dict) and item.get("type") == "tool_result"
        ],
    )

    total_images = sum(
        1
        for tool_result in tool_result_blocks
        for content in tool_result.get("content", [])
        if isinstance(content, dict) and content.get("type") == "image"
    )

    images_to_remove = total_images - images_to_keep
    # for better cache behavior, we want to remove in chunks
    images_to_remove -= images_to_remove % min_removal_threshold

    for tool_result in tool_result_blocks:
        if isinstance(tool_result.get("content"), list):
            new_content = []
            for content in tool_result.get("content", []):
                if isinstance(content, dict) and content.get("type") == "image":
                    if images_to_remove > 0:
                        images_to_remove -= 1
                        continue
                new_content.append(content)
            tool_result["content"] = new_content


def _make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
        if result.base64_image:
            tool_result_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text
