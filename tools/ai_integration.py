class AIIntegration:
    """Handle AI model integrations"""
    
    async def use_chatgpt(self, prompt: str) -> ToolResult:
        """Use integrated ChatGPT without account creation"""
        # Use Apple's ChatGPT integration
        result = await self.shell(
            "osascript -e 'tell application \"System Events\" to use chatgpt'",
            input={"prompt": prompt}
        )
        
        # Apply privacy protections
        return self.apply_privacy_protections(result) 