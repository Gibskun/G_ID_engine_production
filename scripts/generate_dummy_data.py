#!/usr/bin/env python3
"""
Dummy data generation script for the Global ID Management System
Populates the pegawai table with realistic test data matching the new validation rules
"""

import sys
import os
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add app to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.models import Pegawai, Base

# Load environment variables
load_dotenv()

# Indonesian locale faker
fake = Faker('id_ID')  # Indonesian locale
fake_en = Faker('en_US')  # English for fallback

# Database connection - now using consolidated SQL Server database
SOURCE_DATABASE_URL = os.getenv("SOURCE_DATABASE_URL", "mssql+pyodbc://sqlvendor1:password@localhost:1435/gid_dev?driver=ODBC+Driver+17+for+SQL+Server")

def generate_indonesian_name():
    """Generate realistic Indonesian names"""
    first_names = [
        'Ahmad', 'Siti', 'Budi', 'Ratna', 'Eko', 'Linda', 'Agus', 'Maya', 'Dedi', 'Fitri',
        'Bambang', 'Dewi', 'Hendra', 'Nurul', 'Rizky', 'Putri', 'Fajar', 'Indah', 'Teguh', 'Lilis',
        'Wahyu', 'Rina', 'Dimas', 'Sari', 'Anton', 'Wulan', 'Bayu', 'Ayu', 'Joko', 'Tika',
        'Rahman', 'Novi', 'Andi', 'Mega', 'Yudi', 'Ratih', 'Arif', 'Sinta', 'Doni', 'Yani',
        'Iman', 'Diana', 'Guntur', 'Eka', 'Rudi', 'Nita', 'Hadi', 'Lia', 'Roni', 'Siska',
        'Andri', 'Erni', 'Tono', 'Vina', 'Haris', 'Sari', 'Bagus', 'Tuti', 'Irwan', 'Yuli',
        'Dedi', 'Nani', 'Asep', 'Ika', 'Arie', 'Dwi', 'Ucok', 'Ani', 'Beni', 'Cici',
        'Deny', 'Emi', 'Feri', 'Gita', 'Heri', 'Ira', 'Jeki', 'Kiki', 'Ludi', 'Mira',
        'Nino', 'Ovi', 'Peni', 'Qory', 'Rico', 'Siska', 'Tari', 'Ucup', 'Vera', 'Wati',
        'Xavi', 'Yesi', 'Zaki', 'Aldi', 'Bella', 'Citra', 'Dodo', 'Elsa', 'Firman', 'Gina',
        'Hendra', 'Intan', 'Jihan', 'Kania', 'Lina', 'Maria', 'Nina', 'Oscar', 'Poppy', 'Qila',
        'Reza', 'Shinta', 'Tania', 'Ulfa', 'Vero', 'Winda', 'Xyza', 'Yuda', 'Zahra', 'Abdul',
        'Berta', 'Candra', 'Dinda', 'Erik', 'Fina', 'Galih', 'Hana', 'Ivan', 'Juna', 'Karina',
        'Lisa', 'Mita', 'Nanda', 'Okta', 'Prita', 'Rini', 'Susan', 'Tina', 'Ully', 'Vivi'
    ]
    
    last_names = [
        'Santoso', 'Pratama', 'Sari', 'Wijaya', 'Utomo', 'Kusuma', 'Wati',
        'Rahman', 'Hidayat', 'Nurhaliza', 'Simatupang', 'Handayani', 'Setiawan',
        'Maharani', 'Gunawan', 'Purnomo', 'Wulandari', 'Saputra', 'Anggraini',
        'Suryanto', 'Pertiwi', 'Hermawan', 'Rahayu', 'Saputri', 'Nugroho',
        'Lestari', 'Kurniawan', 'Dewi', 'Susanto', 'Fitriani', 'Budiman',
        'Suharto', 'Kartini', 'Baskoro', 'Mulyani', 'Cahyono', 'Andriani',
        'Sutrisno', 'Wahyuni', 'Prasetyo', 'Safitri', 'Hartono', 'Indrayani'
    ]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    return f"{first_name} {last_name}"

def generate_personal_number():
    """Generate employee personal number (employee ID format)"""
    # Generate format: EMP-YYYY-NNNN (EMP-2025-0001, EMP-2025-0002, etc.)
    current_year = datetime.now().year
    sequence = random.randint(1, 9999)
    return f"EMP-{current_year}-{sequence:04d}"

