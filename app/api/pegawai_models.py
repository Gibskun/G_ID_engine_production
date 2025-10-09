"""
Pydantic models for Pegawai REST API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, datetime
import re


class PegawaiCreateRequest(BaseModel):
    """Request model for creating a new employee"""
    name: str = Field(..., min_length=1, max_length=255, description="Employee full name")
    personal_number: Optional[str] = Field(None, max_length=15, description="Employee personal number")
    no_ktp: Optional[str] = Field(None, max_length=50, description="Employee KTP number (any format, up to 50 characters)")
    passport_id: Optional[str] = Field(None, max_length=50, description="Employee passport ID (any format, up to 50 characters)")
    bod: Optional[date] = Field(None, description="Birth date (YYYY-MM-DD)")
    
    @validator('no_ktp')
    def validate_no_ktp(cls, v):
        """Clean KTP number - accept any format"""
        if v and str(v).strip() in ['nan', 'NaN', 'NULL', 'null', '']:
            return None
        return v.strip() if v else None
    
    @validator('passport_id')
    def validate_passport_id(cls, v):
        """Clean passport ID - accept any format"""
        if v and str(v).strip() in ['nan', 'NaN', 'NULL', 'null', '']:
            return None
        return v.strip() if v else None
        
        v = v.strip().upper()
        
        if len(v) < 8 or len(v) > 9:
            raise ValueError('Passport ID must be 8-9 characters long')
        
        # Check if first character is a letter
        if not v[0].isalpha():
            raise ValueError('Passport ID must start with a letter')
        
        # Check if all characters are alphanumeric
        if not v.isalnum():
            raise ValueError('Passport ID can only contain letters and numbers')
        
        # Count letters and numbers
        letter_count = sum(1 for c in v if c.isalpha())
        number_count = sum(1 for c in v if c.isdigit())
        
        # Numbers must dominate (be more than letters)
        if number_count <= letter_count:
            raise ValueError('Passport ID must have more numbers than letters')
        
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Validate and clean name"""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('personal_number')
    def validate_personal_number(cls, v):
        """Validate personal number if provided"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 15:
                raise ValueError('Personal number cannot exceed 15 characters')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "personal_number": "EMP001",
                "no_ktp": "1234567890123456",
                "bod": "1990-01-01"
            }
        }


class PegawaiUpdateRequest(BaseModel):
    """Request model for updating an existing employee"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Employee full name")
    personal_number: Optional[str] = Field(None, max_length=15, description="Employee personal number")
    no_ktp: Optional[str] = Field(None, max_length=50, description="Employee KTP number (any format, up to 50 characters)")
    passport_id: Optional[str] = Field(None, max_length=50, description="Employee passport ID (any format, up to 50 characters)")
    bod: Optional[date] = Field(None, description="Birth date (YYYY-MM-DD)")
    
    @validator('no_ktp')
    def validate_no_ktp(cls, v):
        """Clean KTP number - accept any format"""
        if v and str(v).strip() in ['nan', 'NaN', 'NULL', 'null', '']:
            return None
        return v.strip() if v else None
    
    @validator('passport_id')
    def validate_passport_id(cls, v):
        """Clean passport ID - accept any format"""
        if v and str(v).strip() in ['nan', 'NaN', 'NULL', 'null', '']:
            return None
        return v.strip() if v else None
    
    @validator('name')
    def validate_name(cls, v):
        """Validate and clean name"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty')
        return v
    
    @validator('personal_number')
    def validate_personal_number(cls, v):
        """Validate personal number if provided"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 15:
                raise ValueError('Personal number cannot exceed 15 characters')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe Updated",
                "personal_number": "EMP001",
                "no_ktp": "1234567890123456",
                "bod": "1990-01-01"
            }
        }


class PegawaiResponse(BaseModel):
    """Response model for employee data"""
    id: int = Field(..., description="Employee ID")
    name: str = Field(..., description="Employee full name")
    personal_number: Optional[str] = Field(None, description="Employee personal number")
    no_ktp: str = Field(..., description="Employee KTP number")
    passport_id: str = Field(..., description="Employee passport ID")
    bod: Optional[date] = Field(None, description="Birth date")
    g_id: Optional[str] = Field(None, description="Assigned Global ID")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft deletion timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "personal_number": "EMP001",
                "no_ktp": "1234567890123456",
                "bod": "1990-01-01",
                "g_id": "G025AA01",
                "created_at": "2025-01-01T10:00:00",
                "updated_at": "2025-01-01T10:00:00",
                "deleted_at": None
            }
        }


class PegawaiListResponse(BaseModel):
    """Response model for paginated employee list"""
    total_count: int = Field(..., description="Total number of employees")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    employees: list[PegawaiResponse] = Field(..., description="List of employees")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 100,
                "page": 1,
                "size": 20,
                "total_pages": 5,
                "employees": [
                    {
                        "id": 1,
                        "name": "John Doe",
                        "personal_number": "EMP001",
                        "no_ktp": "1234567890123456",
                        "bod": "1990-01-01",
                        "g_id": "G025AA01",
                        "created_at": "2025-01-01T10:00:00",
                        "updated_at": "2025-01-01T10:00:00",
                        "deleted_at": None
                    }
                ]
            }
        }


class PegawaiCreateResponse(BaseModel):
    """Response model for employee creation"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation result message")
    employee: PegawaiResponse = Field(..., description="Created employee data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Employee created successfully",
                "employee": {
                    "id": 1,
                    "name": "John Doe",
                    "personal_number": "EMP001",
                    "no_ktp": "1234567890123456",
                    "bod": "1990-01-01",
                    "g_id": None,
                    "created_at": "2025-01-01T10:00:00",
                    "updated_at": "2025-01-01T10:00:00",
                    "deleted_at": None
                }
            }
        }


class PegawaiUpdateResponse(BaseModel):
    """Response model for employee update"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation result message")
    employee: PegawaiResponse = Field(..., description="Updated employee data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Employee updated successfully",
                "employee": {
                    "id": 1,
                    "name": "John Doe Updated",
                    "personal_number": "EMP001",
                    "no_ktp": "1234567890123456",
                    "bod": "1990-01-01",
                    "g_id": "G025AA01",
                    "created_at": "2025-01-01T10:00:00",
                    "updated_at": "2025-01-01T12:00:00",
                    "deleted_at": None
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Validation error",
                "detail": "Required field missing"
            }
        }