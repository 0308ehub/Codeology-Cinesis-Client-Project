"""
Configuration file template.
Copy to config.py and update with your settings.
"""
import os

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///carrier_data.db')

# API Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 5000))
API_DEBUG = os.getenv('API_DEBUG', 'True').lower() == 'true'

# File Upload Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 16 * 1024 * 1024))  # 16MB
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'pdf'}

# Enrichment Configuration
ENRICHMENT_ENABLED = os.getenv('ENRICHMENT_ENABLED', 'True').lower() == 'true'
DAT_API_KEY = os.getenv('DAT_API_KEY', '')
TRUCKSTOP_API_KEY = os.getenv('TRUCKSTOP_API_KEY', '')
FMCSA_API_KEY = os.getenv('FMCSA_API_KEY', '')

# Matching Configuration
MATCH_LIMIT_DEFAULT = int(os.getenv('MATCH_LIMIT_DEFAULT', 10))
MATCH_SCORE_THRESHOLD = float(os.getenv('MATCH_SCORE_THRESHOLD', 0.3))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'carrier_processor.log')

