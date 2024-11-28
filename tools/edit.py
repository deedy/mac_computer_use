from collections import defaultdict
from pathlib import Path
from typing import Literal, get_args

from .base_tool import BaseTool, ToolResult

Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]
SNIPPET_LINES: int = 4


class EditTool(BaseTool):
    """
    A filesystem editor tool that allows the user to view, create, and edit files.
    """

    def __init__(self):
        super().__init__()
        self._file_history = defaultdict(list)

    async def execute(self, command: str, **kwargs) -> ToolResult:
        """Execute edit commands"""
        try:
            # Parse command
            parts = command.split()
            action = parts[0].lower()
            
            if action == "view":
                if len(parts) < 2:
                    return ToolResult(success=False, error="File path required")
                path = Path(parts[1])
                return await self._view_file(path)
                
            if action == "create":
                if len(parts) < 3:
                    return ToolResult(success=False, error="File path and content required")
                path = Path(parts[1])
                content = " ".join(parts[2:])
                return await self._create_file(path, content)
                
            if action == "edit":
                if len(parts) < 4:
                    return ToolResult(success=False, error="File path, old text and new text required")
                path = Path(parts[1])
                old_text = parts[2]
                new_text = parts[3]
                return await self._edit_file(path, old_text, new_text)
                
            return ToolResult(success=False, error=f"Unknown action: {action}")
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _view_file(self, path: Path) -> ToolResult:
        """View file contents"""
        try:
            if not path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")
                
            if path.is_dir():
                files = list(path.glob("*"))
                return ToolResult(
                    success=True,
                    output="\n".join(str(f) for f in files)
                )
                
            content = path.read_text()
            return ToolResult(success=True, output=content)
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _create_file(self, path: Path, content: str) -> ToolResult:
        """Create a new file"""
        try:
            if path.exists():
                return ToolResult(success=False, error=f"File already exists: {path}")
                
            path.write_text(content)
            return ToolResult(success=True, output=f"Created file: {path}")
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _edit_file(self, path: Path, old_text: str, new_text: str) -> ToolResult:
        """Edit file contents"""
        try:
            if not path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")
                
            content = path.read_text()
            
            # Save backup
            self._file_history[path].append(content)
            
            # Replace text
            new_content = content.replace(old_text, new_text)
            path.write_text(new_content)
            
            return ToolResult(success=True, output=f"Edited file: {path}")
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def cleanup(self):
        """Cleanup resources"""
        # Nothing to clean up
        pass
