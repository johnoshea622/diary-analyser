#!/usr/bin/env python3
"""
Strip images from Excel files to reduce file size for GitHub.
Creates cleaned versions of files that exceed GitHub's 100MB limit.
"""

import os
import shutil
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.drawing.image import Image

def get_file_size_mb(filepath):
    """Get file size in MB."""
    return os.path.getsize(filepath) / (1024 * 1024)

def strip_images_from_excel(input_path, output_path=None):
    """
    Remove all images from an Excel file.
    If output_path is None, overwrites the original file.
    """
    if output_path is None:
        output_path = input_path
    
    print(f"Processing: {input_path}")
    original_size = get_file_size_mb(input_path)
    print(f"  Original size: {original_size:.2f} MB")
    
    # Load workbook
    wb = load_workbook(input_path)
    
    images_removed = 0
    # Remove images from all sheets
    for sheet in wb.worksheets:
        if hasattr(sheet, '_images') and sheet._images:
            images_removed += len(sheet._images)
            sheet._images = []
    
    # Save cleaned workbook
    wb.save(output_path)
    
    new_size = get_file_size_mb(output_path)
    print(f"  New size: {new_size:.2f} MB")
    print(f"  Images removed: {images_removed}")
    print(f"  Space saved: {original_size - new_size:.2f} MB")
    
    return new_size

def find_large_excel_files(root_dir, size_limit_mb=50):
    """Find Excel files larger than size_limit_mb."""
    large_files = []
    root_path = Path(root_dir)
    
    for excel_file in root_path.rglob("*.xlsx"):
        if excel_file.name.startswith("~$"):  # Skip temp files
            continue
        size_mb = get_file_size_mb(excel_file)
        if size_mb > size_limit_mb:
            large_files.append((excel_file, size_mb))
    
    return sorted(large_files, key=lambda x: x[1], reverse=True)

def main():
    root_dir = Path(__file__).parent
    
    print("=" * 60)
    print("Finding Excel files larger than 50 MB...")
    print("=" * 60)
    
    large_files = find_large_excel_files(root_dir, size_limit_mb=50)
    
    if not large_files:
        print("No large files found!")
        return
    
    print(f"\nFound {len(large_files)} large files:\n")
    for filepath, size in large_files:
        print(f"  {filepath.relative_to(root_dir)}: {size:.2f} MB")
    
    print("\n" + "=" * 60)
    print("Stripping images from large files...")
    print("=" * 60 + "\n")
    
    for filepath, size in large_files:
        try:
            new_size = strip_images_from_excel(filepath)
            if new_size > 100:
                print(f"  WARNING: Still over 100 MB limit!")
        except Exception as e:
            print(f"  ERROR: {e}")
        print()
    
    print("=" * 60)
    print("Done! Files have been cleaned.")
    print("=" * 60)

if __name__ == "__main__":
    main()
