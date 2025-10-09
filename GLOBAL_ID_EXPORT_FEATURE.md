# Global ID Table Export & Passport_ID Analysis Feature

## Overview
Added comprehensive export functionality for the global_id table with detailed passport_id field analysis to help identify and resolve empty passport_id issues.

## New Features Added

### 1. Export API Endpoints

#### `/api/v1/global-id/export`
- **Purpose**: Export all global_id table data
- **Formats**: CSV, Excel (.xlsx)
- **Parameters**:
  - `format`: "csv" or "excel" (default: csv)
  - `separator`: CSV separator - ",", ";", "|" (default: comma)
  - `include_empty_passport`: Include records with empty passport_id (default: true)

#### `/api/v1/global-id/stats`
- **Purpose**: Get detailed statistics about the global_id table
- **Returns**:
  - Total record count
  - Valid vs empty passport_id counts and percentages
  - Status distribution (Active, Inactive, etc.)
  - Source distribution (database_pegawai, excel, etc.)
  - Sample records with empty passport_id for debugging

### 2. Database Explorer UI Enhancement

#### New Export Section
- **Location**: Database Explorer page (after SAP data section)
- **Features**:
  - Real-time table statistics display
  - Export format selection (CSV/Excel)
  - CSV separator options (comma, semicolon, pipe)
  - Filter option to include/exclude empty passport_id records
  - One-click export with progress indication

#### Statistics Dashboard
- **Total Records**: Shows complete count with formatting
- **Passport_ID Analysis**: 
  - Valid passport_id count and percentage
  - Empty passport_id count and percentage
  - Color-coded indicators (green for valid, yellow for empty)
- **Distribution Charts**:
  - Status distribution badges
  - Source distribution badges
- **Sample Data**: Table showing first 5 records with empty passport_id for debugging

### 3. JavaScript Functions

#### `loadGlobalIdStats()`
- Fetches and displays table statistics
- Updates the statistics dashboard
- Shows sample records with empty passport_id

#### `exportGlobalIdData()`
- Handles export button clicks
- Constructs download URLs with user preferences
- Triggers file download
- Shows success/error messages

#### `updateStatsDisplay(stats)`
- Updates the statistics UI
- Formats numbers with locale-specific separators
- Generates status and source distribution badges
- Creates sample data table

## Usage Instructions

### 1. Access the Export Feature
1. Navigate to: `Database Explorer` page
2. Scroll down to "Global ID Data Export & Analysis" section
3. View current table statistics

### 2. Export Data
1. Select export format (CSV or Excel)
2. For CSV: Choose separator (comma, semicolon, or pipe)
3. Choose whether to include records with empty passport_id
4. Click "Export" button
5. File will download automatically

### 3. Analyze Passport_ID Issues
1. Check the statistics section for empty passport_id percentage
2. Review sample records with empty passport_id
3. Note the source distribution to identify problematic data sources
4. Use the "Only records with passport_id" filter to export clean data

## Technical Implementation

### Backend (FastAPI)
- New route handlers in `app/api/routes.py`
- Uses pandas for data processing and export
- Supports multiple export formats and separators
- Comprehensive error handling and validation

### Frontend (JavaScript)
- New section in `templates/database_explorer.html`
- Responsive design with Bootstrap styling
- Real-time statistics loading
- Progress indicators and user feedback

### Database Integration
- Uses existing SQLAlchemy models
- Optimized queries for statistics gathering
- Handles null/empty passport_id detection

## Troubleshooting Empty Passport_ID

### Common Causes
1. **Legacy Data**: Records imported before passport_id was required
2. **Excel Import Issues**: CSV/Excel files missing passport_id column
3. **Validation Bypass**: Data inserted without proper validation
4. **Manual Entry**: Records added through API without passport_id

### Solutions
1. **Use Export Feature**: Export records with empty passport_id
2. **Data Cleanup**: Use the sample records to identify patterns
3. **Re-import Data**: Use proper templates with passport_id column
4. **Update Records**: Manually add missing passport_id values

## Files Modified
- `app/api/routes.py`: Added export and statistics endpoints
- `templates/database_explorer.html`: Added export UI and JavaScript functions

## Benefits
- ✅ Complete data export capability
- ✅ Passport_ID issue identification and analysis
- ✅ Multiple export formats supported
- ✅ User-friendly interface with real-time statistics
- ✅ Debugging tools for data quality issues
- ✅ Flexible filtering options

This feature provides comprehensive tools for data export and passport_id field analysis, helping users identify and resolve data quality issues in the global_id table.