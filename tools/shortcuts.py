from Foundation import NSWorkspace, NSURL
import subprocess
from typing import List, Dict, Optional

class ShortcutsManager:
    """Manage macOS Shortcuts automation"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        
    def get_shortcuts(self) -> List[Dict]:
        """Get available shortcuts"""
        result = subprocess.run(['shortcuts', 'list'], capture_output=True, text=True)
        shortcuts = []
        
        for line in result.stdout.splitlines():
            if line.strip():
                name = line.strip()
                shortcuts.append({
                    'name': name,
                    'folder': self._get_shortcut_folder(name)
                })
        return shortcuts
        
    def run_shortcut(self, name: str, input_data: Optional[str] = None) -> str:
        """Run a specific shortcut"""
        cmd = ['shortcuts', 'run', name]
        if input_data:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            stdout, _ = process.communicate(input_data.encode())
            return stdout.decode()
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
            
    def create_shortcut(self, name: str, actions: List[Dict]) -> bool:
        """Create new shortcut from actions"""
        # Convert actions to Shortcuts format
        shortcut_data = {
            'WFWorkflowName': name,
            'WFWorkflowActions': actions
        }
        
        # Write shortcut file
        with open(f'/tmp/{name}.shortcut', 'w') as f:
            import json
            json.dump(shortcut_data, f)
            
        # Import shortcut
        result = subprocess.run(
            ['shortcuts', 'import', f'/tmp/{name}.shortcut'],
            capture_output=True
        )
        return result.returncode == 0 