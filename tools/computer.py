import asyncio
import base64
import os
import shlex
import pyautogui
import keyboard
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypedDict, cast, get_args
from uuid import uuid4

from anthropic.types.beta import BetaToolComputerUse20241022Param, BetaToolUnionParam

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run

OUTPUT_DIR = "/tmp/outputs"

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

Action_20241022 = Literal[
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

Action_20250124 = (
    Action_20241022
    | Literal[
        "left_mouse_down",
        "left_mouse_up",
        "scroll",
        "hold_key",
        "wait",
        "triple_click",
    ]
)

ScrollDirection = Literal["up", "down", "left", "right"]


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

CLICK_BUTTONS = {
    "left_click": 1,
    "right_click": 3,
    "middle_click": 2,
    "double_click": "--repeat 2 --delay 10 1",
    "triple_click": "--repeat 3 --delay 10 1",
}


class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"


class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: int | None


def chunks(s: str, chunk_size: int) -> list[str]:
    return [s[i : i + chunk_size] for i in range(0, len(s), chunk_size)]


class BaseComputerTool:
    """
    A tool that allows the agent to interact with the screen, keyboard, and mouse of the current macOS computer.
    The tool parameters are defined by Anthropic and are not editable.
    Requires cliclick to be installed: brew install cliclick
    """

    name: Literal["computer"] = "computer"
    width: int
    height: int
    display_num: int | None

    _screenshot_delay = 1.0  # macOS is generally faster than X11
    _scaling_enabled = True

    @property
    def options(self) -> ComputerToolOptions:
        width, height = self.scale_coordinates(
            ScalingSource.COMPUTER, self.width, self.height
        )
        return {
            "display_width_px": width,
            "display_height_px": height,
            "display_number": self.display_num,
        }

    def __init__(self):
        super().__init__()

        self.width, self.height = pyautogui.size()
        assert self.width and self.height, "WIDTH, HEIGHT must be set"
        self.display_num = None  # macOS doesn't use X11 display numbers

    async def __call__(
        self,
        *,
        action: Action_20241022,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        print("Action: ", action, text, coordinate)
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                raise ToolError(f"coordinate is required for {action}")
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ToolError(f"{coordinate} must be a tuple of length 2")
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

            x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])

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
                raise ToolError(output=f"{text} must be a string")

            if action == "key":
                # Convert common key names to pyautogui format
                key_map = {
                    "Return": "enter",
                    "space": "space",
                    "Tab": "tab",
                    "Left": "left",
                    "Right": "right",
                    "Up": "up",
                    "Down": "down",
                    "Escape": "esc",
                    "command": "command",
                    "cmd": "command",
                    "alt": "alt",
                    "shift": "shift",
                    "ctrl": "ctrl"
                }

                try:
                    if "+" in text:
                        # Handle combinations like "ctrl+c"
                        keys = text.split("+")
                        mapped_keys = [key_map.get(k.strip(), k.strip()) for k in keys]
                        await asyncio.get_event_loop().run_in_executor(
                            None, keyboard.press_and_release, '+'.join(mapped_keys)
                        )
                    else:
                        # Handle single keys
                        mapped_key = key_map.get(text, text)
                        await asyncio.get_event_loop().run_in_executor(
                            None, keyboard.press_and_release, mapped_key
                        )

                    return ToolResult(output=f"Pressed key: {text}", error=None, base64_image=None)

                except Exception as e:
                    return ToolResult(output=None, error=str(e), base64_image=None)
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
                import pdb; pdb.set_trace()
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
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"screenshot_{uuid4().hex}.png"

        # Use macOS native screencapture
        screenshot_cmd = f"screencapture -x {path}"
        result = await self.shell(screenshot_cmd, take_screenshot=False)

        if self._scaling_enabled:
            x, y = SCALE_DESTINATION['width'], SCALE_DESTINATION['height']
            await self.shell(
                f"sips -z {y} {x} {path}",  # sips is macOS native image processor
                take_screenshot=False
            )

        if path.exists():
            return result.replace(
                base64_image=base64.b64encode(path.read_bytes()).decode()
            )
        raise ToolError(f"Failed to take screenshot: {result.error}")

    async def shell(self, command: str, take_screenshot=False) -> ToolResult:
        """Run a shell command and return the output, error, and optionally a screenshot."""
        _, stdout, stderr = await run(command)
        base64_image = None

        if take_screenshot:
            # delay to let things settle before taking a screenshot
            await asyncio.sleep(self._screenshot_delay)
            base64_image = (await self.screenshot()).base64_image

        return ToolResult(output=stdout, error=stderr, base64_image=base64_image)

    def scale_coordinates(self, source: ScalingSource, x: int, y: int) -> tuple[int, int]:
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
        x_scaling_factor = SCALE_DESTINATION['width'] / self.width
        y_scaling_factor = SCALE_DESTINATION['height'] / self.height

        if source == ScalingSource.API:
            # Scale up from SCALE_DESTINATION to original resolution
            if x > SCALE_DESTINATION['width'] or y > SCALE_DESTINATION['height']:
                raise ToolError(f"Coordinates {x}, {y} are out of bounds for {SCALE_DESTINATION['width']}x{SCALE_DESTINATION['height']}")
            return round(x / x_scaling_factor), round(y / y_scaling_factor)
        else:
            # Scale down from original resolution to SCALE_DESTINATION
            return round(x * x_scaling_factor), round(y * y_scaling_factor)

