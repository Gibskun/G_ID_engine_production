"""
Dummy Data Generator for Global ID Management System

This script generates Excel files with dummy data that matches the expected format
for testing the Excel/CSV upload functionality.
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from typing import Optional
import os

# Try to import Excel libraries
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

try:
    import xlwt
    XLS_SUPPORT = True
except ImportError:
    XLS_SUPPORT = False


class DummyDataGenerator:
    def __init__(self):
        random.seed(42)  # For reproducible results
        
        # Indonesian names database
        self.first_names = [
            'Ahmad', 'Budi', 'Citra', 'Devi', 'Eko', 'Fitri', 'Gina', 'Hadi',
            'Ika', 'Joko', 'Kiki', 'Lina', 'Maya', 'Nia', 'Oki', 'Putri',
            'Qori', 'Rina', 'Sari', 'Tono', 'Uci', 'Vina', 'Wati', 'Yani', 'Zaki',
            'Andi', 'Bayu', 'Candra', 'Dian', 'Erna', 'Fajar', 'Galih', 'Hana',
            'Indra', 'Jihan', 'Kurnia', 'Lestari', 'Mira', 'Nita', 'Omar', 'Prima'
        ]
        
        self.last_names = [
            'Santoso', 'Pratama', 'Sari', 'Wijaya', 'Utomo', 'Kusuma', 'Wati',
            'Rahman', 'Hidayat', 'Nurhaliza', 'Simatupang', 'Handayani', 'Setiawan',
            'Maharani', 'Gunawan', 'Purnomo', 'Wulandari', 'Saputra', 'Anggraini',
            'Suryanto', 'Pertiwi', 'Hermawan', 'Rahayu', 'Saputri', 'Nugroho',
            'Lestari', 'Kurniawan', 'Dewi', 'Susanto', 'Fitriani', 'Budiman'
        ]
        
    def _generate_random_birth_date(self):
        """Generate a random birth date for someone aged 18-65"""
        today = datetime.now().date()
        min_age_date = today - timedelta(days=65*365)  # 65 years ago
        max_age_date = today - timedelta(days=18*365)  # 18 years ago
        
        # Random date between min and max
        time_between = max_age_date - min_age_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        
        return min_age_date + timedelta(days=random_days)
    
    def _generate_passport_id(self, used_passport_ids: set) -> str:
        """
        Generate unique passport ID with 8-9 characters
        Format: 2-3 letters at the beginning followed by 5-6 numbers
        Example: AB123456, CD789012, EFG345678
        """
        while True:
            # Generate 2-3 letters at the beginning
            letter_count = random.choice([2, 3])
            letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=letter_count))
            
            # Generate 5-6 numbers to complete 8-9 total characters
            number_count = 9 - letter_count if random.choice([True, False]) else 8 - letter_count
            numbers = ''.join(random.choices('0123456789', k=number_count))
            
            passport_id = letters + numbers
            
            # Ensure it's 8-9 characters and unique
            if 8 <= len(passport_id) <= 9 and passport_id not in used_passport_ids:
                used_passport_ids.add(passport_id)
                return passport_id
        
    def generate_dummy_data(self, num_records: int = 100, include_invalid_ktp: bool = False, invalid_ktp_ratio: float = 0.2) -> pd.DataFrame:
        """
        Generate dummy data matching the Excel upload format
        
        Required columns: name, personal_number, no_ktp, passport_id, bod, process
        
        Args:
            num_records: Number of records to generate
            include_invalid_ktp: Whether to include some records with invalid KTP lengths
            invalid_ktp_ratio: Ratio of records with invalid KTP (0.0-1.0)
        """
        data = []
        used_ktps = set()  # Track used KTP numbers to ensure uniqueness
        used_personal_numbers = set()  # Track used personal numbers to ensure uniqueness
        used_passport_ids = set()  # Track used passport IDs to ensure uniqueness
        
        # Calculate how many records should have invalid KTP
        invalid_ktp_count = int(num_records * invalid_ktp_ratio) if include_invalid_ktp else 0
        invalid_ktp_indices = set(random.sample(range(num_records), invalid_ktp_count))
        
        for i in range(num_records):
            # Determine if this record should have invalid KTP
            should_have_invalid_ktp = i in invalid_ktp_indices
            
            # Generate KTP number (16 digits for valid, other lengths for invalid)
            while True:
                if should_have_invalid_ktp:
                    # Generate invalid KTP with random length (12-15 digits only - respect database limit of 16)
                    invalid_lengths = list(range(12, 16))  # 12-15 digits only
                    target_length = random.choice(invalid_lengths)
                    ktp_number = ''.join(random.choices('0123456789', k=target_length))
                else:
                    # Generate valid KTP number (exactly 16 digits)
                    # Indonesian KTP format: PPKKSSDDMMYYXXXX
                    province_codes = ['32', '33', '34', '35', '36', '61', '73', '74', '75', '76']
                    province = random.choice(province_codes)
                    
                    # KK = Kabupaten/Kota (01-99)
                    kabupaten = f"{random.randint(1, 99):02d}"
                    
                    # SS = Kecamatan (01-99)
                    kecamatan = f"{random.randint(1, 99):02d}"
                    
                    # DDMMYY = Birth date
                    birth_date = self._generate_random_birth_date()
                    dd = f"{birth_date.day:02d}"
                    mm = f"{birth_date.month:02d}"
                    yy = f"{birth_date.year % 100:02d}"
                    
                    # XXXX = Sequential number (0001-9999)
                    seq = f"{random.randint(1, 9999):04d}"
                    
                    ktp_number = f"{province}{kabupaten}{kecamatan}{dd}{mm}{yy}{seq}"
                
                if ktp_number not in used_ktps:
                    used_ktps.add(ktp_number)
                    break
            
            # Generate unique personal number (Employee ID format: EMP-YYYY-NNNN)
            while True:
                current_year = datetime.now().year
                sequence = random.randint(1, 9999)
                personal_number = f"EMP-{current_year}-{sequence:04d}"
                
                if personal_number not in used_personal_numbers:
                    used_personal_numbers.add(personal_number)
                    break
            
            # Generate unique passport ID
            passport_id = self._generate_passport_id(used_passport_ids)
            
            # Generate birth date (BOD format: YYYY-MM-DD)
            birth_date = self._generate_random_birth_date() if should_have_invalid_ktp else birth_date
            bod = birth_date.strftime('%Y-%m-%d')
            
            # Generate Indonesian-style name
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            name = f"{first_name} {last_name}"
            
            # Determine process field value
            if len(ktp_number) == 16:
                # Valid KTP length - process field is ignored (can be 0, 1, or empty)
                process = random.choice([0, 1, ''])
            else:
                # Invalid KTP length - determine if should be allowed or rejected
                if should_have_invalid_ktp and random.random() < 0.7:  # 70% of invalid KTPs get process=1
                    process = 1  # Allow processing despite invalid KTP
                else:
                    process = random.choice([0, '', 2, 3])  # Reject processing
            
            data.append({
                'name': name,
                'personal_number': personal_number,
                'no_ktp': ktp_number,
                'passport_id': passport_id,
                'bod': bod,
                'process': process
            })
        
        return pd.DataFrame(data)
    
    def create_excel_file(self, num_records: int = 100, filename: Optional[str] = None, include_invalid_ktp: bool = False, invalid_ktp_ratio: float = 0.2) -> str:
        """
        Create Excel (.xlsx) file with dummy data
        Each field is properly separated into individual columns
        
        Args:
            num_records: Number of records to generate
            filename: Output filename (optional)
            include_invalid_ktp: Whether to include records with invalid KTP lengths
            invalid_ktp_ratio: Ratio of records with invalid KTP (0.0-1.0)
            
        Returns:
            Path to the created Excel file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            suffix = "_with_invalid_ktp" if include_invalid_ktp else ""
            filename = f"dummy_data_{num_records}records{suffix}_{timestamp}.xlsx"
        
        # Ensure .xlsx extension
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        # Generate data with proper column separation
        df = self.generate_dummy_data(num_records, include_invalid_ktp, invalid_ktp_ratio)
        
        if EXCEL_SUPPORT:
            # Create proper Excel file with openpyxl
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"✅ Created Excel file: {filename}")
        else:
            # Fallback to CSV with xlsx extension
            df.to_csv(filename.replace('.xlsx', '.csv'), index=False)
            print(f"⚠️  openpyxl not available. Created CSV instead: {filename.replace('.xlsx', '.csv')}")
            print("   To create proper Excel files, install: pip install openpyxl")
            filename = filename.replace('.xlsx', '.csv')
        
        return os.path.abspath(filename)
    
    def create_xls_file(self, num_records: int = 100, filename: Optional[str] = None) -> str:
        """
        Create Excel (.xls) file with dummy data (legacy Excel format)
        Each field is properly separated into individual columns
        
        Args:
            num_records: Number of records to generate
            filename: Output filename (optional)
            
        Returns:
            Path to the created Excel file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"dummy_data_{num_records}records_{timestamp}.xls"
        
        # Ensure .xls extension
        if not filename.endswith('.xls'):
            filename += '.xls'
        
        # Generate data with proper column separation
        df = self.generate_dummy_data(num_records)
        
        # Try multiple approaches for XLS file creation
        try:
            # First try with openpyxl but change extension to xlsx
            xlsx_filename = filename.replace('.xls', '.xlsx')
            df.to_excel(xlsx_filename, index=False, engine='openpyxl')
            print(f"✅ Created Excel file: {xlsx_filename} (converted from .xls to .xlsx format)")
            return os.path.abspath(xlsx_filename)
        except Exception as e:
            try:
                # Try direct xlwt if available
                import xlwt
                # Manual XLS creation with xlwt
                workbook = xlwt.Workbook()
                worksheet = workbook.add_sheet('Employee Data')
                
                # Write headers
                headers = ['name', 'personal_number', 'no_ktp', 'bod']
                for col, header in enumerate(headers):
                    worksheet.write(0, col, header)
                
                # Write data
                for row, (_, data_row) in enumerate(df.iterrows(), 1):
                    for col, value in enumerate(data_row):
                        worksheet.write(row, col, str(value))
                
                workbook.save(filename)
                print(f"✅ Created XLS file: {filename}")
                return os.path.abspath(filename)
            except Exception:
                # Fallback to CSV
                csv_filename = filename.replace('.xls', '.csv')
                df.to_csv(csv_filename, index=False)
                print(f"⚠️  XLS creation failed. Created CSV instead: {csv_filename}")
                print("   XLS format has compatibility issues with current pandas version")
                return os.path.abspath(csv_filename)
    
    def create_csv_file(self, num_records: int = 100, filename: Optional[str] = None, include_invalid_ktp: bool = False, invalid_ktp_ratio: float = 0.2) -> str:
        """
        Create CSV file with dummy data
        
        Args:
            num_records: Number of records to generate
            filename: Output filename (optional)
            include_invalid_ktp: Whether to include records with invalid KTP lengths
            invalid_ktp_ratio: Ratio of records with invalid KTP (0.0-1.0)
            
        Returns:
            Path to the created CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            suffix = "_with_invalid_ktp" if include_invalid_ktp else ""
            filename = f"dummy_data_{num_records}records{suffix}_{timestamp}.csv"
        
        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # Generate data
        df = self.generate_dummy_data(num_records, include_invalid_ktp, invalid_ktp_ratio)
        
        # Save as CSV
        df.to_csv(filename, index=False)
        
        return os.path.abspath(filename)
    
    def create_all_formats(self, num_records: int = 100, base_filename: Optional[str] = None) -> dict:
        """
        Create files in all supported formats (CSV, XLSX, XLS)
        Each field is properly separated into individual columns
        
        Args:
            num_records: Number of records to generate
            base_filename: Base filename without extension (optional)
            
        Returns:
            Dictionary with format as key and filepath as value
        """
        if base_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"dummy_data_{num_records}records_{timestamp}"
        
        files_created = {}
        
        # Create CSV (always works)
        csv_file = self.create_csv_file(num_records, f"{base_filename}.csv")
        files_created['CSV'] = csv_file
        
        # Create XLSX (modern Excel)
        xlsx_file = self.create_excel_file(num_records, f"{base_filename}.xlsx")
        files_created['XLSX'] = xlsx_file
        
        # Create XLS (legacy Excel)
        xls_file = self.create_xls_file(num_records, f"{base_filename}.xls")
        files_created['XLS'] = xls_file
        
        return files_created
    
    def verify_data_structure(self, num_records: int = 5, include_invalid_ktp: bool = True) -> None:
        """
        Verify that data is properly structured with separate columns
        """
        print("🔍 Verifying Data Structure:")
        df = self.generate_dummy_data(num_records, include_invalid_ktp, 0.4)  # 40% invalid for testing
        
        print(f"  📊 Columns: {list(df.columns)}")
        print(f"  📏 Shape: {df.shape} (rows, columns)")
        print(f"  🔢 Data Types:")
        for col in df.columns:
            print(f"    - {col}: {df[col].dtype}")
        
        print("\n📋 Sample Data Preview:")
        print(df.head(3).to_string(index=False))
        
        # Verify KTP length distribution
        print(f"\n📏 KTP Length Analysis:")
        ktp_lengths = df['no_ktp'].str.len().value_counts().sort_index()
        for length, count in ktp_lengths.items():
            status = "✅ Valid" if length == 16 else "❌ Invalid"
            print(f"    - {length} digits: {count} records ({status})")
        
        # Verify process field distribution
        print(f"\n🔄 Process Field Analysis:")
        process_counts = df['process'].value_counts()
        for value, count in process_counts.items():
            if value == 1:
                print(f"    - process = 1: {count} records (✅ Override - allows invalid KTP)")
            elif value == 0:
                print(f"    - process = 0: {count} records (❌ No override)")
            elif value == '':
                print(f"    - process = empty: {count} records (❌ No override)")
            else:
                print(f"    - process = {value}: {count} records (❌ No override)")
        
        # Verify logic: invalid KTP with process=1 should be allowed
        invalid_ktp_with_override = df[(df['no_ktp'].str.len() != 16) & (df['process'] == 1)]
        invalid_ktp_without_override = df[(df['no_ktp'].str.len() != 16) & (df['process'] != 1)]
        
        print(f"\n🎯 Validation Logic Summary:")
        print(f"    - Invalid KTP with process=1 (should be allowed): {len(invalid_ktp_with_override)} records")
        print(f"    - Invalid KTP without process=1 (should fail): {len(invalid_ktp_without_override)} records")
        print(f"    - Valid KTP (process field ignored): {len(df[df['no_ktp'].str.len() == 16])} records")
        
        # Verify each field is in separate column
        expected_columns = ['name', 'personal_number', 'no_ktp', 'passport_id', 'bod', 'process']
        missing_columns = set(expected_columns) - set(df.columns)
        extra_columns = set(df.columns) - set(expected_columns)
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
        if extra_columns:
            print(f"⚠️  Extra columns: {extra_columns}")
        if not missing_columns and not extra_columns:
            print("✅ All expected columns present and properly separated")
    
    def create_sample_files(self):
        """Create sample files with different record counts in multiple formats"""
        files_created = []
        
        print("📊 Creating sample files in multiple formats...")
        
        # Create small sample (10 records) - all formats
        print("  📄 Small dataset (10 records) - Normal data...")
        csv_small = self.create_csv_file(10, "sample_data_small.csv")
        xlsx_small = self.create_excel_file(10, "sample_data_small.xlsx")
        files_created.extend([csv_small, xlsx_small])
        
        # Create small sample with invalid KTP for testing
        print("  📄 Small dataset (10 records) - With invalid KTP testing...")
        csv_small_test = self.create_csv_file(10, "sample_data_small_ktp_test.csv", include_invalid_ktp=True, invalid_ktp_ratio=0.4)
        xlsx_small_test = self.create_excel_file(10, "sample_data_small_ktp_test.xlsx", include_invalid_ktp=True, invalid_ktp_ratio=0.4)
        files_created.extend([csv_small_test, xlsx_small_test])
        
        # Create medium sample (100 records) - all formats
        print("  📄 Medium dataset (100 records) - Normal data...")
        csv_medium = self.create_csv_file(100, "sample_data_medium.csv")
        xlsx_medium = self.create_excel_file(100, "sample_data_medium.xlsx")
        files_created.extend([csv_medium, xlsx_medium])
        
        # Create medium sample with invalid KTP for testing
        print("  📄 Medium dataset (100 records) - With invalid KTP testing...")
        csv_medium_test = self.create_csv_file(100, "sample_data_medium_ktp_test.csv", include_invalid_ktp=True, invalid_ktp_ratio=0.2)
        xlsx_medium_test = self.create_excel_file(100, "sample_data_medium_ktp_test.xlsx", include_invalid_ktp=True, invalid_ktp_ratio=0.2)
        files_created.extend([csv_medium_test, xlsx_medium_test])
        
        # Create large sample (1000 records) - all formats
        print("  📄 Large dataset (1000 records) - Normal data...")
        csv_large = self.create_csv_file(1000, "sample_data_large.csv")
        xlsx_large = self.create_excel_file(1000, "sample_data_large.xlsx")
        files_created.extend([csv_large, xlsx_large])
        
        return files_created


