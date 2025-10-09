#!/usr/bin/env python3
"""
Quick verification script to check exported CSV files for passport_id content
"""

import pandas as pd
import os
import sys

def check_csv_file(filepath):
    """Check a CSV file for passport_id content"""
    try:
        print(f"🔍 Analyzing CSV file: {filepath}")
        print("=" * 60)
        
        # Read the CSV file
        df = pd.read_csv(filepath)
        
        # Basic info
        print(f"📊 File Statistics:")
        print(f"   - Total rows: {len(df)}")
        print(f"   - Total columns: {len(df.columns)}")
        print(f"   - Columns: {list(df.columns)}")
        
        # Check if passport_id column exists
        if 'passport_id' not in df.columns:
            print("❌ No 'passport_id' column found in the file!")
            return False
        
        # Analyze passport_id column
        passport_col = df['passport_id']
        
        print(f"\n🔍 Passport_ID Column Analysis:")
        print(f"   - Non-null values: {passport_col.notna().sum()}")
        print(f"   - Null values: {passport_col.isna().sum()}")
        print(f"   - Empty strings: {(passport_col == '').sum()}")
        print(f"   - Total unique values: {passport_col.nunique()}")
        
        # Show sample values
        print(f"\n📋 Sample passport_id values (first 10):")
        for i, value in enumerate(passport_col.head(10)):
            status = "✅ Valid" if pd.notna(value) and value != '' else "❌ Empty/Null"
            print(f"   {i+1}. '{value}' - {status}")
        
        # Show value types
        print(f"\n🔍 Data Type Analysis:")
        print(f"   - Column dtype: {passport_col.dtype}")
        print(f"   - Sample value types: {[type(val) for val in passport_col.head(3).values]}")
        
        # Check for any obvious issues
        has_data = passport_col.notna().any() and (passport_col != '').any()
        
        if has_data:
            print(f"\n✅ RESULT: Passport_ID data found in the file!")
        else:
            print(f"\n❌ RESULT: No valid passport_ID data found!")
        
        return has_data
        
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return False

def main():
    """Main function to check CSV files"""
    # Default paths to check
    download_paths = [
        os.path.expanduser("~/Downloads/global_id_export.csv"),
        os.path.expanduser("~/Desktop/global_id_export.csv"),
        "./global_id_export.csv",
        "C:/Users/*/Downloads/global_id_export.csv"
    ]
    
    print("🔧 CSV File Passport_ID Verification Tool")
    print("=" * 60)
    
    # Check if user provided a file path
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if os.path.exists(filepath):
            check_csv_file(filepath)
        else:
            print(f"❌ File not found: {filepath}")
    else:
        print("📁 Checking common download locations...")
        
        found_file = False
        for path in download_paths:
            if '*' not in path and os.path.exists(path):
                print(f"\n📁 Found file: {path}")
                check_csv_file(path)
                found_file = True
                break
        
        if not found_file:
            print("\n❌ No exported CSV files found in common locations.")
            print("\n💡 Usage:")
            print("   python check_export.py [path_to_csv_file]")
            print("\n💡 Try:")
            print("   1. Download a new CSV export from the web interface")
            print("   2. Check your Downloads folder")
            print("   3. Run this script with the full path to your CSV file")

if __name__ == "__main__":
    main()