import subprocess
from pathlib import Path
from typing import List

class AutomatorWorkflow:
    """Integration with macOS Automator"""
    
    def __init__(self, workflow_dir: str = "~/Library/Services"):
        self.workflow_dir = Path(workflow_dir).expanduser()
        
    def create_service(self, name: str, script: str):
        """Create an Automator service workflow"""
        workflow_path = self.workflow_dir / f"{name}.workflow"
        workflow_path.mkdir(exist_ok=True)
        
        # Create Info.plist
        info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>NSServices</key>
            <array>
                <dict>
                    <key>NSMenuItem</key>
                    <dict>
                        <key>default</key>
                        <string>{name}</string>
                    </dict>
                    <key>NSMessage</key>
                    <string>runWorkflowAsService</string>
                </dict>
            </array>
        </dict>
        </plist>"""
        
        (workflow_path / "Contents/Info.plist").write_text(info_plist)
        (workflow_path / "Contents/document.wflow").write_text(script)
        
    def run_workflow(self, name: str, input_data: str = None):
        """Run an Automator workflow"""
        workflow_path = self.workflow_dir / f"{name}.workflow"
        cmd = ["automator", str(workflow_path)]
        
        if input_data:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            process.communicate(input_data.encode())
        else:
            subprocess.run(cmd) 