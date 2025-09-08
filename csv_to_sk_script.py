#!/usr/bin/env python3
"""
CSV to SerialKiller2 Script Converter
Converts magnetometer CSV data into a SerialKiller2 script format
"""

import csv
import sys
import os

def convert_csv_to_sk_script(csv_file_path, output_file_path=None):
    """
    Convert CSV magnetometer data to SerialKiller2 script format
    
    Args:
        csv_file_path: Path to the input CSV file
        output_file_path: Path to the output script file (optional)
    """
    
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found: {csv_file_path}")
        return False
    
    if output_file_path is None:
        base_name = os.path.splitext(csv_file_path)[0]
        output_file_path = f"{base_name}_sk_script.txt"
    
    try:
        # Read CSV file
        with open(csv_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            header = next(csv_reader)  # Skip header
            print(f"CSV Header: {header}")
            
            # Generate SerialKiller2 script
            script_lines = [
                "# Script generated from CSV magnetometer data",
                "# Usage: Load this script in SerialKiller2 and run it",
                "",
                "ptime=250;",
                '@plot key-value --keys "HX,HY,HZ" --points 1000 --title \'Magnetometer Output Helmholtz Mag\'',
                "",
                "@info=Starting magnetometer data output (from CSV)",
                "@delay=100",
                "",
                "# Magnetometer data points from CSV",
                ""
            ]
            
            data_count = 0
            for row in csv_reader:
                if len(row) >= 4:  # time, HX, HY, HZ
                    try:
                        hx = round(float(row[1]), 1)
                        hy = round(float(row[2]), 1)
                        hz = round(float(row[3]), 1)
                        script_lines.append(f"target={hx},{hy},{hz};")
                        data_count += 1
                    except ValueError:
                        print(f"Skipping invalid row: {row}")
                        continue
            
            script_lines.extend([
                "",
                "@info=Finished magnetometer data output",
                f"# Total data points: {data_count}"
            ])
            
            # Write script file
            with open(output_file_path, 'w') as script_file:
                script_file.write('\n'.join(script_lines))
            
            print(f"Successfully converted {data_count} data points")
            print(f"SerialKiller2 script saved to: {output_file_path}")
            return True
            
    except Exception as e:
        print(f"Error converting CSV file: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python csv_to_sk_script.py <csv_file> [output_file]")
        print("Example: python csv_to_sk_script.py mag_data.csv mag_data_script.txt")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = convert_csv_to_sk_script(csv_file, output_file)
    sys.exit(0 if success else 1)
