#!/usr/bin/env python3
"""
Merge CSV rows that are close in time and have complementary (non-overlapping) data.

This fixes the issue where magnetometer readings arrive at slightly different times
and get logged as separate rows with missing values.

Usage:
    python merge_csv_rows.py input.csv [output.csv] [--threshold 0.05]
    
If output.csv is not specified, it will overwrite the input file.
"""

import csv
import sys
import argparse
from pathlib import Path


def parse_value(val):
    """Parse a CSV value, returning None for empty strings."""
    if val is None or val.strip() == '':
        return None
    try:
        return float(val)
    except ValueError:
        return val


def merge_rows(row1, row2, time_col=0):
    """
    Merge two rows, preferring non-empty values.
    Uses the earlier timestamp.
    """
    merged = []
    for i, (v1, v2) in enumerate(zip(row1, row2)):
        val1 = parse_value(v1)
        val2 = parse_value(v2)
        
        if i == time_col:
            # Use the earlier timestamp
            if val1 is not None and val2 is not None:
                merged.append(str(min(val1, val2)))
            elif val1 is not None:
                merged.append(str(val1))
            else:
                merged.append(str(val2) if val2 is not None else '')
        else:
            # For data columns, prefer non-empty values
            if val1 is not None and val2 is not None:
                # Both have values - use the first one (or average if you prefer)
                merged.append(str(val1))
            elif val1 is not None:
                merged.append(str(val1))
            elif val2 is not None:
                merged.append(str(val2))
            else:
                merged.append('')
    
    return merged


def rows_are_complementary(row1, row2, time_col=0):
    """
    Check if two rows have complementary data (non-overlapping values).
    Returns True if they can be safely merged without losing data.
    """
    for i, (v1, v2) in enumerate(zip(row1, row2)):
        if i == time_col:
            continue
        val1 = parse_value(v1)
        val2 = parse_value(v2)
        # If both have values, they overlap (not complementary)
        if val1 is not None and val2 is not None:
            return False
    return True


def process_csv(input_path, output_path, time_threshold=0.05, time_col=0):
    """
    Process a CSV file, merging rows that are close in time.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output CSV file
        time_threshold: Maximum time difference (in seconds) to consider rows for merging
        time_col: Index of the timestamp column (default 0)
    """
    rows = []
    header = None
    
    # Read all rows
    with open(input_path, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append(row)
    
    if not rows:
        print("No data rows found.")
        return 0
    
    # Process rows, merging where appropriate
    merged_rows = []
    i = 0
    merge_count = 0
    
    while i < len(rows):
        current_row = rows[i]
        current_time = parse_value(current_row[time_col])
        
        # Look ahead to see if next row should be merged
        if i + 1 < len(rows):
            next_row = rows[i + 1]
            next_time = parse_value(next_row[time_col])
            
            # Check if times are close enough and rows are complementary
            if (current_time is not None and next_time is not None and
                abs(next_time - current_time) <= time_threshold and
                rows_are_complementary(current_row, next_row, time_col)):
                
                # Merge the rows
                merged = merge_rows(current_row, next_row, time_col)
                merged_rows.append(merged)
                merge_count += 1
                i += 2  # Skip both rows
                continue
        
        # No merge, just keep the current row
        merged_rows.append(current_row)
        i += 1
    
    # Write output
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(merged_rows)
    
    return merge_count


def main():
    parser = argparse.ArgumentParser(
        description='Merge CSV rows that are close in time with complementary data.'
    )
    parser.add_argument('input', help='Input CSV file')
    parser.add_argument('output', nargs='?', help='Output CSV file (default: overwrite input)')
    parser.add_argument('--threshold', '-t', type=float, default=0.05,
                        help='Time threshold in seconds for merging (default: 0.05)')
    parser.add_argument('--time-col', '-c', type=int, default=0,
                        help='Index of timestamp column (default: 0)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path
    
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found.")
        sys.exit(1)
    
    print(f"Processing: {input_path}")
    print(f"Time threshold: {args.threshold}s")
    
    merge_count = process_csv(input_path, output_path, args.threshold, args.time_col)
    
    print(f"Merged {merge_count} row pairs")
    print(f"Output written to: {output_path}")


if __name__ == '__main__':
    main()
