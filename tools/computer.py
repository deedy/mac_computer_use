import asyncio
import base64
import os
import shlex
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypedDict
from uuid import uuid4
from io import BytesIO
from PIL import Image

from anthropic.types.beta import BetaToolComputerUse20241022Param

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run

# Constants
OUTPUT_DIR = "/tmp/outputs"
TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

# Check if we're running in a codespace environment
IS_CODESPACE = os.environ.get("CODESPACES") == "true"

Action = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
]


class Resolution(TypedDict):
    width: int
    height: int


# sizes above XGA/WXGA are not recommended (see README.md)
# scale down to one of these targets if ComputerTool._scaling_enabled is set
MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),  # 4:3
    "WXGA": Resolution(width=1280, height=800),  # 16:10
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9
}
SCALE_DESTINATION = MAX_SCALING_TARGETS["FWXGA"]


class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"


class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: int | None


def chunks(s: str, chunk_size: int) -> list[str]:
    return [s[i : i + chunk_size] for i in range(0, len(s), chunk_size)]


def compress_image(image_data: bytes, max_size: int = MAX_IMAGE_SIZE) -> bytes:
    """Compress image data until it's under the specified max size."""
    img = Image.open(BytesIO(image_data))
    quality = 95
    output = BytesIO()

    while True:
        output.seek(0)
        output.truncate()
        img.save(output, format="PNG", optimize=True, quality=quality)
        size = output.tell()

        if size <= max_size or quality <= 5:
            break

        quality -= 5

    return output.getvalue()


