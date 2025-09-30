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
        
    def generate_dummy_data(self, num_records: int = 100) -> pd.DataFrame:
        """
        Generate dummy data matching the Excel upload format
        
        Required columns: name, personal_number, no_ktp, bod
        """
        data = []
        used_ktps = set()  # Track used KTP numbers to ensure uniqueness
        used_personal_numbers = set()  # Track used personal numbers to ensure uniqueness
        
        for i in range(num_records):
            # Generate unique KTP number (16 digits)
            while True:
                # Indonesian KTP format: PPKKSSDDMMYYXXXX
                # PP = Province (32 = Jakarta, 35 = Jabar, 33 = Jateng, etc.)
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
            
            # Generate birth date (BOD format: YYYY-MM-DD)
            bod = birth_date.strftime('%Y-%m-%d')
            
            # Generate Indonesian-style name
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            name = f"{first_name} {last_name}"
            
            data.append({
                'name': name,
                'personal_number': personal_number,
                'no_ktp': ktp_number,
                'bod': bod
            })
        
        return pd.DataFrame(data)
    
    def create_excel_file(self, num_records: int = 100, filename: Optional[str] = None) -> str:
        """
        Create Excel file with dummy data
        Note: This creates a CSV file with .xlsx extension for compatibility.
        For proper Excel formatting, install openpyxl or xlsxwriter.
        
        Args:
            num_records: Number of records to generate
            filename: Output filename (optional)
            
        Returns:
            Path to the created Excel file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"dummy_data_{num_records}records_{timestamp}.xlsx"
        
        # Ensure .xlsx extension
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        # Generate data
        df = self.generate_dummy_data(num_records)
        
        # Since Excel libraries aren't available, save as CSV but inform user
        csv_filename = filename.replace('.xlsx', '.csv')
        df.to_csv(csv_filename, index=False)
        
        print(f"⚠️  Excel libraries not available. Created CSV instead: {csv_filename}")
        print("   To create proper Excel files, install: pip install openpyxl")
        
        return os.path.abspath(csv_filename)
    
    def create_csv_file(self, num_records: int = 100, filename: Optional[str] = None) -> str:
        """
        Create CSV file with dummy data
        
        Args:
            num_records: Number of records to generate
            filename: Output filename (optional)
            
        Returns:
            Path to the created CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"dummy_data_{num_records}records_{timestamp}.csv"
        
        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # Generate data
        df = self.generate_dummy_data(num_records)
        
        # Save as CSV
        df.to_csv(filename, index=False)
        
        return os.path.abspath(filename)
    
    def create_sample_files(self):
        """Create sample files with different record counts"""
        files_created = []
        
        # Create small sample (10 records)
        excel_small = self.create_excel_file(10, "sample_data_small.xlsx")
        csv_small = self.create_csv_file(10, "sample_data_small.csv")
        files_created.extend([excel_small, csv_small])
        
        # Create medium sample (100 records)
        excel_medium = self.create_excel_file(100, "sample_data_medium.xlsx")
        csv_medium = self.create_csv_file(100, "sample_data_medium.csv")
        files_created.extend([excel_medium, csv_medium])
        
        # Create large sample (1000 records)
        excel_large = self.create_excel_file(1000, "sample_data_large.xlsx")
        csv_large = self.create_csv_file(1000, "sample_data_large.csv")
        files_created.extend([excel_large, csv_large])
        
        return files_created


def main():
    """Main function to demonstrate the dummy data generator"""
    print("🏭 Global ID Dummy Data Generator")
    print("=" * 50)
    
    generator = DummyDataGenerator()
    
    print("📊 Creating sample files...")
    files = generator.create_sample_files()
    
    print("\n✅ Files created successfully:")
    for file_path in files:
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"  📄 {os.path.basename(file_path)} ({file_size:.1f} KB)")
    
    print(f"\n📁 All files saved in: {os.getcwd()}")
    
    # Display sample data
    print("\n📋 Sample of generated data:")
    sample_df = generator.generate_dummy_data(5)
    print(sample_df.to_string(index=False))
    
    print("\n🎯 Usage Tips:")
    print("- Upload these files to test the Excel/CSV upload functionality")
    print("- Files contain realistic Indonesian names and KTP numbers")
    print("- All KTP numbers and personal numbers are unique within each file")
    print("- Personal numbers follow employee ID format (EMP-YYYY-NNNN)")
    print("- Birth dates are realistic (18-65 years old)")


if __name__ == "__main__":
    main()