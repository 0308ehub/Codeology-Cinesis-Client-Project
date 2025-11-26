"""
REST API for carrier data processing and load matching.
Provides endpoints for onboarding, matching, and data management.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from typing import Dict, Any
from pathlib import Path

from database import Database
from onboarding import OnboardingFlow
from load_matching import LoadMatchingEngine
from schema import CarrierProfile, Load, DataSource

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize services
database = Database()
onboarding_flow = OnboardingFlow(database)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'carrier-data-processor'
    }), 200


@app.route('/api/v1/onboard', methods=['POST'])
def onboard_carrier():
    """
    Onboard a carrier by uploading files.
    
    Request:
        - files: List of files (CSV, Excel, PDF)
        - carrier_name: Optional carrier name
        - carrier_mc: Optional carrier MC number
    
    Response:
        - carrier_id: Generated carrier ID
        - stats: Processing statistics
        - errors: List of errors
        - warnings: List of warnings
    """
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    carrier_name = request.form.get('carrier_name')
    carrier_mc = request.form.get('carrier_mc')
    
    saved_files = []
    try:
        # Save uploaded files
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                saved_files.append(filepath)
            else:
                return jsonify({'error': f'Invalid file type: {file.filename}'}), 400
        
        # Process files
        results = onboarding_flow.process_upload(
            saved_files,
            carrier_name=carrier_name,
            carrier_mc=carrier_mc
        )
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up uploaded files
        for filepath in saved_files:
            try:
                os.remove(filepath)
            except:
                pass


@app.route('/api/v1/carrier/<carrier_id>/status', methods=['GET'])
def get_carrier_status(carrier_id: str):
    """Get onboarding status for a carrier"""
    try:
        status = onboarding_flow.get_onboarding_status(carrier_id)
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/carrier/<carrier_id>/matches', methods=['POST'])
def get_load_matches(carrier_id: str):
    """
    Get load matches for a carrier.
    
    Request body:
        - loads: List of available loads (JSON)
        - limit: Maximum number of matches (default: 10)
    
    Response:
        - matches: List of matched loads with scores
        - summary: Match summary statistics
    """
    try:
        data = request.get_json()
        loads_data = data.get('loads', [])
        limit = data.get('limit', 10)
        
        # Convert load data to Load objects
        # This is simplified - in production, use proper deserialization
        available_loads = []
        for load_data in loads_data:
            # Create Load object from data
            # Note: This is a simplified version
            load = Load(
                load_id=load_data.get('load_id'),
                source=DataSource.MANUAL
            )
            available_loads.append(load)
        
        # Generate matches
        results = onboarding_flow.generate_matches(carrier_id, available_loads, limit)
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/carrier/<carrier_id>/profile', methods=['GET'])
def get_carrier_profile(carrier_id: str):
    """Get carrier profile"""
    try:
        profile = database.get_carrier_profile(carrier_id)
        if not profile:
            return jsonify({'error': 'Carrier not found'}), 404
        
        # Convert to dict
        # In production, use proper serialization
        return jsonify({
            'carrier_id': profile.carrier_id,
            'carrier_name': profile.carrier_name,
            'mc_number': profile.mc_number,
            # ... add more fields
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        # In production, query database for real stats
        return jsonify({
            'total_carriers': 0,
            'total_loads': 0,
            'total_brokers': 0,
            'total_lanes': 0
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5001)

