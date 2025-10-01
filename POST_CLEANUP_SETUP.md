# 🚀 Post-Cleanup Setup Guide

After running the cleanup script, follow these steps to restore the development environment:

## 1. Recreate Virtual Environment

```powershell
# Navigate to project directory
cd "C:\Folder Project\G_ID_engine_production"

# Create new virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 2. Install Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

## 3. Verify Environment Configuration

```powershell
# Check if .env file exists and is configured
Get-Content .env

# Make sure database connection details are correct
```

## 4. Test Database Connection

```powershell
# Run table verification script
python verify_tables.py

# Or create tables if needed
python create_tables_sqlalchemy.py
```

## 5. Start Application

```powershell
# For development (Windows)
.\start_production_8001.bat

# For production (Linux)
# ./start_production_8001.sh
```

## 6. Verify Application

- Open browser: `http://localhost:8001`
- Check API docs: `http://localhost:8001/docs`
- Test database explorer: `http://localhost:8001/database-explorer`

## 📊 Space Saved

The cleanup typically saves:
- **Virtual Environment**: 200-500 MB
- **Python Cache**: 10-50 MB  
- **Duplicate Files**: 5-20 MB
- **Sample Data**: Variable (depends on file sizes)

**Total Estimated Savings: 215-570 MB**

## 🔒 Important Files Preserved

All critical system files were preserved:
- ✅ Main application code (`main.py`, `app/`)
- ✅ Configuration files (`.env`, `requirements.txt`)
- ✅ Documentation (all `.md` files)
- ✅ Database scripts (`create_tables_sqlalchemy.py`)
- ✅ Production deployment scripts
- ✅ Ultra-performance features
- ✅ Templates and static files
- ✅ API endpoints and models

## 🚨 What Was Removed

- ❌ Virtual environment (`venv/`) - Will be recreated
- ❌ Python cache files (`__pycache__/`, `*.pyc`)
- ❌ Duplicate data generators (kept ultra version)
- ❌ Basic table creation script (kept SQLAlchemy version)
- ❌ Test/debug files (`test_dashboard_fix.py`)
- ❌ Large sample data files (if any)

## 🔧 Troubleshooting

If you encounter issues after cleanup:

1. **ModuleNotFoundError**: Ensure virtual environment is activated and dependencies installed
2. **Database Connection**: Verify `.env` file configuration
3. **Permission Errors**: Run PowerShell as Administrator if needed
4. **Port Issues**: Check if port 8001 is available

## 📝 Next Steps

1. Run the cleanup script: `.\cleanup_project.ps1`
2. Follow this setup guide
3. Test the application thoroughly
4. Consider setting up automated backups for the cleaned project