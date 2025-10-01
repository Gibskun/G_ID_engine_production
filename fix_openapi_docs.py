#!/usr/bin/env python3
"""
OpenAPI/Swagger Documentation Fix Script
This script validates and fixes common issues with FastAPI OpenAPI generation
"""

import sys
import os
sys.path.append('/var/www/G_ID_engine_production')

from main import app
import json
from datetime import datetime

def test_openapi_generation():
    """Test if OpenAPI schema can be generated without errors"""
    try:
        print("🔍 Testing OpenAPI schema generation...")
        schema = app.openapi()
        
        # Check required fields
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in schema:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Check version field in info
        if 'version' not in schema.get('info', {}):
            print("❌ Missing version field in info section")
            return False
            
        print("✅ OpenAPI schema generation successful!")
        print(f"   - OpenAPI Version: {schema.get('openapi', 'Unknown')}")
        print(f"   - API Version: {schema['info'].get('version', 'Unknown')}")
        print(f"   - Title: {schema['info'].get('title', 'Unknown')}")
        print(f"   - Endpoints: {len(schema.get('paths', {}))}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAPI schema generation failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return False

def validate_routes():
    """Validate all registered routes"""
    try:
        print("\n🛣️  Validating registered routes...")
        
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods) if route.methods else [],
                    'name': getattr(route, 'name', 'unnamed')
                })
        
        print(f"✅ Found {len(routes)} routes:")
        for route in routes[:10]:  # Show first 10
            methods = ', '.join(route['methods']) if route['methods'] else 'N/A'
            print(f"   - {methods:12} {route['path']}")
        
        if len(routes) > 10:
            print(f"   ... and {len(routes) - 10} more routes")
            
        return True
        
    except Exception as e:
        print(f"❌ Route validation failed: {str(e)}")
        return False

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        print("\n📦 Checking dependencies...")
        
        dependencies = [
            'fastapi',
            'uvicorn', 
            'pydantic',
            'sqlalchemy',
            'python-dotenv'
        ]
        
        missing = []
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"   ✅ {dep}")
            except ImportError:
                print(f"   ❌ {dep} - MISSING")
                missing.append(dep)
        
        if missing:
            print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
            return False
        else:
            print("✅ All dependencies available")
            return True
            
    except Exception as e:
        print(f"❌ Dependency check failed: {str(e)}")
        return False

def export_openapi_schema():
    """Export OpenAPI schema to file for debugging"""
    try:
        print("\n💾 Exporting OpenAPI schema...")
        
        schema = app.openapi()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"openapi_schema_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(schema, f, indent=2, default=str)
        
        print(f"✅ Schema exported to: {filename}")
        print(f"   File size: {os.path.getsize(filename)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema export failed: {str(e)}")
        return False

def main():
    """Main diagnostic function"""
    print("🚀 FastAPI OpenAPI Diagnostic Tool")
    print("=" * 50)
    
    success_count = 0
    total_tests = 4
    
    # Run tests
    if test_openapi_generation():
        success_count += 1
    
    if validate_routes():
        success_count += 1
        
    if check_dependencies():
        success_count += 1
        
    if export_openapi_schema():
        success_count += 1
    
    # Summary
    print(f"\n📊 Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✅ All tests passed! Your FastAPI app should work correctly.")
        print("\n💡 If Swagger UI still doesn't work:")
        print("   1. Restart the service: sudo systemctl restart gid-system.service")
        print("   2. Clear browser cache")
        print("   3. Check nginx configuration")
        print("   4. Verify SSL certificates")
    else:
        print("❌ Some tests failed. Check the errors above.")
        print("\n🔧 Suggested fixes:")
        print("   1. Check import statements in your router files")
        print("   2. Verify all Pydantic models are properly defined")
        print("   3. Check for circular imports")
        print("   4. Ensure all dependencies are installed")
    
    return success_count == total_tests

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Diagnostic interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)