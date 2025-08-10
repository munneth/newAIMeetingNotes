from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to the Meeting Notes API',
        'status': 'running'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'meeting-notes-api'
    })

@app.route('/api/meetings', methods=['GET'])
def get_meetings():
    # Placeholder for getting meetings
    return jsonify({
        'meetings': [],
        'message': 'Meetings endpoint - implement logic here'
    })

@app.route('/api/meetings', methods=['POST'])
def create_meeting():
    data = request.get_json()
    
    if not data or 'link' not in data:
        return jsonify({'error': 'Meeting link is required'}), 400
    
    # Placeholder for creating meeting
    meeting = {
        'id': 'temp-id',
        'link': data['link'],
        'duration': data.get('duration'),
        'created_at': '2024-01-01T00:00:00Z'
    }
    
    return jsonify({
        'success': True,
        'meeting': meeting
    }), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
