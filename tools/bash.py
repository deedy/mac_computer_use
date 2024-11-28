import asyncio
import os
import pty
import select
import subprocess
import termios
import tty
from typing import Optional

from loguru import logger

from .base_tool import BaseTool, ToolResult


class BashTool(BaseTool):
    """Execute bash commands in an interactive shell."""

    def __init__(self):
        super().__init__()
        self._process = None
        self._master_fd = None
        self._initialize_shell()

    def _initialize_shell(self):
        """Initialize interactive shell."""
        try:
            # Create pseudo-terminal
            master_fd, slave_fd = pty.openpty()
            self._master_fd = master_fd

            # Set terminal attributes
            tty.setraw(slave_fd)

            # Start zsh process
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            
            self._process = subprocess.Popen(
                ["/bin/zsh"],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                env=env,
                start_new_session=True,
                universal_newlines=True
            )

            os.close(slave_fd)

        except Exception as e:
            logger.error(f"Failed to initialize shell: {e}")
            raise

    async def execute(self, command: str, **kwargs) -> ToolResult:
        """Execute a bash command."""
        try:
            if not self._process or self._process.poll() is not None:
                self._initialize_shell()

            # Write command to master fd
            wrapped_command = f"{command}\necho $?\n"
            os.write(self._master_fd, wrapped_command.encode())

            # Read output asynchronously
            output = []
            exit_code = None
            
            while True:
                # Use asyncio.get_event_loop().run_in_executor for blocking operations
                loop = asyncio.get_event_loop()
                ready = await loop.run_in_executor(None, lambda: select.select([self._master_fd], [], [], 0.1)[0])
                
                if not ready:
                    break
                    
                try:
                    data = await loop.run_in_executor(None, lambda: os.read(self._master_fd, 1024).decode())
                    output.append(data)
                    
                    # Check for exit code
                    if data.strip().isdigit():
                        exit_code = int(data.strip())
                        break
                except OSError:
                    break

            output_str = "".join(output)
            
            if exit_code == 0:
                return ToolResult(success=True, output=output_str)
            else:
                return ToolResult(success=False, error=f"Command failed with exit code {exit_code}: {output_str}")

        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return ToolResult(success=False, error=str(e))

    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                self._process.wait(timeout=1)
            if self._master_fd is not None:
                os.close(self._master_fd)
        except Exception as e:
            logger.error(f"Error cleaning up BashTool: {e}")

    def __del__(self):
        """Cleanup resources on deletion."""
        try:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                self._process.wait(timeout=1)
            if self._master_fd is not None:
                os.close(self._master_fd)
        except Exception as e:
            logger.error(f"Error cleaning up BashTool: {e}")
