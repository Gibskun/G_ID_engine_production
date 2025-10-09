# Global ID Tables Download Feature Implementation

## Overview
Added new download functionality for the Global ID tables on the database explorer page, allowing users to download complete data from both `global_id` and `global_id_non_database` tables.

## New Features Added

### 1. API Endpoints
**File:** `app/api/routes.py`

#### Global ID Table Export Endpoint
- **URL:** `/api/v1/global-id-table/export`
- **Method:** GET
- **Parameters:**
  - `format`: csv|excel (default: csv)
  - `separator`: ,|;|| (for CSV format, default: ,)
- **Response:** Downloads all records from `global_id` table
- **Filename format:** `global_id_table_export_YYYYMMDD_HHMMSS.csv/xlsx`

#### Global ID Non-Database Export Endpoint
- **URL:** `/api/v1/global-id-non-database/export`
- **Method:** GET
- **Parameters:**
  - `format`: csv|excel (default: csv)
  - `separator`: ,|;|| (for CSV format, default: ,)
- **Response:** Downloads all records from `global_id_non_database` table
- **Filename format:** `global_id_non_database_export_YYYYMMDD_HHMMSS.csv/xlsx`

### 2. Frontend Interface
**File:** `templates/database_explorer.html`

#### New Section: "Global ID Tables Data Download"
- Added between the "View SAP Employee Data" button and "SAP Export Section"
- Two-column layout with side-by-side download controls

#### Download Controls
**Left Column - Global ID Table:**
- Export format selector (CSV/Excel)
- CSV separator options (comma, semicolon, pipe)
- "Download Global ID Table" button (blue styling)

**Right Column - Global ID Non-Database Table:**
- Export format selector (CSV/Excel)
- CSV separator options (comma, semicolon, pipe)
- "Download Global ID Non-Database" button (info styling)

#### JavaScript Functions
- `downloadGlobalIdTable()` - Handles global_id table downloads
- `downloadGlobalIdNonDatabase()` - Handles global_id_non_database table downloads
- Event listeners for format changes to show/hide CSV separator options
- Progress indicators and success/error messages

## Data Structure

### Global ID Table Export Fields:
- g_id: Global ID identifier
- name: Employee name
- personal_number: Personal number
- no_ktp: KTP number
- passport_id: Passport ID
- bod: Birth date
- status: Record status (Active/Non Active)
- source: Data source
- created_at: Creation timestamp
- updated_at: Last update timestamp

### Global ID Non-Database Table Export Fields:
- g_id: Global ID identifier
- name: Employee name
- personal_number: Personal number
- no_ktp: KTP number
- passport_id: Passport ID
- bod: Birth date
- status: Record status (Active/Non Active)
- source: Data source
- created_at: Creation timestamp
- updated_at: Last update timestamp

## User Interface Features

### Visual Design
- **Section Header:** Database icon with "Global ID Tables Data Download" title
- **Layout:** Responsive two-column grid layout
- **Color Coding:** 
  - Global ID Table: Primary blue buttons
  - Global ID Non-Database: Info blue buttons
- **Icons:** Table and file-excel icons for visual distinction

### User Experience
- **Format Selection:** Dropdown for CSV/Excel choice
- **CSV Options:** Separator selection (comma, semicolon, pipe)
- **Dynamic UI:** CSV separator options only shown when CSV format selected
- **Progress Feedback:** Spinner animation during download
- **Status Messages:** Success/error alerts using existing UIUtils
- **File Naming:** Timestamped filenames for organization

### Error Handling
- Connection error handling
- Empty dataset validation
- User-friendly error messages
- Button state management during downloads

## Benefits

1. **Complete Data Access:** Users can download full datasets from both Global ID tables
2. **Format Flexibility:** Support for both CSV and Excel formats
3. **Customizable CSV:** Multiple separator options for different regional preferences
4. **Quick Access:** Direct download without complex filtering
5. **Backup Capability:** Easy way to create complete data backups
6. **Analysis Support:** Download data for external analysis tools

## Usage Instructions

1. **Navigate** to the Database Explorer page
2. **Locate** the "Global ID Tables Data Download" section
3. **Choose** the table you want to download from:
   - Global ID Table (main records)
   - Global ID Non-Database Table (Excel import data)
4. **Select** export format (CSV or Excel)
5. **Choose** CSV separator if using CSV format
6. **Click** the download button
7. **File** will automatically download with timestamped filename

## Integration with Existing Features

- **Consistent UI:** Uses same styling as existing export sections
- **Compatible API:** Follows same patterns as other export endpoints
- **Error Handling:** Uses existing UIUtils for consistent messaging
- **Responsive Design:** Adapts to different screen sizes like other sections

## Technical Implementation Details

### API Response Handling
- Pandas DataFrame for data processing
- Proper date formatting (YYYY-MM-DD for dates, YYYY-MM-DD HH:MM:SS for timestamps)
- HTTP response headers for file downloads
- Appropriate MIME types for CSV and Excel

### Frontend JavaScript
- Async/await pattern for API calls
- Event-driven format selection
- DOM manipulation for dynamic UI updates
- Error boundary with try/catch blocks

### Security Considerations
- Uses existing database session dependencies
- No additional authentication required (inherits from page access)
- Query parameters properly encoded
- No SQL injection vulnerabilities (uses ORM queries)

This implementation provides users with comprehensive access to their Global ID data while maintaining consistency with the existing application design and functionality.