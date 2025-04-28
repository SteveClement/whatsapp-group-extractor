#!/usr/bin/env python3
"""
WhatsApp Chat Exporter - Convert WhatsApp chat exports to HTML and JSON formats.

This script processes WhatsApp chat export zip files and converts them to
browsable HTML and searchable JSON formats. It preserves the chat structure
and includes media files if available.

Usage:
    whatsapp_converter.py convert ZIPFILE [--output-dir DIR] [--info-file FILE]
    whatsapp_converter.py update ZIPFILE --output-dir DIR [--info-file FILE] [--highlight LEVEL]

Commands:
    convert             Process a new WhatsApp export
    update              Update an existing export with new messages

Arguments:
    ZIPFILE             Path to the WhatsApp export zip file
    
Options:
    --output-dir DIR    Output directory for HTML and JSON files [default: html]
    --info-file FILE    Optional path to a custom info.txt file
    --highlight LEVEL   How to highlight new messages (none, subtle, prominent) [default: subtle]
    -h, --help          Show this help message and exit
"""

import os
import sys
import logging
import argparse
import traceback

from chat_exporter.exporter import process_export, process_update

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Convert WhatsApp chat export to HTML and JSON'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Process a new WhatsApp export')
    convert_parser.add_argument(
        'zip_path',
        help='Path to WhatsApp export zip file'
    )
    convert_parser.add_argument(
        '-o', '--output-dir',
        help='Output directory (default: ./html)',
        default='html'
    )
    convert_parser.add_argument(
        '-i', '--info-file',
        help='Path to custom info.txt file'
    )
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update an existing export with new messages')
    update_parser.add_argument(
        'zip_path',
        help='Path to WhatsApp export zip file'
    )
    update_parser.add_argument(
        '-o', '--output-dir',
        help='Directory with existing export',
        required=True
    )
    update_parser.add_argument(
        '-i', '--info-file',
        help='Path to custom info.txt file'
    )
    update_parser.add_argument(
        '--highlight',
        choices=['none', 'subtle', 'prominent'],
        default='subtle',
        help='How to highlight new messages'
    )
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # No command specified
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        if args.command == 'convert':
            # Process a new export
            html_path, json_path, metadata_path = process_export(
                args.zip_path,
                args.output_dir,
                args.info_file
            )
            
            logger.info(f"Conversion complete!")
            logger.info(f"HTML file: {html_path}")
            logger.info(f"JSON file: {json_path}")
            logger.info(f"Metadata file: {metadata_path}")
            logger.info(f"\nOpen the HTML file in a web browser to view the chat.")
            
        elif args.command == 'update':
            # Update an existing export
            html_path, json_path, metadata_path, new_count = process_update(
                args.zip_path,
                args.output_dir,
                args.info_file,
                args.highlight
            )
            
            if new_count > 0:
                logger.info(f"Update complete! Added {new_count} new messages.")
                logger.info(f"HTML file: {html_path}")
                logger.info(f"JSON file: {json_path}")
                logger.info(f"Metadata file: {metadata_path}")
                logger.info(f"\nOpen the HTML file in a web browser to view the chat.")
            else:
                logger.info(f"No new messages found in the update.")
        
        return 0
    
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        return 1
    
    except Exception as e:
        logger.error(f"Error: An unexpected error occurred.")
        logger.error(f"{type(e).__name__}: {e}")
        logger.error("\nStack trace:")
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())
