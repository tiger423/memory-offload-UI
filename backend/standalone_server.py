#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone Backend Server (Optional)
Alternative Flask-based REST API server for the inference engine
Can be used instead of Node.js + Python subprocess architecture
"""

import os
import sys
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import uuid
from datetime import datetime
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.inference_engine import InferenceEngine
from backend.config import config

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Active sessions
active_sessions = {}
session_lock = threading.Lock()


# =============================================================================
# Helper Functions
# =============================================================================

def create_sse_message(event, data):
    """Create Server-Sent Event message"""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# =============================================================================
# API Endpoints
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'backend': 'python-flask'
    })


@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of available models"""
    models = config.get_all_models()
    return jsonify({
        'success': True,
        'models': models
    })


@app.route('/api/models/<model_id>', methods=['GET'])
def get_model(model_id):
    """Get specific model configuration"""
    try:
        model_config = config.get_model_config(model_id)
        return jsonify({
            'success': True,
            'model': model_config
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@app.route('/api/inference/start', methods=['POST'])
def start_inference():
    """Start inference session"""
    data = request.json

    # Validate input
    if not data.get('modelId') or not data.get('prompt'):
        return jsonify({
            'success': False,
            'error': 'modelId and prompt are required'
        }), 400

    # Create session
    session_id = str(uuid.uuid4())

    session = {
        'id': session_id,
        'modelId': data['modelId'],
        'prompt': data['prompt'],
        'config': {
            'quantization': data.get('quantization', '8-bit'),
            'enableFp32CpuOffload': data.get('enableFp32CpuOffload', True),
            'maxLength': data.get('maxLength', 50),
            'temperature': data.get('temperature', 0.7),
            'topP': data.get('topP', 0.9),
            'gpuMemory': data.get('gpuMemory', '14GiB'),
            'cpuMemory': data.get('cpuMemory', '56GiB')
        },
        'status': 'queued',
        'created': datetime.now().isoformat(),
        'result': None,
        'error': None
    }

    with session_lock:
        active_sessions[session_id] = session

    # Start inference in background thread
    thread = threading.Thread(
        target=run_inference,
        args=(session_id,)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'sessionId': session_id,
        'message': 'Inference session started'
    })


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session status"""
    session = active_sessions.get(session_id)

    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404

    return jsonify({
        'success': True,
        'session': session
    })


@app.route('/api/session/<session_id>/stream', methods=['GET'])
def stream_session(session_id):
    """Stream session updates via Server-Sent Events"""
    def generate():
        session = active_sessions.get(session_id)
        if not session:
            yield create_sse_message('error', {'error': 'Session not found'})
            return

        # Send initial status
        yield create_sse_message('status', {'status': session['status']})

        # Poll for updates (simplified - in production use proper event queue)
        while True:
            session = active_sessions.get(session_id)
            if not session:
                break

            if session['status'] in ['completed', 'failed']:
                if session['status'] == 'completed':
                    yield create_sse_message('result', session['result'])
                else:
                    yield create_sse_message('error', {'error': session.get('error')})
                break

            import time
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')


# =============================================================================
# Inference Worker
# =============================================================================

def run_inference(session_id):
    """
    Run inference in background thread

    Args:
        session_id: Session identifier
    """
    session = active_sessions.get(session_id)
    if not session:
        return

    try:
        session['status'] = 'loading'

        # Create callback to update session
        def update_callback(event, data):
            if session_id in active_sessions:
                active_sessions[session_id]['lastUpdate'] = {
                    'event': event,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }

                # Update status
                if event == 'status':
                    active_sessions[session_id]['status'] = data.get('status', 'unknown')

        # Initialize engine
        engine = InferenceEngine(
            model_id=session['modelId'],
            progress_callback=update_callback
        )

        # Load model
        success = engine.load_model(
            quantization=session['config']['quantization'],
            enable_fp32_cpu_offload=session['config']['enableFp32CpuOffload'],
            gpu_memory=session['config']['gpuMemory'],
            cpu_memory=session['config']['cpuMemory']
        )

        if not success:
            session['status'] = 'failed'
            session['error'] = 'Failed to load model'
            return

        # Generate
        result = engine.generate(
            prompt=session['prompt'],
            max_length=session['config']['maxLength'],
            temperature=session['config']['temperature'],
            top_p=session['config']['topP']
        )

        session['status'] = 'completed'
        session['result'] = result
        session['completed'] = datetime.now().isoformat()

        # Cleanup
        engine.unload_model()

    except Exception as e:
        session['status'] = 'failed'
        session['error'] = str(e)
        import traceback
        traceback.print_exc()


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('BACKEND_PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    print('='*60)
    print('🚀 LLM Inference Backend Server (Standalone)')
    print('='*60)
    print(f'📍 Server: http://localhost:{port}')
    print(f'🔑 HF Token: {"✅ Configured" if config.hf_token else "❌ Not configured"}')
    print('='*60)
    print('Available endpoints:')
    print('  GET  /api/health          - Health check')
    print('  GET  /api/models          - List models')
    print('  POST /api/inference/start - Start inference')
    print('  GET  /api/session/:id     - Get session status')
    print('  GET  /api/session/:id/stream - Stream updates (SSE)')
    print('='*60)
    print('\n⚠️  Note: This is an alternative to the Node.js server.')
    print('    For production, use the Node.js + Python architecture.\n')

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
