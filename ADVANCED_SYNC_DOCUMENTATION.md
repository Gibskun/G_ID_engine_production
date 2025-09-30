# Advanced Data Synchronization and Duplicate Handling Documentation

## Overview

This document describes the implementation of sophisticated data synchronization and duplicate handling logic for the Global ID (G_ID) Management System. The system implements bidirectional synchronization based on a unique composite key `(name, personal_number, no_ktp, bod)`.

## Core Components

### 1. Advanced Sync Service (`advanced_sync_service.py`)

The main service class that handles all synchronization logic.

#### Key Features:
- **Composite Key Matching**: Uses `(name, personal_number, no_ktp, bod)` as unique identifier
- **Bidirectional Sync**: Handles both file uploads and database synchronization
- **G_ID Preservation**: Maintains G_ID consistency across different data sources
- **Order Preservation**: Ensures G_ID ordering is not scrambled in target tables

### 2. Database Architecture

The system works with three main tables:

#### `global_id` (Master Table)
- Primary source of truth for all G_IDs
- Contains records from both pegawai_db and file uploads
- Source field indicates origin: `'database_pegawai'` or `'excel'`

#### `global_id_non_database` (File Records)
- Stores copies of Excel/CSV uploaded data
- Maintains same structure as global_id
- Always has source: `'excel'`

#### `pegawai` (Source Database)
- External employee database
- G_ID field populated through synchronization
- Source field indicates: `'database_pegawai'`

## Scenario Implementations

### Scenario 1: File Upload Process (Excel/CSV)

**Triggering Condition:**
A row in the uploaded file has fields `(name, personal_number, no_ktp, bod)` that exactly match a record in the `global_id` table, where the matching record originated from the `pegawai_db`.

**Implementation Logic:**

```python
def scenario_1_excel_csv_upload(self, upload_data, filename):
    for record in upload_data:
        unique_key = self.get_unique_key(record)
        existing_record = self.find_matching_record_in_global_id(unique_key, db)
        
        if existing_record:
            # MATCH FOUND: Reuse existing G_ID
            # Insert into global_id_non_database with existing G_ID
            non_db_record = GlobalIDNonDatabase(
                g_id=existing_record.g_id,  # Reuse existing G_ID
                ...
            )
            db.add(non_db_record)
        else:
            # NO MATCH: Generate new G_ID
            new_gid = self.gid_generator.generate_next_gid()
            # Insert into both global_id and global_id_non_database
```

**Key Benefits:**
- ✅ No duplicate G_IDs generated
- ✅ Maintains referential integrity
- ✅ Preserves G_ID ordering
- ✅ Tracks data lineage through source field

### Scenario 2: Direct Pegawai Database Addition

**Triggering Condition:**
A new record is added to `pegawai_db` with fields `(name, personal_number, no_ktp, bod)` that exactly match a record in the `global_id` table, where the matching record originated from a previous file upload.

**Implementation Logic:**

```python
def scenario_2_pegawai_sync(self):
    pegawai_records = db.query(Pegawai).filter(Pegawai.g_id.is_(None)).all()
    
    for pegawai_record in pegawai_records:
        unique_key = self.get_unique_key(pegawai_record)
        existing_global = self.find_matching_record_in_global_id(unique_key, db)
        
        if existing_global:
            # MATCH FOUND: Assign existing G_ID
            pegawai_record.g_id = existing_global.g_id
        else:
            # NO MATCH: Generate new G_ID and create global_id record
            new_gid = self.gid_generator.generate_next_gid()
            pegawai_record.g_id = new_gid
            # Create new global_id record
```

**Key Benefits:**
- ✅ Prevents duplicate G_ID assignment
- ✅ Links previously uploaded file data with database records
- ✅ Maintains data consistency across sources
- ✅ Automatic G_ID population for new employees

## API Reference

### Core Methods

#### `get_unique_key(record: Dict[str, Any]) -> Tuple[str, str, str, Optional[date]]`
Extracts the composite unique key from any record.

**Parameters:**
- `record`: Dictionary containing record data

**Returns:**
- Tuple of `(name, personal_number, no_ktp, bod)`

**Example:**
```python
record = {
    'name': 'John Doe',
    'personal_number': 'EMP001',
    'no_ktp': '1234567890123456',
    'bod': '1990-01-01'
}
unique_key = service.get_unique_key(record)
# Returns: ('John Doe', 'EMP001', '1234567890123456', date(1990, 1, 1))
```

#### `scenario_1_excel_csv_upload(upload_data: List[Dict], filename: str) -> Dict[str, Any]`
Processes Excel/CSV file upload with duplicate detection.

**Parameters:**
- `upload_data`: List of record dictionaries from uploaded file
- `filename`: Name of the uploaded file

**Returns:**
```python
{
    'success': bool,
    'total_records': int,
    'matched_records': int,        # Records that reused existing G_IDs
    'new_records': int,           # Records that got new G_IDs
    'error_records': int,
    'reused_gids': [              # Details of reused G_IDs
        {
            'row': int,
            'gid': str,
            'name': str,
            'match_source': str
        }
    ],
    'created_gids': [...],        # Details of newly created G_IDs
    'errors': [...]               # Error messages
}
```

#### `scenario_2_pegawai_sync() -> Dict[str, Any]`
Synchronizes pegawai database records with existing global_id records.