def generate_no_ktp(invalid_ktp: bool = False):
    """
    Generate Indonesian KTP number (16 digits)
    If invalid_ktp is True, generate 12-15 digits (respecting database constraints)
    """
    if invalid_ktp:
        # Generate invalid KTP with 12-15 digits (not 16, but respecting database limit)
        ktp_length = random.choice([12, 13, 14, 15])
        return ''.join([str(random.randint(0, 9)) for _ in range(ktp_length)])
    
    # Generate valid 16-digit KTP
    # Format: XXXXXX-DDMMYY-XXXX
    # First 6 digits: area code (expanded list for more variety)
    area_codes = [
        '110101', '110102', '110103', '110104', '110105',  # Jakarta
        '320101', '320102', '320103', '320104', '320105',  # West Java
        '330101', '330102', '330103', '330104', '330105',  # Central Java
        '350101', '350102', '350103', '350104', '350105',  # East Java
        '360101', '360102', '360103', '360104', '360105',  # Banten
        '310101', '310102', '310103', '310104', '310105',  # DKI Jakarta
        '340101', '340102', '340103', '340104', '340105',  # DIY
        '610101', '610102', '610103', '610104', '610105',  # West Kalimantan
        '620101', '620102', '620103', '620104', '620105',  # Central Kalimantan
        '630101', '630102', '630103', '630104', '630105',  # South Kalimantan
        '640101', '640102', '640103', '640104', '640105',  # East Kalimantan
        '650101', '650102', '650103', '650104', '650105',  # North Kalimantan
        '710101', '710102', '710103', '710104', '710105',  # North Sulawesi
        '720101', '720102', '720103', '720104', '720105',  # Central Sulawesi
        '730101', '730102', '730103', '730104', '730105',  # South Sulawesi
        '740101', '740102', '740103', '740104', '740105',  # Southeast Sulawesi
        '750101', '750102', '750103', '750104', '750105',  # West Sulawesi
        '760101', '760102', '760103', '760104', '760105',  # Gorontalo
        '810101', '810102', '810103', '810104', '810105',  # Maluku
        '820101', '820102', '820103', '820104', '820105',  # North Maluku
        '910101', '910102', '910103', '910104', '910105',  # Papua
        '920101', '920102', '920103', '920104', '920105',  # West Papua
    ]
    
    # Birth date (DDMMYY format)
    birth_date = fake.date_of_birth(minimum_age=18, maximum_age=65)
    ddmmyy = birth_date.strftime('%d%m%y')
    
    # Last 4 digits: serial number
    serial = f"{random.randint(1, 9999):04d}"
    
    return f"{random.choice(area_codes)}{ddmmyy}{serial}"

def generate_birth_date():
    """Generate realistic birth date"""
    return fake.date_of_birth(minimum_age=18, maximum_age=65)

def generate_passport_id(used_passport_ids: set) -> str:
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

def create_dummy_data(count=10000, include_invalid_ktp=False, invalid_ktp_ratio=0.2):
    """
    Create dummy data records with support for invalid KTP and process override
    
    Args:
        count: Number of records to generate
        include_invalid_ktp: Whether to include some records with invalid KTP lengths
        invalid_ktp_ratio: Ratio of records with invalid KTP (0.0-1.0)
    """
    records = []
    used_ktps = set()
    used_personal_numbers = set()
    used_passport_ids = set()
    
    # Calculate how many records should have invalid KTP
    invalid_ktp_count = int(count * invalid_ktp_ratio) if include_invalid_ktp else 0
    
    for i in range(count):
        # Determine if this record should have invalid KTP
        should_have_invalid_ktp = include_invalid_ktp and i < invalid_ktp_count
        
        # Ensure unique No_KTP
        while True:
            no_ktp = generate_no_ktp(invalid_ktp=should_have_invalid_ktp)
            if no_ktp not in used_ktps:
                used_ktps.add(no_ktp)
                break
        
        # Ensure unique personal_number
        while True:
            personal_number = generate_personal_number()
            if personal_number not in used_personal_numbers:
                used_personal_numbers.add(personal_number)
                break
        
        # Generate unique passport_id
        passport_id = generate_passport_id(used_passport_ids)
        
        # Determine process field value based on KTP validity
        if len(no_ktp) == 16:
            # Valid KTP length - process field is ignored (can be 0, 1, or empty)
            process = random.choice([0, 1, ''])
        else:
            # Invalid KTP length - determine if should be allowed or rejected
            if should_have_invalid_ktp and random.random() < 0.7:  # 70% of invalid KTPs get process=1
                process = 1  # Allow processing despite invalid KTP
            else:
                process = random.choice([0, '', 2, 3])  # Reject processing

        record = {
            'name': generate_indonesian_name(),
            'personal_number': personal_number,  # Every employee gets a personal number
            'no_ktp': no_ktp,
            'passport_id': passport_id,
            'bod': generate_birth_date(),
            'process': process  # Process override field
        }
        
        records.append(record)
    
    return records

