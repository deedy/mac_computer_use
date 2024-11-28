import Quartz
from AppKit import NSURL
from typing import List

class QuickLook:
    """Integration with macOS Quick Look"""
    
    def preview_files(self, file_paths: List[str]):
        """Show Quick Look preview of files"""
        urls = [NSURL.fileURLWithPath_(path) for path in file_paths]
        panel = Quartz.QLPreviewPanel.sharedPreviewPanel()
        
        # Set up preview panel
        panel.setDataSource_(self)
        panel.makeKeyAndOrderFront_(None)
        
    def numberOfPreviewItemsInPreviewPanel_(self, panel) -> int:
        """Required QLPreviewPanelDataSource method"""
        return len(self.urls)
        
    def previewPanel_previewItemAtIndex_(self, panel, index) -> NSURL:
        """Required QLPreviewPanelDataSource method"""
        return self.urls[index] 