**Returns:**
```python
{
    'success': bool,
    'total_records': int,
    'matched_records': int,        # Records assigned existing G_IDs
    'new_records': int,           # Records that got new G_IDs
    'assigned_gids': [            # G_IDs assigned from existing records
        {
            'pegawai_id': int,
            'gid': str,
            'name': str
        }
    ],
    'created_gids': [...],        # New G_IDs created
    'errors': [...]
}
```

### File Processing Methods

#### `process_excel_csv_upload(file_content: bytes, filename: str) -> Dict[str, Any]`
Main entry point for file upload processing.

**Parameters:**
- `file_content`: Binary content of uploaded file
- `filename`: Name of uploaded file (determines processing method)

**Supported Formats:**
- Excel: `.xlsx`, `.xls`
- CSV: `.csv`

#### `sync_pegawai_database() -> Dict[str, Any]`
Main entry point for pegawai database synchronization.

## Integration Examples

### Flask Integration

```python
from flask import Flask, request, jsonify
from advanced_sync_service import AdvancedSyncService

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Process the file
    sync_service = AdvancedSyncService()
    result = sync_service.process_excel_csv_upload(
        file.read(), 
        file.filename
    )
    
    return jsonify(result)

@app.route('/sync-pegawai', methods=['POST'])
def sync_pegawai():
    sync_service = AdvancedSyncService()
    result = sync_service.sync_pegawai_database()
    return jsonify(result)
```

### Command Line Usage

```python
from advanced_sync_service import AdvancedSyncService

# Create service
service = AdvancedSyncService()

# Process a file
with open('employees.xlsx', 'rb') as f:
    result = service.process_excel_csv_upload(f.read(), 'employees.xlsx')
    print(f"Upload result: {result}")

# Sync pegawai database
sync_result = service.sync_pegawai_database()
print(f"Sync result: {sync_result}")
```

## Data Flow Diagrams

### Scenario 1: File Upload with Match
```
Excel/CSV File → Validation → Unique Key Extraction → Global_ID Lookup
                                                            ↓
                                                       Match Found?
                                                       ↙        ↘
                                                   Yes           No
                                                    ↓             ↓
                                          Reuse Existing G_ID  Generate New G_ID
                                                    ↓             ↓
                                         Insert to Non_DB     Insert to Both Tables
```

### Scenario 2: Pegawai Sync with Match
```
Pegawai Records (no G_ID) → Unique Key Extraction → Global_ID Lookup
                                                           ↓
                                                    Match Found?
                                                    ↙        ↘
                                                Yes           No
                                                 ↓             ↓
                                      Assign Existing G_ID  Generate New G_ID
                                                 ↓             ↓
                                         Update Pegawai   Create Global_ID & 
                                                          Update Pegawai
```

## Testing

### Unit Tests
Run the comprehensive test suite:

```bash
python test_advanced_sync.py
```

### Test Coverage
- ✅ Scenario 1: File upload with matches
- ✅ Scenario 2: Pegawai sync with matches
- ✅ File processing integration
- ✅ Validation error handling
- ✅ Database state verification

### Manual Testing
The test suite includes manual testing functions that demonstrate real-world usage:

```python
# Run manual demonstration
from test_advanced_sync import run_manual_test
run_manual_test()
```

## Performance Considerations

### Optimizations Implemented
1. **Batch Processing**: Records processed in batches to reduce database round trips
2. **In-Memory Duplicate Detection**: Uses sets for fast duplicate checking
3. **Efficient Queries**: Optimized SQL queries with proper indexing
4. **Transaction Management**: Proper commit/rollback handling

### Recommended Batch Sizes
- **File Upload**: Process up to 1000 records per batch
- **Pegawai Sync**: Process up to 500 records per batch
- **Large Files**: Consider chunking files > 10MB

## Error Handling

### Validation Errors
- Missing required fields (`name`, `no_ktp`)
- Invalid `no_ktp` format (must be 16 digits)
- Invalid date formats for `bod`

### Processing Errors
- Database connection failures
- Duplicate key violations
- File format issues

### Recovery Mechanisms
- Transaction rollback on errors
- Detailed error logging
- Partial success reporting

## Security Considerations

### Data Validation
- Input sanitization for all fields
- SQL injection prevention through parameterized queries
- File type validation

### Access Control
- Database connection through secure credentials
- Audit logging for all operations
- Change tracking through audit_log table

## Migration and Deployment

### Prerequisites
- PostgreSQL databases: `global_id_db`, `pegawai_db`
- Required Python packages: `pandas`, `sqlalchemy`, `psycopg2`
- Proper database schema (see `sql/create_schema.sql`)

### Deployment Steps
1. Deploy `advanced_sync_service.py` to server
2. Update database connection strings
3. Run test suite to verify functionality
4. Integrate with existing web application
5. Configure monitoring and logging

## Troubleshooting

### Common Issues
1. **Database Connection Errors**: Check connection strings and credentials
2. **Duplicate Key Violations**: Verify unique constraints on tables
3. **Date Parsing Errors**: Ensure consistent date formats (YYYY-MM-DD)
4. **Memory Issues with Large Files**: Use batch processing for files > 50MB

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- [ ] Real-time synchronization triggers
- [ ] Advanced conflict resolution
- [ ] Batch file processing queue
- [ ] Performance monitoring dashboard
- [ ] Advanced duplicate detection algorithms

### API Extensions
- [ ] REST API endpoints
- [ ] Webhook notifications
- [ ] File upload progress tracking
- [ ] Scheduled synchronization jobs