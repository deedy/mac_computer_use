from rich.console import Console
from rich.progress import Progress, SpinnerColumn
from rich.syntax import Syntax

class UIManager:
    """Enhanced terminal UI with Rich"""
    
    def __init__(self):
        self.console = Console()
        
    def show_code(self, code: str, language: str):
        """Show syntax-highlighted code"""
        syntax = Syntax(code, language, theme="monokai")
        self.console.print(syntax)
        
    async def with_progress(self, message: str):
        """Show progress spinner during operations"""
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            transient=True
        ) as progress:
            task = progress.add_task(message, total=None)
            yield progress, task 