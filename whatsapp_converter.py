#!/usr/bin/env python3
"""
WhatsApp Chat Exporter - Convert WhatsApp chat exports to HTML and JSON formats.

This script processes WhatsApp chat export zip files and converts them to
browsable HTML and searchable JSON formats. It preserves the chat structure
and includes media files if available.

Usage:
    whatsapp_converter.py ZIPFILE [--output-dir DIR] [--info-file FILE]

Arguments:
    ZIPFILE               Path to the WhatsApp export zip file
    
Options:
    --output-dir DIR      Output directory for HTML and JSON files [default: html]
    --info-file FILE      Optional path to a custom info.txt file
    -h, --help            Show this help message and exit
"""

import os
import sys
import argparse
import traceback

from chat_exporter.exporter import process_export

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Convert WhatsApp chat export to HTML and JSON'
    )
    
    parser.add_argument(
        'zip_path',
        help='Path to WhatsApp export zip file'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory (default: ./html)',
        default='html'
    )
    
    parser.add_argument(
        '-i', '--info-file',
        help='Path to custom info.txt file'
    )
    
    # Parse command line arguments
    args = parser.parse_args()
    
    try:
        # Process the export
        html_path, json_path = process_export(
            args.zip_path,
            args.output_dir,
            args.info_file
        )
        
        print(f"\nConversion complete!")
        print(f"HTML file: {html_path}")
        print(f"JSON file: {json_path}")
        print(f"\nOpen the HTML file in a web browser to view the chat.")
        
        return 0
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"Error: An unexpected error occurred.", file=sys.stderr)
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        print("\nStack trace:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
