from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import subprocess
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Fixed paths
INPUT_VIDEO_PATH = "/Users/adityakhanna/Desktop/Project/football_analysis/input_videos/08fd33_4.mp4"
OUTPUT_VIDEO_PATH = "/Users/adityakhanna/Desktop/Project/football_analysis/output_videos/output_video.avl"
PYTHON_PATH = "/Users/adityakhanna/miniconda3/envs/football/bin/python"
SCRIPT_WORKING_DIR = "/Users/adityakhanna/Desktop/Project/football_analysis"

# Global variable to track processing status
processing_status = {"status": "idle", "message": ""}

def run_processing_script():
    """Run the Python processing script in a separate thread"""
    global processing_status
    
    try:
        processing_status = {"status": "processing", "message": "Running Python script..."}
        
        # Change to the project directory and run the script
        result = subprocess.run(
            [PYTHON_PATH, "main.py"],
            cwd=SCRIPT_WORKING_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            # Check if output file was created
            if os.path.exists(OUTPUT_VIDEO_PATH):
                processing_status = {"status": "completed", "message": "Processing completed successfully!"}
            else:
                processing_status = {"status": "error", "message": "Script ran but output file not found"}
        else:
            processing_status = {"status": "error", "message": f"Script failed: {result.stderr}"}
            
    except subprocess.TimeoutExpired:
        processing_status = {"status": "error", "message": "Processing timed out"}
    except Exception as e:
        processing_status = {"status": "error", "message": f"Error running script: {str(e)}"}

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing"""
    global processing_status
    
    try:
        # Check if file is in request
        if 'video' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Create input directory if it doesn't exist
        input_dir = os.path.dirname(INPUT_VIDEO_PATH)
        os.makedirs(input_dir, exist_ok=True)
        
        # Save the uploaded file to the fixed location
        file.save(INPUT_VIDEO_PATH)
        processing_status = {"status": "uploaded", "message": "File uploaded successfully!"}
        
        # Start processing in a separate thread
        threading.Thread(target=run_processing_script, daemon=True).start()
        
        return jsonify({"message": "File uploaded and processing started", "status": "uploaded"})
    
    except Exception as e:
        processing_status = {"status": "error", "message": f"Upload failed: {str(e)}"}
        return jsonify({"error": str(e)}), 500

@app.route('/status')
def get_status():
    """Get current processing status"""
    return jsonify(processing_status)

@app.route('/output')
def serve_output():
    """Serve the processed output video"""
    try:
        if os.path.exists(OUTPUT_VIDEO_PATH):
            return send_file(OUTPUT_VIDEO_PATH, as_attachment=False)
        else:
            return jsonify({"error": "Output video not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset')
def reset_status():
    """Reset processing status"""
    global processing_status
    processing_status = {"status": "idle", "message": ""}
    
    # Optionally clean up files
    try:
        if os.path.exists(INPUT_VIDEO_PATH):
            os.remove(INPUT_VIDEO_PATH)
        if os.path.exists(OUTPUT_VIDEO_PATH):
            os.remove(OUTPUT_VIDEO_PATH)
    except:
        pass
    
    return jsonify({"message": "Status reset"})

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(os.path.dirname(INPUT_VIDEO_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_VIDEO_PATH), exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)