def main():
    """Main function to demonstrate the dummy data generator"""
    print("🏭 Global ID Dummy Data Generator")
    print("=" * 50)
    
    # Check library availability
    print("📚 Library Status:")
    print(f"  - pandas: ✅ Available")
    print(f"  - openpyxl (Excel .xlsx): {'✅ Available' if EXCEL_SUPPORT else '❌ Not installed'}")
    print(f"  - xlwt (Excel .xls): {'✅ Available' if XLS_SUPPORT else '❌ Not installed'}")
    
    if not EXCEL_SUPPORT:
        print("\n� To install Excel support:")
        print("   pip install openpyxl xlwt")
    
    print()
    
    generator = DummyDataGenerator()
    
    # Verify data structure
    generator.verify_data_structure(3)
    print()
    
    files = generator.create_sample_files()
    
    print("\n✅ Files created successfully:")
    csv_files = []
    excel_files = []
    
    for file_path in files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024  # KB
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].upper()
            
            if file_ext == '.CSV':
                csv_files.append(f"  📄 {file_name} ({file_size:.1f} KB)")
            else:
                excel_files.append(f"  📊 {file_name} ({file_size:.1f} KB)")
    
    if csv_files:
        print("  📋 CSV Files:")
        for file_info in csv_files:
            print(file_info)
    
    if excel_files:
        print("  📊 Excel Files:")
        for file_info in excel_files:
            print(file_info)
    
    print(f"\n📁 All files saved in: {os.getcwd()}")
    
    # Display sample data structure
    print("\n📋 Data Structure (each field in separate column):")
    sample_df = generator.generate_dummy_data(3)
    print(sample_df.to_string(index=False))
    
    print(f"\n📊 Column Details:")
    for i, col in enumerate(['name', 'personal_number', 'no_ktp', 'passport_id', 'bod', 'process'], 1):
        print(f"  Column {i}: {col}")
    
    print("\n🎯 Usage Tips:")
    print("- Each field is properly separated into individual columns")
    print("- Support for CSV and XLSX formats")
    print("- Files contain realistic Indonesian names and KTP numbers")
    print("- All KTP numbers and personal numbers are unique within each file")
    print("- Personal numbers follow employee ID format (EMP-YYYY-NNNN)")
    print("- Birth dates are realistic (18-65 years old)")
    print("- Passport IDs follow the required format (8-9 characters, letter first, numbers dominate)")
    print("- NEW: Process column for KTP validation override:")
    print("  * process = 1: Allows invalid KTP lengths (not 16 characters) to be processed")
    print("  * process = 0 or empty: Invalid KTP lengths will be rejected")
    print("  * For valid KTP (16 characters): process field is ignored")
    print("- Ready for upload to test Excel/CSV upload functionality with KTP validation")
    
    print("\n🧪 Test Files Created:")
    print("- Normal files: All KTP numbers are exactly 16 characters")
    print("- KTP test files: Include invalid KTP lengths with process override column")
    print("- Use KTP test files to verify the validation override functionality")


if __name__ == "__main__":
    main()