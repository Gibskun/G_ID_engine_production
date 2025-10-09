#!/usr/bin/env python3
"""
Search for the EXACT duplicate checking logic that generates the error message
"Duplicate KTP number 'X' (also found in row Y)"
"""

import os
import re

def search_for_duplicate_logic():
    """Search for the exact logic creating the duplicate error messages"""
    
    search_patterns = [
        r'duplicate.*ktp.*number.*found.*row',
        r'duplicate.*ktp.*row',
        r'also.*found.*in.*row',
        r'seen_ktp.*i\+2',
        r'seen_ktp.*row',
        r'row.*\d+.*duplicate',
        r'if.*ktp.*in.*seen',
        r'seen.*add.*row',
        r'seen.*append.*row'
    ]
    
    all_findings = []
    
    # Search all Python files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', 'venv', '.env']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        for pattern in search_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                all_findings.append({
                                    'file': filepath,
                                    'line': i,
                                    'content': line.strip(),
                                    'pattern': pattern
                                })
                except:
                    continue
    
    return all_findings

def search_for_string_construction():
    """Search for f-string or string formatting that creates the error message"""
    
    string_patterns = [
        r'f.*duplicate.*ktp.*number.*row',
        r'f.*duplicate.*number.*found.*row',
        r'format.*duplicate.*row',
        r'\".*duplicate.*ktp.*number.*\"',
        r'\'.*duplicate.*ktp.*number.*\'',
        r'\+.*also.*found.*in.*row',
        r'also.*found.*in.*row.*\+',
        r'f\".*also.*found.*row',
        r'f\'.*also.*found.*row'
    ]
    
    findings = []
    
    for root, dirs, files in os.walk('.'):
        if any(skip in root for skip in ['.git', '__pycache__', 'venv', '.env']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        for pattern in string_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                findings.append({
                                    'file': filepath,
                                    'line': i,
                                    'content': line.strip(),
                                    'pattern': pattern
                                })
                except:
                    continue
    
    return findings

def main():
    print("🔍 SEARCHING FOR DUPLICATE ERROR MESSAGE LOGIC")
    print("=" * 60)
    
    print("\n🔧 Searching for duplicate checking logic...")
    logic_findings = search_for_duplicate_logic()
    
    print(f"\n🔧 Searching for error message construction...")
    string_findings = search_for_string_construction()
    
    all_findings = logic_findings + string_findings
    
    if not all_findings:
        print("❌ NO MATCHING PATTERNS FOUND!")
        print("The duplicate checking logic might be:")
        print("1. Hidden in compiled code")
        print("2. Coming from frontend validation")
        print("3. Using different variable names")
        print("4. In a different file format")
    else:
        print(f"⚠️ FOUND {len(all_findings)} POTENTIAL MATCHES:")
        print()
        
        current_file = None
        for finding in all_findings:
            if finding['file'] != current_file:
                current_file = finding['file']
                print(f"📁 {finding['file']}:")
            
            print(f"   Line {finding['line']:3d}: {finding['content']}")
        
        print()
        print("🔧 These locations need to be disabled!")

if __name__ == "__main__":
    main()