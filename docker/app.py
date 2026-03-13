import os
import sys
import tempfile
import zipfile
import shutil
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, send_file, jsonify, after_this_request

# Ensure we can import spatialmedia
# Assuming the Dockerfile places spatialmedia in a reachable location or we are running from root
try:
    from spatialmedia import metadata_utils
    from spatialmedia import mpeg
except ImportError:
    # Fallback for local dev if running from docker folder
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from spatialmedia import metadata_utils
    from spatialmedia import mpeg

app = Flask(__name__)
# Use a static path so all workers access the same directory
# Also allows mounting a volume to /app/uploads
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/app/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB max upload

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Console:
    def __init__(self):
        self.log = []
    def append(self, text):
        self.log.append(text)
    def __call__(self, text):
        self.append(text)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    uploaded_files = []
    
    for file in files:
        if file.filename == '':
            continue
        
        # Reject files that contain directory separators or '..'
        normalized_filename = file.filename.replace('\\', '/')
        if '/' in normalized_filename or '..' in normalized_filename:
            return jsonify({'error': f'Invalid filename detected: {file.filename}'}), 400
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Analyze file skipped as per user request
        
        metadata_info = {
            'filename': filename,
            'spherical': False,
            'stereo': 'none',
            'audio': False,
            'audio_desc': 'Unknown'
        }
        
        uploaded_files.append(metadata_info)
        
    return jsonify({'files': uploaded_files})

@app.route('/inject', methods=['POST'])
def inject_metadata():
    data = request.json
    files_to_process = data.get('files', [])
    options = data.get('options', {})
    
    if not files_to_process:
        return jsonify({'error': 'No files specified'}), 400

    stereo_mode = "none"
    if options.get('stereo'): # Checkbox for 3D
         stereo_mode = "top-bottom" # As per GUI logic
    
    metadata = metadata_utils.Metadata()
    if options.get('spherical'):
        metadata.video = metadata_utils.generate_spherical_xml(stereo=stereo_mode)
    
    # Audio handling logic copied from gui.py
    # Note: In the GUI 'spatial_audio' checkbox is only enabled if supported.
    # We will assume backend logic needs to re-verify or trust frontend.
    # For now, simplistic approach:
    
    results = []
    
    for raw_filename in files_to_process:
        normalized_filename = raw_filename.replace('\\', '/')
        if '/' in normalized_filename or '..' in normalized_filename:
            results.append({
                'filename': raw_filename,
                'error': 'Invalid filename detected',
                'logs': ['Rejected due to unsafe filename path.'],
                'success': False
            })
            continue

        filename = secure_filename(raw_filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_filename = f"injected_{filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        console = Console()
        try:
             # Re-parse to get specific audio audio capabilities for this file if needed
            if options.get('spatial_audio'):
                parsed = metadata_utils.parse_metadata(input_path, lambda x: None)
                if parsed and parsed.num_audio_channels:
                     desc = metadata_utils.get_spatial_audio_description(parsed.num_audio_channels)
                     if desc.is_supported:
                         metadata.audio = metadata_utils.get_spatial_audio_metadata(
                            desc.order,
                            desc.has_head_locked_stereo
                        )
            
            metadata_utils.inject_metadata(input_path, output_path, metadata, console.append)
            results.append({
                'filename': filename,
                'output_url': f"/download/{output_filename}",
                'logs': console.log,
                'success': True
            })
        except Exception as e:
            results.append({
                'filename': filename,
                'error': str(e),
                'logs': console.log,
                'success': False
            })

    return jsonify({'results': results})

@app.route('/download/<path:filename>')
def download_file(filename):
    normalized_filename = filename.replace('\\', '/')
    if '/' in normalized_filename or '..' in normalized_filename:
        return "Invalid file path", 400
        
    secure_name = secure_filename(filename)
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], secure_name), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
