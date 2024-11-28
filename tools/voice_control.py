from AppKit import NSSpeechSynthesizer, NSSpeechRecognizer
from typing import Callable, Optional

class VoiceControl:
    """Voice control and speech synthesis integration"""
    
    def __init__(self):
        self.synthesizer = NSSpeechSynthesizer.alloc().init()
        self.recognizer = NSSpeechRecognizer.alloc().init()
        self.commands = {}
        
    def speak(self, text: str, voice: str = None):
        """Speak text using macOS speech synthesis"""
        if voice:
            self.synthesizer.setVoice_(voice)
        self.synthesizer.startSpeakingString_(text)
        
    def register_command(self, phrase: str, callback: Callable):
        """Register voice command with callback"""
        self.commands[phrase] = callback
        self.recognizer.addCommand_(phrase)
        
    def start_listening(self):
        """Start listening for voice commands"""
        self.recognizer.setDelegate_(self)
        self.recognizer.startListening()
        
    def stop_listening(self):
        """Stop listening for voice commands"""
        self.recognizer.stopListening()
        
    def speechRecognizer_didRecognizeCommand_(self, recognizer, command):
        """Handle recognized voice command"""
        if command in self.commands:
            self.commands[command]() 