class ComputerTool20241022(BaseComputerTool, BaseAnthropicTool):
    api_type: Literal["computer_20241022"] = "computer_20241022"

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

class ComputerTool20250124(BaseComputerTool, BaseAnthropicTool):
    api_type: Literal["computer_20250124"] = "computer_20250124"

    def to_params(self):
        return cast(
            BetaToolUnionParam,
            {"name": self.name, "type": self.api_type, **self.options},
        )

    async def __call__(
        self,
        *,
        action: Action_20250124,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        scroll_direction: ScrollDirection | None = None,
        scroll_amount: int | None = None,
        duration: int | float | None = None,
        key: str | None = None,
        **kwargs,
    ):
        if action in ("left_mouse_down", "left_mouse_up"):
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action=}.")
            click_cmd = {
                "left_mouse_down": "dd:.",  # Press down
                "left_mouse_up": "du:.",    # Release up
            }[action]
            return await self.shell(f"cliclick {click_cmd}")

        if action == "scroll":
            if scroll_direction is None or scroll_direction not in get_args(
                ScrollDirection
            ):
                raise ToolError(
                    f"{scroll_direction=} must be 'up', 'down', 'left', or 'right'"
                )
            if not isinstance(scroll_amount, int) or scroll_amount < 0:
                raise ToolError(f"{scroll_amount=} must be a non-negative int")

            if coordinate is not None:
                x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])
                await self.shell(f"cliclick m:{x},{y}")

            # Map scroll directions to cliclick scroll commands
            scroll_cmd = {
                "up": "kp:page-up",
                "down": "kp:page-down",
                "left": "kp:arrow-left",
                "right": "kp:arrow-right"
            }[scroll_direction]

            commands = []
            if text:
                commands.append(f"cliclick kd:{text}")
            for _ in range(scroll_amount):
                commands.append(f"cliclick {scroll_cmd}")
            if text:
                commands.append(f"cliclick ku:{text}")

            for cmd in commands:
                await self.shell(cmd)
            return await self.screenshot()

        if action in ("hold_key", "wait"):
            if duration is None or not isinstance(duration, (int, float)):
                raise ToolError(f"{duration=} must be a number")
            if duration < 0:
                raise ToolError(f"{duration=} must be non-negative")
            if duration > 100:
                raise ToolError(f"{duration=} is too long.")

            if action == "hold_key":
                if text is None:
                    raise ToolError(f"text is required for {action}")
                await self.shell(f"cliclick kd:{text}")
                await asyncio.sleep(duration)
                await self.shell(f"cliclick ku:{text}")
                return await self.screenshot()

            if action == "wait":
                await asyncio.sleep(duration)
                return await self.screenshot()

        if action in (
            "left_click",
            "right_click",
            "double_click",
            "triple_click",
            "middle_click",
        ):
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")

            if coordinate is not None:
                x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])
                await self.shell(f"cliclick m:{x},{y}")

            click_cmd = {
                "left_click": "c:.",
                "right_click": "rc:.",
                "middle_click": "mc:.",
                "double_click": "dc:.",
                "triple_click": "tc:.",  # Note: cliclick may not support triple click natively
            }[action]

            if key:
                await self.shell(f"cliclick kd:{key}")
            result = await self.shell(f"cliclick {click_cmd}")
            if key:
                await self.shell(f"cliclick ku:{key}")
            return result

        return await super().__call__(
            action=action, text=text, coordinate=coordinate, key=key, **kwargs
        )