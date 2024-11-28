class PowerManager:
    """Advanced power management"""
    
    async def prevent_sleep(self, duration: int = None):
        """Prevent system sleep"""
        if duration:
            await self.shell(f"caffeinate -t {duration}")
        else:
            await self.shell("caffeinate -d")
            
    async def optimize_display(self):
        """Configure display for performance"""
        await self.shell("""
            defaults write NSGlobalDomain NSWindowResizeTime .001
            defaults write com.apple.dock autohide-time-modifier -float 0.15
            defaults write com.apple.dock autohide-delay -float 0
        """) 