class ComputerTool(BaseAnthropicTool):
    """
    A tool that allows the agent to interact with the screen, keyboard, and mouse.
    The tool parameters are defined by Anthropic and are not editable.
    """

    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20241022"] = "computer_20241022"
    width: int
    height: int
    display_num: int | None

    _screenshot_delay = 1.0
    _scaling_enabled = True

    @property
    def options(self) -> ComputerToolOptions:
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
            "display_number": self.display_num,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self):
        super().__init__()

        # Set default dimensions
        self.width = int(os.environ.get("WIDTH", 1366))
        self.height = int(os.environ.get("HEIGHT", 768))
        self.display_num = None

        if IS_CODESPACE:
            print("Running in codespace environment - some features may be limited")

    async def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        print("Action: ", action, text, coordinate)

        if IS_CODESPACE:
            return ToolResult(
                error="This action is not supported in codespace environment. This tool is designed for macOS systems."
            )

        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                raise ToolError(f"coordinate is required for {action}")
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ToolError(f"{coordinate} must be a tuple of length 2")
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

            x, y = self.scale_coordinates(
                ScalingSource.API, coordinate[0], coordinate[1]
            )

            if action == "mouse_move":
                return await self.shell(f"cliclick m:{x},{y}")
            elif action == "left_click_drag":
                return await self.shell(f"cliclick dd:{x},{y}")

        if action in ("key", "type"):
            if text is None:
                raise ToolError(f"text is required for {action}")
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action}")
            if not isinstance(text, str):
                raise ToolError("Text input must be a string")

            if action == "key":
                # Use cliclick for key presses
                key_map = {
                    "Return": "kp:return",
                    "space": "kp:space",
                    "Tab": "kp:tab",
                    "Left": "kp:arrow-left",
                    "Right": "kp:arrow-right",
                    "Up": "kp:arrow-up",
                    "Down": "kp:arrow-down",
                    "Escape": "kp:esc",
                    "command": "kp:cmd",
                    "cmd": "kp:cmd",
                    "alt": "kp:alt",
                    "shift": "kp:shift",
                    "ctrl": "kp:ctrl",
                }

                try:
                    if "+" in text:
                        # Handle combinations like "ctrl+c"
                        keys = text.split("+")
                        mapped_keys = [
                            key_map.get(k.strip(), f"kp:{k.strip()}") for k in keys
                        ]
                        cmd = "cliclick " + " ".join(mapped_keys)
                    else:
                        # Handle single keys
                        mapped_key = key_map.get(text, f"kp:{text}")
                        cmd = f"cliclick {mapped_key}"

                    return await self.shell(cmd)

                except Exception as e:
                    return ToolResult(error=str(e))

            elif action == "type":
                results: list[ToolResult] = []
                for chunk in chunks(text, TYPING_GROUP_SIZE):
                    cmd = f"cliclick w:{TYPING_DELAY_MS} t:{shlex.quote(chunk)}"
                    results.append(await self.shell(cmd, take_screenshot=False))
                screenshot_base64 = (await self.screenshot()).base64_image
                return ToolResult(
                    output="".join(result.output or "" for result in results),
                    error="".join(result.error or "" for result in results),
                    base64_image=screenshot_base64,
                )

        if action in (
            "left_click",
            "right_click",
            "double_click",
            "middle_click",
            "screenshot",
            "cursor_position",
        ):
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action}")

            if action == "screenshot":
                return await self.screenshot()
            elif action == "cursor_position":
                result = await self.shell(
                    "cliclick p",
                    take_screenshot=False,
                )
                if result.output:
                    x, y = map(int, result.output.strip().split(","))
                    x, y = self.scale_coordinates(ScalingSource.COMPUTER, x, y)
                    return result.replace(output=f"X={x},Y={y}")
                return result
            else:
                click_cmd = {
                    "left_click": "c:.",
                    "right_click": "rc:.",
                    "middle_click": "mc:.",
                    "double_click": "dc:.",
                }[action]
                return await self.shell(f"cliclick {click_cmd}")

        raise ToolError(f"Invalid action: {action}")

    async def screenshot(self):
        """Take a screenshot of the current screen and return the base64 encoded image."""
        if IS_CODESPACE:
            return ToolResult(
                error="Screenshot functionality is not available in codespace environment"
            )

        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"screenshot_{uuid4().hex}.png"

        try:
            # Use screencapture on macOS
            result = await self.shell(f"screencapture -x {path}")
            if result.error:
                return result

            if path.exists():
                # Read the image and compress if necessary
                image_data = path.read_bytes()
                if len(image_data) > MAX_IMAGE_SIZE:
                    image_data = compress_image(image_data)

                return ToolResult(base64_image=base64.b64encode(image_data).decode())
            return ToolResult(error="Screenshot file was not created")
        except Exception as e:
            return ToolResult(error=f"Failed to take screenshot: {str(e)}")
        finally:
            # Clean up the temporary file
            if path.exists():
                path.unlink()

    async def shell(self, command: str, take_screenshot=False) -> ToolResult:
        """Run a shell command and return the output, error, and optionally a screenshot."""
        _, stdout, stderr = await run(command)
        base64_image = None

        if take_screenshot:
            # delay to let things settle before taking a screenshot
            await asyncio.sleep(self._screenshot_delay)
            base64_image = (await self.screenshot()).base64_image

        return ToolResult(output=stdout, error=stderr, base64_image=base64_image)

    def scale_coordinates(
        self, source: ScalingSource, x: int, y: int
    ) -> tuple[int, int]:
        """
        Scale coordinates between original resolution and target resolution (SCALE_DESTINATION).

        Args:
            source: ScalingSource.API for scaling up from SCALE_DESTINATION to original resolution
                   or ScalingSource.COMPUTER for scaling down from original to SCALE_DESTINATION
            x, y: Coordinates to scale

        Returns:
            Tuple of scaled (x, y) coordinates
        """
        if not self._scaling_enabled:
            return x, y

        # Calculate scaling factors
        x_scaling_factor = SCALE_DESTINATION["width"] / self.width
        y_scaling_factor = SCALE_DESTINATION["height"] / self.height

        if source == ScalingSource.API:
            # Scale up from SCALE_DESTINATION to original resolution
            if x > SCALE_DESTINATION["width"] or y > SCALE_DESTINATION["height"]:
                raise ToolError(
                    f"Coordinates {x}, {y} are out of bounds for {SCALE_DESTINATION['width']}x{SCALE_DESTINATION['height']}"
                )
            return round(x / x_scaling_factor), round(y / y_scaling_factor)
        else:
            # Scale down from original resolution to SCALE_DESTINATION
            return round(x * x_scaling_factor), round(y * y_scaling_factor)
