#!/usr/bin/env python3
"""
Find All Duplicate Checking Logic
Searches for any remaining duplicate validation code
"""

import os
import re

def search_file_for_patterns(filepath, patterns):
    """Search a file for specific patterns"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
        
        found = []
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    found.append({
                        'file': filepath,
                        'line': i,
                        'content': line.strip(),
                        'pattern': pattern
                    })
        return found
    except Exception as e:
        return []

def find_duplicate_checking():
    """Find all duplicate checking logic"""
    
    # Patterns to search for
    patterns = [
        r'duplicate.*ktp',
        r'duplicate.*passport',
        r'duplicate.*found',
        r'skipped.*duplicate',
        r'also found in row',
        r'already exists',
        r'seen_ktp',
        r'seen_passport',
        r'duplicated.*subset',
        r'existing_record.*ktp',
        r'if.*in.*seen',
        r'skip.*record',
        r'record_errors\.append',
        r'validation.*error',
        r'errors.*duplicate'
    ]
    
    # Directories to search
    search_dirs = [
        'app/services',
        'app/api',
        'app/models'
    ]
    
    all_findings = []
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        findings = search_file_for_patterns(filepath, patterns)
                        all_findings.extend(findings)
    
    return all_findings

def main():
    print("🔍 SEARCHING FOR ALL DUPLICATE CHECKING LOGIC")
    print("=" * 60)
    
    findings = find_duplicate_checking()
    
    if not findings:
        print("✅ NO DUPLICATE CHECKING FOUND!")
        print("All validation appears to be disabled.")
    else:
        print(f"⚠️  FOUND {len(findings)} POTENTIAL DUPLICATE CHECKS:")
        print()
        
        current_file = None
        for finding in findings:
            if finding['file'] != current_file:
                current_file = finding['file']
                print(f"📁 {finding['file']}:")
            
            print(f"   Line {finding['line']:3d}: {finding['content']}")
        
        print()
        print("🔧 RECOMMENDATIONS:")
        print("Review the lines above and disable any active duplicate checking.")

if __name__ == "__main__":
    main()