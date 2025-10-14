"""
Environment Configuration Manager
Automatically detects whether running locally or on server and applies appropriate settings
"""

import os
import socket
from typing import Dict, Any
from dotenv import load_dotenv

class EnvironmentConfig:
    """Manages environment-specific configuration"""
    
    def __init__(self):
        load_dotenv()
        self.environment = self._detect_environment()
        self._apply_environment_config()
    
    @property
    def database_server(self):
        """Get database server address"""
        return os.getenv('DATABASE_HOST', '127.0.0.1')
    
    @property
    def database_port(self):
        """Get database port"""
        return os.getenv('DATABASE_PORT', '1435')
    
    @property
    def app_host(self):
        """Get application host"""
        return os.getenv('APP_HOST', '127.0.0.1')
    
    @property
    def app_port(self):
        """Get application port"""
        return os.getenv('APP_PORT', '8000')
    
    def _detect_environment(self) -> str:
        """Detect if running locally or on server"""
        try:
            # Check if we're on the GCP server
            hostname = socket.gethostname()
            
            # Server indicators
            if any(indicator in hostname.lower() for indicator in ['gcp', 'ubuntu', 'debian']):
                return 'server'
            
            # Check for server-specific paths
            if os.path.exists('/var/www/G_ID_engine_production'):
                return 'server'
            
            # Check if we can connect directly to the database server (server environment)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('10.182.128.3', 1433))
                sock.close()
                if result == 0:
                    return 'server'
            except:
                pass
            
            # Default to local if none of the above
            return 'local'
            
        except Exception:
            # Default to local on any error
            return 'local'
    
    def _apply_environment_config(self):
        """Apply environment-specific configuration"""
        if self.environment == 'server':
            self._apply_server_config()
        else:
            self._apply_local_config()
    
    def _apply_server_config(self):
        """Apply server-specific configuration"""
        # Override with server settings
        os.environ.setdefault('DATABASE_URL', 
            'mssql+pyodbc://sqlvendor1:1U~xO%602Un-gGqmPj@10.182.128.3:1433/gid_dev?driver=ODBC+Driver+17+for+SQL+Server')
        os.environ.setdefault('SOURCE_DATABASE_URL', 
            'mssql+pyodbc://sqlvendor1:1U~xO%602Un-gGqmPj@10.182.128.3:1433/gid_dev?driver=ODBC+Driver+17+for+SQL+Server')
        
        os.environ.setdefault('DATABASE_HOST', '10.182.128.3')
        os.environ.setdefault('DATABASE_PORT', '1433')
        os.environ.setdefault('APP_HOST', '0.0.0.0')
        os.environ.setdefault('APP_PORT', '8001')
        os.environ.setdefault('DEBUG', 'False')
        
        # Server performance settings
        os.environ.setdefault('DATABASE_POOL_SIZE', '20')
        os.environ.setdefault('DATABASE_MAX_OVERFLOW', '30')
        os.environ.setdefault('DATABASE_POOL_TIMEOUT', '30')
        os.environ.setdefault('DATABASE_POOL_RECYCLE', '3600')
        os.environ.setdefault('QUERY_TIMEOUT', '60')
        
        print("🖥️  Server environment detected - using direct database connection")
    
    def _apply_local_config(self):
        """Apply local development configuration"""
        # Use tunnel configuration for local development
        os.environ.setdefault('DATABASE_URL', 
            'mssql+pyodbc://sqlvendor1:1U~xO%602Un-gGqmPj@127.0.0.1:1435/gid_dev?driver=ODBC+Driver+17+for+SQL+Server')
        os.environ.setdefault('SOURCE_DATABASE_URL', 
            'mssql+pyodbc://sqlvendor1:1U~xO%602Un-gGqmPj@127.0.0.1:1435/gid_dev?driver=ODBC+Driver+17+for+SQL+Server')
        
        os.environ.setdefault('DATABASE_HOST', '127.0.0.1')
        os.environ.setdefault('DATABASE_PORT', '1435')
        os.environ.setdefault('APP_HOST', '127.0.0.1')
        os.environ.setdefault('APP_PORT', '8000')
        os.environ.setdefault('DEBUG', 'True')
        
        # Local performance settings (smaller pool for local dev)
        os.environ.setdefault('DATABASE_POOL_SIZE', '5')
        os.environ.setdefault('DATABASE_MAX_OVERFLOW', '10')
        os.environ.setdefault('DATABASE_POOL_TIMEOUT', '10')
        os.environ.setdefault('DATABASE_POOL_RECYCLE', '1800')
        os.environ.setdefault('QUERY_TIMEOUT', '30')
        
        print("💻 Local environment detected - using SSH tunnel (127.0.0.1:1435)")
        print("   Make sure SSH tunnel is running:")
        print("   gcloud compute start-iap-tunnel gcp-hr-applications 1433 --local-host-port=localhost:1435 --zone=asia-southeast2-a")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            'environment': self.environment,
            'database_url': os.getenv('DATABASE_URL'),
            'database_host': os.getenv('DATABASE_HOST'),
            'database_port': os.getenv('DATABASE_PORT'),
            'app_host': os.getenv('APP_HOST'),
            'app_port': int(os.getenv('APP_PORT', 8000)),
            'debug': os.getenv('DEBUG', 'True').lower() == 'true',
            'pool_size': int(os.getenv('DATABASE_POOL_SIZE', 5)),
            'max_overflow': int(os.getenv('DATABASE_MAX_OVERFLOW', 10)),
            'pool_timeout': int(os.getenv('DATABASE_POOL_TIMEOUT', 10)),
            'pool_recycle': int(os.getenv('DATABASE_POOL_RECYCLE', 1800)),
            'query_timeout': int(os.getenv('QUERY_TIMEOUT', 30))
        }
    
    def print_config(self):
        """Print current configuration for debugging"""
        config = self.get_config()
        print("\n🔧 Current Configuration:")
        print(f"   Environment: {config['environment']}")
        print(f"   Database Host: {config['database_host']}:{config['database_port']}")
        print(f"   App Host: {config['app_host']}:{config['app_port']}")
        print(f"   Debug Mode: {config['debug']}")
        print(f"   Pool Size: {config['pool_size']}")
        print(f"   Query Timeout: {config['query_timeout']}s")
        print()

# Global configuration instance
env_config = EnvironmentConfig()