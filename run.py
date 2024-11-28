#!/usr/bin/env python3
"""Main entry point for Computer Use application."""

import os
import sys
import subprocess
import signal
from pathlib import Path
from loguru import logger


def setup_environment():
    """Setup environment variables and paths."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, str(project_root))
    
    # Setup logging
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "computer_use.log",
        rotation="100 MB",
        retention="10 days",
        level="INFO"
    )
    
    # Check for required environment variables
    required_vars = [
        "ANTHROPIC_API_KEY",
        "WIDTH",
        "HEIGHT"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        sys.exit(1)


def signal_handler(signum, frame):
    print("\nGracefully shutting down...")
    sys.exit(0)


def main():
    """Main entry point."""
    try:
        setup_environment()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Get the directory containing run.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the streamlit command
        cmd = [
            "streamlit", "run",
            os.path.join(current_dir, "streamlit.py"),
            "--server.address", "localhost",
            "--server.port", "8501"
        ]

        # Run streamlit with proper error handling
        try:
            subprocess.run(
                cmd,
                check=True,
                text=True,
                capture_output=False
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running Streamlit: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nGracefully shutting down...")
            sys.exit(0)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 