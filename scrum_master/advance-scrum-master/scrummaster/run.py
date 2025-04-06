#!/usr/bin/env python
"""
Runner script to launch either the CLI or API version of the Scrum Master Bot.
"""

import argparse
import sys
import os

def main():
    """Main entry point that parses command line args and runs the selected interface"""
    
    parser = argparse.ArgumentParser(
        description="Scrum Master Bot - A simple NLP-powered assistant for daily standups"
    )
    
    parser.add_argument(
        "--interface", "-i",
        choices=["cli", "api"],
        default="cli",
        help="Interface to launch (cli or api, default: cli)"
    )
    
    parser.add_argument(
        "--data-file", "-d",
        default="scrum_data.json",
        help="Path to data file (default: scrum_data.json)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port for API server (default: 8000)"
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for API server (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    if args.interface == "cli":
        # Import and run CLI
        try:
            from scrummaster.cli import ScrumMasterCLI
            app = ScrumMasterCLI(data_file=args.data_file)
            app.run()
        except ImportError:
            print("Error: Could not import CLI interface.")
            print("Make sure the required packages are installed:")
            print("  pip install textual nltk")
            sys.exit(1)
    else:
        # Import and run API
        try:
            import uvicorn
            from scrummaster.api import app
            print(f"Starting API server at http://{args.host}:{args.port}")
            print("API documentation available at:")
            print(f"  http://{args.host}:{args.port}/docs")
            uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("Error: Could not import API interface.")
            print("Make sure the required packages are installed:")
            print("  pip install fastapi uvicorn nltk")
            sys.exit(1)


if __name__ == "__main__":
    main()