#!/usr/bin/env python3
"""
Download a test export file to verify passport_id data
"""

import requests
import os

def download_test_export():
    """Download a test export file"""
    base_url = "http://127.0.0.1:8000"
    
    print("🔧 Downloading Test Export File")
    print("=" * 40)
    
    try:
        # Download CSV export
        print("📥 Downloading CSV export...")
        response = requests.get(f"{base_url}/api/v1/global-id/export?format=csv&include_empty_passport=true")
        
        if response.status_code == 200:
            # Save to file
            filename = "test_global_id_export.csv"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ File saved: {filename}")
            print(f"   File size: {file_size:,} bytes")
            
            # Get file info
            if os.path.exists(filename):
                actual_size = os.path.getsize(filename)
                print(f"   Verified size: {actual_size:,} bytes")
                
                # Show first few lines
                print(f"\n📋 First few lines of the file:")
                with open(filename, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if i >= 5:  # Show first 5 lines
                            break
                        print(f"   {i+1}: {line.strip()}")
                
                print(f"\n✅ Test file created successfully!")
                print(f"💡 Now run: python check_export.py {filename}")
            else:
                print(f"❌ File was not created properly")
                
        else:
            print(f"❌ Download failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    download_test_export()