def populate_database(include_invalid_ktp=False):
    """
    Populate the database with dummy data
    
    Args:
        include_invalid_ktp: Whether to include records with invalid KTP lengths and process override
    """
    try:
        # Create engine and session
        engine = create_engine(SOURCE_DATABASE_URL, echo=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        session = SessionLocal()
        
        # Check if data already exists
        existing_count = session.query(Pegawai).count()
        
        if existing_count > 0:
            print(f"Database already contains {existing_count} records.")
            choice = input("Do you want to add more records? (y/n): ").lower()
            if choice != 'y':
                print("Operation cancelled.")
                return
        
        # Generate dummy data
        data_type = "mixed (valid + invalid KTPs)" if include_invalid_ktp else "valid KTPs only"
        print(f"Generating 7500 dummy records with {data_type}...")
        dummy_data = create_dummy_data(7500, include_invalid_ktp=include_invalid_ktp, invalid_ktp_ratio=0.2)
        
        # Insert data
        print("Inserting records into database...")
        inserted_count = 0
        invalid_ktp_count = 0
        process_override_count = 0
        
        for i, data in enumerate(dummy_data, 1):
            try:
                # Count statistics for reporting
                if len(data['no_ktp']) != 16:
                    invalid_ktp_count += 1
                if data.get('process') == 1:
                    process_override_count += 1
                    
                pegawai = Pegawai(
                    name=data['name'],
                    personal_number=data['personal_number'],  # Use personal_number field to match schema
                    no_ktp=data['no_ktp'],
                    passport_id=data['passport_id'],
                    bod=data['bod']
                    # Note: process field is not stored in database, it's only for Excel uploads
                )
                
                session.add(pegawai)
                session.commit()
                inserted_count += 1
                
                # Progress indicator every 100 records
                if i % 100 == 0:
                    print(f"✓ Inserted {i} records... ({i/len(dummy_data)*100:.1f}%)")
                elif i % 10 == 0:
                    print(f"✓ Inserted {i} records...")
                
            except Exception as e:
                print(f"✗ Error inserting record {i}: {str(e)}")
                session.rollback()
        
        print(f"\nSuccessfully inserted {inserted_count} records.")
        print(f"Total records in database: {session.query(Pegawai).count()}")
        
        if include_invalid_ktp:
            print(f"\n📊 Generation Statistics:")
            print(f"• Records with invalid KTP length: {invalid_ktp_count}")
            print(f"• Records with process override (process=1): {process_override_count}")
            print(f"• Valid KTP records: {inserted_count - invalid_ktp_count}")
        
        session.close()
        
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        print("Please check your database connection settings in .env file")
        return False
    
    return True

def display_sample_data():
    """Display sample of the generated data"""
    try:
        engine = create_engine(SOURCE_DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # Get first 10 records
        records = session.query(Pegawai).limit(10).all()
        
        if records:
            print("\n" + "="*80)
            print("SAMPLE DATA (First 10 records):")
            print("="*80)
            print(f"{'ID':<5} {'Name':<25} {'Personal Number':<17} {'No_KTP':<18} {'Birth Date':<12}")
            print("-"*80)
            
            for record in records:
                bod_str = record.bod.strftime('%Y-%m-%d') if record.bod is not None else 'N/A'
                personal_num = record.personal_number or 'N/A'
                print(f"{record.id:<5} {record.name:<25} {personal_num:<17} "
                      f"{record.no_ktp:<18} {bod_str:<12}")
            
            print(f"\nTotal records: {session.query(Pegawai).count()}")
        else:
            print("No data found in database.")
        
        session.close()
        
    except Exception as e:
        print(f"Error displaying data: {str(e)}")

def clear_database():
    """Clear all data from pegawai table"""
    try:
        engine = create_engine(SOURCE_DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        count = session.query(Pegawai).count()
        
        if count == 0:
            print("Database is already empty.")
            return
        
        print(f"Database contains {count} records.")
        confirmation = input(f"Are you sure you want to delete all {count} records? (yes/no): ").lower()
        
        if confirmation == 'yes':
            session.query(Pegawai).delete()
            session.commit()
            print("All records deleted successfully.")
        else:
            print("Operation cancelled.")
        
        session.close()
        
    except Exception as e:
        print(f"Error clearing database: {str(e)}")

def main():
    """Main function with menu"""
    print("="*60)
    print("GLOBAL ID MANAGEMENT SYSTEM - DUMMY DATA GENERATOR")
    print("="*60)
    
    while True:
        print("\nOptions:")
        print("1. Populate database with dummy data (valid KTPs only)")
        print("2. Populate database with mixed data (valid + invalid KTPs)")
        print("3. Display sample data")
        print("4. Clear database")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            if populate_database(include_invalid_ktp=False):
                print("\n✓ Dummy data population completed successfully!")
            else:
                print("\n✗ Failed to populate dummy data.")
        
        elif choice == '2':
            if populate_database(include_invalid_ktp=True):
                print("\n✓ Mixed dummy data population completed successfully!")
            else:
                print("\n✗ Failed to populate dummy data.")
        
        elif choice == '3':
            display_sample_data()
        
        elif choice == '4':
            clear_database()
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # Check if faker is available
    try:
        from faker import Faker
    except ImportError:
        print("Error: 'faker' package not found.")
        print("Please install it using: pip install faker")
        sys.exit(1)
    
    main()