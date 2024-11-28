import re
import subprocess
from typing import Set, Dict, Optional, Any
from pathlib import Path
from .config import settings
from .logging_config import logger
from typing import Optional
import logging
from dataclasses import dataclass


class SecurityError(Exception):
    """Base class for security-related errors"""
    pass

@dataclass
class SecurityContext:
    """Security context for operations"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    permissions: list[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []

class SecurityManager:
    """Security manager with enhanced macOS protections.
    
    This class provides security features specifically designed for macOS:
    - Command validation and sanitization
    - Path traversal protection
    - Sandboxed command execution
    - Input validation
    """
    
    # List of allowed commands and their parameters
    ALLOWED_COMMANDS: Set[str] = {
        'ls', 'cd', 'pwd', 'echo', 'cat',
        'grep', 'find', 'head', 'tail', 'wc',
        'mkdir', 'touch', 'rm', 'cp', 'mv',
        'open', 'pbcopy', 'pbpaste', 'screencapture'
    }
    
    # Dangerous patterns in commands
    DANGEROUS_PATTERNS: Set[str] = {
        r'rm\s+-rf\s+[/~]',  # Dangerous rm commands
        r'>\s*/dev/',        # Writing to device files
        r'mkfifo',           # Creating named pipes
        r'chmod\s+777',      # Overly permissive chmod
        r'sudo',             # Sudo commands
        r';.*&&',            # Command chaining
        r'\|\s*bash',        # Piping to bash
        r'curl.*\|\s*bash',  # Downloading and executing
    }
    
    def __init__(self):
        self.context = SecurityContext()
        
    @classmethod
    def validate_command(cls, command: str) -> bool:
        """Validate if a command is allowed and safe.
        
        Args:
            command: The command string to validate
            
        Returns:
            bool: True if command is safe, False otherwise
        """
        # Split command and get the base command
        parts = command.strip().split()
        if not parts:
            return False
            
        base_command = parts[0]
        
        # Check if command is in allowed list
        if base_command not in cls.ALLOWED_COMMANDS:
            logger.warning(f"Command not in allowed list: {base_command}")
            return False
            
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                msg = f"Dangerous pattern detected in command: {command}"
                logger.warning(msg)
                return False
                
        return True
    
    @classmethod
    def validate_path(cls, path: str) -> bool:
        """Validate if a path is safe to access.
        
        Args:
            path: The path to validate
            
        Returns:
            bool: True if path is safe, False otherwise
        """
        try:
            # Convert to absolute path
            abs_path = Path(path).resolve()
            
            # Check if path is within workspace
            workspace_path = Path.cwd().resolve()
            if not abs_path.is_relative_to(workspace_path):
                logger.warning(f"Path outside workspace: {path}")
                return False
                
            # Check for symbolic links
            if abs_path.is_symlink():
                logger.warning(f"Symbolic link detected: {path}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False
    
    @classmethod
    def sanitize_input(cls, input_str: str) -> str:
        """Sanitize input string to prevent injection attacks.
        
        Args:
            input_str: The input string to sanitize
            
        Returns:
            str: The sanitized string
        """
        # Remove shell special characters
        sanitized = re.sub(r'[;&|`$]', '', input_str)
        # Remove path traversal attempts
        sanitized = re.sub(r'\.\.[/\\]', '', sanitized)
        # Remove null bytes
        sanitized = sanitized.replace('\0', '')
        return sanitized
    
    @classmethod
    def run_sandboxed_command(
        cls, command: str
    ) -> subprocess.CompletedProcess[str]:
        """Run a command in a sandboxed environment.
        
        Args:
            command: The command to execute
            
        Returns:
            CompletedProcess: The command execution result
            
        Raises:
            SecurityError: If sandbox is disabled or command is not allowed
        """
        if not settings.SANDBOX_ENABLED:
            raise SecurityError("Sandbox is disabled")
            
        if not cls.validate_command(command):
            raise SecurityError(f"Command not allowed: {command}")
            
        try:
            # Set up a clean environment
            env: Dict[str, str] = {
                'PATH': '/usr/local/bin:/usr/bin:/bin',
                'HOME': str(Path.home()),
                'LANG': 'en_US.UTF-8',
            }
            
            # Run command with restrictions
            result = subprocess.run(
                command,
                shell=True,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                check=True,  # Raise CalledProcessError on non-zero exit
            )
            
            logger.info(f"Command executed successfully: {command}")
            return result
            
        except subprocess.TimeoutExpired:
            msg = f"Command timed out: {command}"
            logger.error(msg)
            raise SecurityError(msg)
        except subprocess.CalledProcessError as e:
            msg = f"Command failed with exit code {e.returncode}: {command}"
            logger.error(msg)
            raise SecurityError(msg) from e
        except Exception as e:
            msg = f"Command execution error: {e}"
            logger.error(msg)
            raise SecurityError(msg) from e
    
    async def check_permissions(self) -> bool:
        """Check if current operation is allowed"""
        try:
            # For now, just check if accessibility is enabled
            import Quartz
            if not Quartz.AXIsProcessTrusted():
                raise SecurityError(
                    "Accessibility access not enabled. Please enable in "
                    "System Settings > Privacy & Security > Accessibility"
                )
            return True
            
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            raise SecurityError(str(e))
            
    def set_context(self, context: SecurityContext) -> None:
        """Set security context"""
        self.context = context
    
    def sanitize_input(self, value: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Basic sanitization - remove dangerous characters
        dangerous_chars = [';', '&&', '|', '`', '$', '(', ')', '{', '}']
        sanitized = value
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and presence."""
        if not api_key:
            return False
        # Basic validation - check if key looks like a valid format
        return len(api_key) >= 32 and api_key.isprintable()
    
    async def cleanup(self) -> None:
        """Cleanup security resources."""
        self._permissions = {}