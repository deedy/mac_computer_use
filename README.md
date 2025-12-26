# Anthropic Computer Use (for Mac)

[Anthropic Computer Use](https://github.com/anthropics/anthropic-quickstarts/blob/main/computer-use-demo/README.md) is a beta Anthropic feature which runs a Docker image with Ubuntu and controls it. This fork allows you to run it natively on macOS, providing direct system control through native macOS commands and utilities.

> [!CAUTION]
> This comes with obvious risks. The Anthropic agent can control everything on your Mac. Please be careful.
> Claude 4 models refuse to do unsafe things like purchase items or download illegal content.

## Supported Models

This project supports all three latest Claude 4.5 model families with computer use capabilities:

| Model | Best For | Model ID |
|-------|----------|----------|
| **Claude Opus 4.5** | Complex tasks, highest capability | `claude-opus-4-5-20251101` |
| **Claude Sonnet 4.5** (default) | Balanced performance & cost | `claude-sonnet-4-5-20250929` |
| **Claude Haiku 4.5** | Fast responses, cost-effective | `claude-haiku-4-5-20251001` |

Select your preferred model in the sidebar UI. The appropriate beta API and tool versions are automatically configured:
- Opus 4.5: `computer-use-2025-11-24` (with zoom capability)
- Sonnet/Haiku 4.5: `computer-use-2025-01-24`

Tool types used:
- `computer_20250124` - Screen, mouse, and keyboard control
- `bash_20250124` - Command line execution
- `text_editor_20250124` - File editing capabilities

## Features

- Native macOS GUI interaction (no Docker required)
- Screen capture using native macOS commands
- Keyboard and mouse control through cliclick
- Multiple LLM provider support (Anthropic, Bedrock, Vertex)
- Streamlit-based interface
- Automatic screen resolution scaling
- File system interaction and editing capabilities

## Prerequisites

- macOS Sonoma 15.7 or later
- Python 3.12+
- Homebrew (for installing additional dependencies)
- cliclick (`brew install cliclick`) - Required for mouse and keyboard control

## Setup Instructions

1. Clone the repository and navigate to it:

```bash
git clone https://github.com/deedy/mac_computer_use.git
cd mac_computer_use
```

2. Create and activate a virtual environment:

```bash
python3.12 -m venv venv
source venv/bin/activate
```

3. Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

4. Install Python requirements:

```bash
pip install -r requirements.txt
```

## Running the Demo

### Set up your environment and Anthropic API key

1. In a `.env` file add:

```
API_PROVIDER=anthropic
ANTHROPIC_API_KEY=<key>
WIDTH=800
HEIGHT=600
DISPLAY_NUM=1
```

Set the screen dimensions (recommended: stay within XGA/WXGA resolution), and put in your key from [Anthropic Console](https://console.anthropic.com/settings/keys).

2. Start the Streamlit app:

```bash
streamlit run streamlit.py
```

The interface will be available at http://localhost:8501

## Screen Size Considerations

We recommend using one of these resolutions for optimal performance:

-   XGA: 1024x768 (4:3)
-   WXGA: 1280x800 (16:10)
-   FWXGA: 1366x768 (~16:9)

Higher resolutions will be automatically scaled down to these targets to optimize model performance. You can set the resolution using environment variables:

```bash
export WIDTH=1024
export HEIGHT=768
streamlit run streamlit.py
```

> [!IMPORTANT]
> The Beta API used in this reference implementation is subject to change. Please refer to the [API release notes](https://docs.claude.com/en/release-notes/api) for the most up-to-date information.
>
> **Updated December 2025**: This project has been updated to use the `computer-use-2025-01-24` beta API with Claude Sonnet 4.5 as the default model.
