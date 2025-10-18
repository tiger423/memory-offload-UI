# Testing Guide

Complete testing guide for the LLM Inference Web UI - covers unit tests, integration tests, and end-to-end testing.

## 📋 Table of Contents

1. [Testing Setup](#testing-setup)
2. [Backend Tests](#backend-tests)
3. [Frontend Tests](#frontend-tests)
4. [Integration Tests](#integration-tests)
5. [Manual Testing Checklist](#manual-testing-checklist)
6. [Performance Testing](#performance-testing)
7. [Troubleshooting Tests](#troubleshooting-tests)

---

## Testing Setup

### Prerequisites

```bash
# Python testing tools
pip install pytest pytest-asyncio pytest-mock

# Node.js testing tools (optional)
npm install --save-dev jest supertest
```

### Test Environment

```bash
# Set test environment
export NODE_ENV=test
export HF_TOKEN=test_token_here

# Use smaller model for testing
export TEST_MODEL=llama2-7b
```

---

## Backend Tests

### 1. Test Backend Configuration

**File: `test_backend_config.py`**

```python
#!/usr/bin/env python3
"""Test backend configuration module"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.config import config, MODEL_REGISTRY, get_quantization_config

def test_model_registry():
    """Test model registry is properly configured"""
    print("Testing Model Registry...")

    # Check required models exist
    required_models = ['opt-30b', 'llama2-7b', 'llama2-13b', 'falcon-7b']
    for model_id in required_models:
        assert model_id in MODEL_REGISTRY, f"Model {model_id} not found"
        model = MODEL_REGISTRY[model_id]

        # Verify required fields
        assert 'id' in model
        assert 'name' in model
        assert 'hf_name' in model
        assert 'size_gb' in model
        assert 'min_gpu_memory' in model
        assert 'min_cpu_memory' in model

    print(f"✅ {len(MODEL_REGISTRY)} models configured")

def test_backend_config():
    """Test backend configuration class"""
    print("\nTesting Backend Config...")

    # Test getting all models
    models = config.get_all_models()
    assert len(models) > 0, "No models found"
    print(f"✅ Found {len(models)} models")

    # Test getting specific model
    model = config.get_model_config('llama2-7b')
    assert model['id'] == 'llama2-7b'
    print("✅ Model retrieval works")

    # Test invalid model
    try:
        config.get_model_config('invalid-model')
        assert False, "Should raise ValueError"
    except ValueError:
        print("✅ Invalid model raises error")

def test_quantization_config():
    """Test quantization configuration"""
    print("\nTesting Quantization Config...")

    # Test 8-bit config
    config_8bit = get_quantization_config('8-bit', True)
    assert config_8bit is not None
    print("✅ 8-bit config created")

    # Test 4-bit config
    config_4bit = get_quantization_config('4-bit', False)
    assert config_4bit is not None
    print("✅ 4-bit config created")

    # Test none config
    config_none = get_quantization_config('none', False)
    assert config_none is None
    print("✅ None config returns None")

if __name__ == '__main__':
    print("="*60)
    print("Backend Configuration Tests")
    print("="*60)

    try:
        test_model_registry()
        test_backend_config()
        test_quantization_config()

        print("\n" + "="*60)
        print("✅ ALL BACKEND CONFIG TESTS PASSED")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

### 2. Test Memory Utils

**File: `test_memory_utils.py`**

```python
#!/usr/bin/env python3
"""Test memory utilities"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from memory_utils import (
    get_gpu_memory_info,
    get_cpu_memory_info,
    get_disk_usage,
    analyze_device_map,
    estimate_model_memory
)

def test_gpu_memory():
    """Test GPU memory info"""
    print("Testing GPU Memory Info...")

    info = get_gpu_memory_info()

    if 'error' in info:
        print("⚠️  CUDA not available, skipping GPU test")
        return

    assert 'allocated' in info
    assert 'reserved' in info
    assert 'free' in info
    assert 'total' in info

    assert info['total'] > 0
    print(f"✅ GPU: {info['total']} GB total")

def test_cpu_memory():
    """Test CPU memory info"""
    print("\nTesting CPU Memory Info...")

    info = get_cpu_memory_info()

    assert 'used' in info
    assert 'available' in info
    assert 'total' in info
    assert 'percent' in info

    assert info['total'] > 0
    print(f"✅ CPU: {info['total']} GB total")

def test_disk_usage():
    """Test disk usage"""
    print("\nTesting Disk Usage...")

    info = get_disk_usage('.')

    assert 'used' in info
    assert 'free' in info
    assert 'total' in info

    assert info['total'] > 0
    print(f"✅ Disk: {info['total']} GB total")

def test_device_map_analysis():
    """Test device map analysis"""
    print("\nTesting Device Map Analysis...")

    # Mock device map
    device_map = {
        'model.layer.0': 0,
        'model.layer.1': 0,
        'model.layer.2': 'cpu',
        'model.layer.3': 'cpu',
        'model.norm': 0
    }

    analysis = analyze_device_map(device_map)

    assert 'device_counts' in analysis
    assert 'module_types' in analysis

    assert analysis['device_counts']['0'] == 3
    assert analysis['device_counts']['cpu'] == 2

    print("✅ Device map analysis works")

def test_model_memory_estimation():
    """Test model memory estimation"""
    print("\nTesting Model Memory Estimation...")

    # Test 7B model
    fp32_size = estimate_model_memory(7, 'float32')
    fp16_size = estimate_model_memory(7, 'float16')
    int8_size = estimate_model_memory(7, 'int8')

    assert fp32_size == 28.0  # 7B * 4 bytes
    assert fp16_size == 14.0  # 7B * 2 bytes
    assert int8_size == 7.0   # 7B * 1 byte

    print(f"✅ 7B model: FP32={fp32_size}GB, FP16={fp16_size}GB, INT8={int8_size}GB")

if __name__ == '__main__':
    print("="*60)
    print("Memory Utilities Tests")
    print("="*60)

    try:
        test_gpu_memory()
        test_cpu_memory()
        test_disk_usage()
        test_device_map_analysis()
        test_model_memory_estimation()

        print("\n" + "="*60)
        print("✅ ALL MEMORY UTILS TESTS PASSED")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

### 3. Test Inference Engine (Mock)

**File: `test_inference_engine.py`**

```python
#!/usr/bin/env python3
"""Test inference engine (without loading actual models)"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.inference_engine import InferenceEngine

def test_inference_engine_init():
    """Test inference engine initialization"""
    print("Testing InferenceEngine Initialization...")

    # Test with valid model
    engine = InferenceEngine('llama2-7b')

    assert engine.model_id == 'llama2-7b'
    assert engine.model_config is not None
    assert engine.hf_model_name == 'meta-llama/Llama-2-7b-hf'

    print("✅ InferenceEngine initialized")

def test_inference_engine_invalid_model():
    """Test inference engine with invalid model"""
    print("\nTesting Invalid Model...")

    try:
        engine = InferenceEngine('invalid-model')
        assert False, "Should raise ValueError"
    except ValueError as e:
        print(f"✅ Invalid model raises error: {e}")

def test_callback_mechanism():
    """Test callback mechanism"""
    print("\nTesting Callback Mechanism...")

    events = []

    def test_callback(event, data):
        events.append({'event': event, 'data': data})

    engine = InferenceEngine('llama2-7b', progress_callback=test_callback)

    # Trigger an emit
    engine._emit('test_event', {'message': 'test'})

    assert len(events) == 1
    assert events[0]['event'] == 'test_event'
    assert events[0]['data']['message'] == 'test'

    print("✅ Callback mechanism works")

def test_device_map_serialization():
    """Test device map serialization"""
    print("\nTesting Device Map Serialization...")

    engine = InferenceEngine('llama2-7b')

    device_map = {
        'layer.0': 0,
        'layer.1': 'cpu',
        'layer.2': 'disk'
    }

    serialized = engine._serialize_device_map(device_map)

    assert serialized['layer.0'] == 0
    assert serialized['layer.1'] == 'cpu'
    assert serialized['layer.2'] == 'disk'

    print("✅ Device map serialization works")

if __name__ == '__main__':
    print("="*60)
    print("Inference Engine Tests (Mock)")
    print("="*60)

    try:
        test_inference_engine_init()
        test_inference_engine_invalid_model()
        test_callback_mechanism()
        test_device_map_serialization()

        print("\n" + "="*60)
        print("✅ ALL INFERENCE ENGINE TESTS PASSED")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

---

## Frontend Tests

### 1. Test Express Server

**File: `webapp/test_server.js`**

```javascript
const request = require('supertest');
const app = require('./server'); // Export app in server.js

describe('Express Server API Tests', () => {

    test('GET /api/models should return model list', async () => {
        const response = await request(app)
            .get('/api/models')
            .expect('Content-Type', /json/)
            .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.models).toBeInstanceOf(Array);
        expect(response.body.models.length).toBeGreaterThan(0);
    });

    test('GET /api/status should return server status', async () => {
        const response = await request(app)
            .get('/api/status')
            .expect('Content-Type', /json/)
            .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.status).toBeDefined();
    });

    test('POST /api/inference/start with valid data', async () => {
        const response = await request(app)
            .post('/api/inference/start')
            .send({
                modelId: 'llama2-7b',
                prompt: 'Test prompt',
                quantization: '8-bit'
            })
            .expect('Content-Type', /json/)
            .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.sessionId).toBeDefined();
    });

    test('POST /api/inference/start without modelId should fail', async () => {
        const response = await request(app)
            .post('/api/inference/start')
            .send({
                prompt: 'Test prompt'
            })
            .expect(400);

        expect(response.body.success).toBe(false);
    });

});
```

### 2. Manual Frontend Test Script

**File: `test_frontend.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Frontend Test Suite</title>
    <style>
        body { font-family: monospace; padding: 20px; }
        .test { margin: 10px 0; }
        .pass { color: green; }
        .fail { color: red; }
    </style>
</head>
<body>
    <h1>Frontend Test Suite</h1>
    <div id="results"></div>

    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script>
        const results = document.getElementById('results');

        function logTest(name, passed, details) {
            const div = document.createElement('div');
            div.className = 'test ' + (passed ? 'pass' : 'fail');
            div.textContent = `${passed ? '✅' : '❌'} ${name}${details ? ': ' + details : ''}`;
            results.appendChild(div);
        }

        async function runTests() {
            // Test 1: Fetch models
            try {
                const response = await fetch('/api/models');
                const data = await response.json();
                logTest('Fetch models', data.success && data.models.length > 0,
                    `Found ${data.models.length} models`);
            } catch (e) {
                logTest('Fetch models', false, e.message);
            }

            // Test 2: WebSocket connection
            try {
                const socket = io();
                socket.on('connect', () => {
                    logTest('WebSocket connection', true, 'Connected');
                    socket.disconnect();
                });
                socket.on('connect_error', (error) => {
                    logTest('WebSocket connection', false, error.message);
                });
            } catch (e) {
                logTest('WebSocket connection', false, e.message);
            }

            // Test 3: Server status
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                logTest('Server status', data.success,
                    `Status: ${data.status.server}`);
            } catch (e) {
                logTest('Server status', false, e.message);
            }

            // Test 4: Invalid model ID
            try {
                const response = await fetch('/api/models/invalid-id');
                logTest('Invalid model handling', response.status === 404,
                    `Status: ${response.status}`);
            } catch (e) {
                logTest('Invalid model handling', false, e.message);
            }
        }

        runTests();
    </script>
</body>
</html>
```

---

## Integration Tests

### Full End-to-End Test

**File: `test_e2e.py`**

```python
#!/usr/bin/env python3
"""
End-to-End Integration Test
Tests complete flow from frontend → backend → inference
"""

import sys
import os
import json
import subprocess
import time
import requests

def test_full_inference_flow():
    """Test complete inference flow"""

    print("="*60)
    print("End-to-End Integration Test")
    print("="*60)

    # Step 1: Check server is running
    print("\n1. Checking server...")
    try:
        response = requests.get('http://localhost:3000/api/status', timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding. Start server first:")
            print("   cd webapp && npm start")
            sys.exit(1)
        print("✅ Server is running")
    except requests.exceptions.RequestException:
        print("❌ Server not reachable. Start server first:")
        print("   cd webapp && npm start")
        sys.exit(1)

    # Step 2: Get available models
    print("\n2. Fetching models...")
    response = requests.get('http://localhost:3000/api/models')
    data = response.json()
    assert data['success'], "Failed to fetch models"
    models = data['models']
    print(f"✅ Found {len(models)} models")

    # Step 3: Start inference with smallest model
    print("\n3. Starting inference (this will take time)...")
    test_model = 'llama2-7b'  # Use smallest model

    payload = {
        'modelId': test_model,
        'prompt': 'Hello',
        'quantization': '8-bit',
        'enableFp32CpuOffload': True,
        'maxLength': 20,  # Short generation for testing
        'temperature': 0.7,
        'topP': 0.9,
        'gpuMemory': '6GiB',
        'cpuMemory': '12GiB'
    }

    response = requests.post('http://localhost:3000/api/inference/start', json=payload)
    data = response.json()

    if not data['success']:
        print(f"❌ Failed to start inference: {data.get('error')}")
        sys.exit(1)

    session_id = data['sessionId']
    print(f"✅ Inference started (Session: {session_id})")

    # Step 4: Poll session status
    print("\n4. Monitoring inference progress...")
    max_wait = 300  # 5 minutes max
    start_time = time.time()

    while True:
        if time.time() - start_time > max_wait:
            print("❌ Timeout waiting for inference")
            sys.exit(1)

        response = requests.get(f'http://localhost:3000/api/session/{session_id}')
        session = response.json()['session']

        status = session['status']
        print(f"   Status: {status}")

        if status == 'completed':
            print("✅ Inference completed")
            break
        elif status == 'failed':
            print(f"❌ Inference failed: {session.get('error')}")
            sys.exit(1)

        time.sleep(2)

    # Step 5: Verify results
    print("\n5. Verifying results...")
    if 'output' in session and session['output']:
        print(f"✅ Generated output: {session['output'][:100]}...")
    if 'metrics' in session and session['metrics']:
        print(f"✅ Metrics collected: {session['metrics']}")

    print("\n" + "="*60)
    print("✅ END-TO-END TEST PASSED")
    print("="*60)

if __name__ == '__main__':
    try:
        test_full_inference_flow()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

---

## Manual Testing Checklist

### Pre-Flight Checks

```bash
□ Node.js v18+ installed
□ Python 3.9+ installed
□ CUDA available (nvidia-smi works)
□ Dependencies installed (npm + pip)
□ .env file configured with HF_TOKEN
□ Backend imports work
□ Server starts without errors
```

### UI Functionality Tests

#### 1. Page Load
```
□ Open http://localhost:3000
□ Page loads within 2 seconds
□ No console errors
□ WebSocket connects (green badge)
□ Model dropdown populated
```

#### 2. Model Selection
```
□ Select each model from dropdown
□ Model info appears with correct details
□ Size, GPU, RAM requirements shown
```

#### 3. Configuration
```
□ Toggle quantization options
□ Toggle FP32 CPU offload
□ Adjust temperature slider (value updates)
□ Adjust top-p slider (value updates)
□ Expand advanced settings
□ Modify GPU/CPU memory limits
□ Change max length
```

#### 4. Inference (LLaMA 2 7B)
```
□ Enter prompt: "Hello, world!"
□ Click "Start Inference"
□ Status card appears
□ Progress bar animates 0-100%
□ Status messages update
□ Memory bars update
□ Model loads within 2 minutes
□ Generation starts
□ Output appears
□ Metrics card appears
□ Device map card appears
□ "Complete" status shown
□ Total time < 5 minutes
```

#### 5. Memory Monitoring
```
□ GPU memory bar shows usage
□ CPU memory bar shows usage
□ Values update in real-time
□ No memory leaks after 3 inferences
```

#### 6. Stop Functionality
```
□ Start inference
□ Click "Stop" button
□ Process terminates
□ Status shows "Stopped"
□ UI resets properly
```

#### 7. Error Handling
```
□ Try inference without model selected → Error shown
□ Try inference without prompt → Error shown
□ Disconnect internet during load → Error shown
□ Kill Python process manually → Error shown
□ Try invalid GPU memory → Handles gracefully
```

#### 8. Multiple Sessions
```
□ Complete one inference
□ Start another inference
□ Previous results remain visible
□ New session gets unique ID
□ No interference between sessions
```

---

## Performance Testing

### Benchmark Script

**File: `benchmark.py`**

```python
#!/usr/bin/env python3
"""Performance benchmark script"""

import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.inference_engine import InferenceEngine

def benchmark_model(model_id, prompt, max_length=30):
    """Benchmark a specific model"""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {model_id}")
    print(f"{'='*60}")

    times = {}

    # Initialize
    init_start = time.time()
    engine = InferenceEngine(model_id)
    times['init'] = time.time() - init_start
    print(f"Initialization: {times['init']:.2f}s")

    # Load model
    load_start = time.time()
    success = engine.load_model(
        quantization='8-bit',
        enable_fp32_cpu_offload=True,
        gpu_memory='6GiB',
        cpu_memory='12GiB'
    )
    times['load'] = time.time() - load_start
    print(f"Model Load: {times['load']:.2f}s")

    if not success:
        print("❌ Failed to load model")
        return None

    # Generate
    gen_start = time.time()
    result = engine.generate(
        prompt=prompt,
        max_length=max_length,
        temperature=0.7
    )
    times['generate'] = time.time() - gen_start
    print(f"Generation: {times['generate']:.2f}s")

    # Cleanup
    cleanup_start = time.time()
    engine.unload_model()
    times['cleanup'] = time.time() - cleanup_start
    print(f"Cleanup: {times['cleanup']:.2f}s")

    # Calculate metrics
    tokens_generated = result['metrics']['tokensGenerated']
    tokens_per_sec = tokens_generated / times['generate']
    total_time = sum(times.values())

    print(f"\nResults:")
    print(f"  Tokens generated: {tokens_generated}")
    print(f"  Tokens/second: {tokens_per_sec:.2f}")
    print(f"  Total time: {total_time:.2f}s")

    return {
        'model_id': model_id,
        'times': times,
        'tokens_generated': tokens_generated,
        'tokens_per_sec': tokens_per_sec,
        'total_time': total_time
    }

if __name__ == '__main__':
    prompt = "Hello, world!"
    max_length = 30

    # Benchmark smallest model
    result = benchmark_model('llama2-7b', prompt, max_length)

    if result:
        print(f"\n{'='*60}")
        print("✅ BENCHMARK COMPLETE")
        print(f"{'='*60}")
```

---

## Troubleshooting Tests

### Diagnostic Script

**File: `diagnose.sh`**

```bash
#!/bin/bash
# Comprehensive diagnostic script

echo "========================================="
echo "LLM Inference UI Diagnostics"
echo "========================================="

# Check Node.js
echo -e "\n1. Node.js:"
if command -v node &> /dev/null; then
    node --version
    echo "✅ Node.js installed"
else
    echo "❌ Node.js not found"
fi

# Check Python
echo -e "\n2. Python:"
if command -v python &> /dev/null; then
    python --version
    echo "✅ Python installed"
elif command -v python3 &> /dev/null; then
    python3 --version
    echo "✅ Python3 installed"
else
    echo "❌ Python not found"
fi

# Check CUDA
echo -e "\n3. CUDA:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo "✅ CUDA available"
else
    echo "⚠️  CUDA not detected"
fi

# Check Python packages
echo -e "\n4. Python Packages:"
python -c "import torch; print(f'torch: {torch.__version__}')" 2>/dev/null && echo "✅ torch" || echo "❌ torch"
python -c "import transformers; print(f'transformers: {transformers.__version__}')" 2>/dev/null && echo "✅ transformers" || echo "❌ transformers"
python -c "import accelerate; print(f'accelerate: {accelerate.__version__}')" 2>/dev/null && echo "✅ accelerate" || echo "❌ accelerate"
python -c "import bitsandbytes; print(f'bitsandbytes: {bitsandbytes.__version__}')" 2>/dev/null && echo "✅ bitsandbytes" || echo "❌ bitsandbytes"

# Check Node packages
echo -e "\n5. Node.js Packages:"
cd webapp 2>/dev/null
if [ -d "node_modules" ]; then
    echo "✅ node_modules exists"
    [ -d "node_modules/express" ] && echo "✅ express" || echo "❌ express"
    [ -d "node_modules/socket.io" ] && echo "✅ socket.io" || echo "❌ socket.io"
else
    echo "❌ node_modules not found. Run: npm install"
fi
cd ..

# Check .env file
echo -e "\n6. Configuration:"
if [ -f "webapp/.env" ]; then
    echo "✅ .env file exists"
    if grep -q "HF_TOKEN=hf_" webapp/.env; then
        echo "✅ HF_TOKEN configured"
    else
        echo "⚠️  HF_TOKEN not set or invalid"
    fi
else
    echo "❌ .env file not found"
fi

# Check backend imports
echo -e "\n7. Backend Imports:"
python -c "from backend.inference_engine import InferenceEngine; print('✅ backend imports work')" 2>/dev/null || echo "❌ backend import failed"

# Check server
echo -e "\n8. Server Status:"
if curl -s http://localhost:3000/api/status > /dev/null 2>&1; then
    echo "✅ Server is running"
else
    echo "⚠️  Server not running. Start with: cd webapp && npm start"
fi

echo -e "\n========================================="
echo "Diagnostics Complete"
echo "========================================="
```

Make it executable:
```bash
chmod +x diagnose.sh
```

---

## Running All Tests

### Test Runner Script

**File: `run_tests.sh`**

```bash
#!/bin/bash
# Run all tests

echo "Running Test Suite..."

# Backend tests
echo -e "\n1. Backend Configuration Tests"
python test_backend_config.py || exit 1

echo -e "\n2. Memory Utils Tests"
python test_memory_utils.py || exit 1

echo -e "\n3. Inference Engine Tests"
python test_inference_engine.py || exit 1

# Diagnostics
echo -e "\n4. System Diagnostics"
./diagnose.sh

echo -e "\n========================================="
echo "✅ ALL TESTS PASSED"
echo "========================================="
```

Make it executable:
```bash
chmod +x run_tests.sh
```

---

## Test Summary

### Quick Test Commands

```bash
# Run all backend tests
python test_backend_config.py
python test_memory_utils.py
python test_inference_engine.py

# Run diagnostics
./diagnose.sh

# Run full test suite
./run_tests.sh

# Manual E2E test (requires running server)
python test_e2e.py

# Performance benchmark
python benchmark.py
```

### Expected Results

- **Backend tests**: < 1 second each
- **Diagnostics**: < 5 seconds
- **E2E test**: 3-5 minutes (includes inference)
- **Benchmark**: 2-4 minutes per model

---

This testing guide provides comprehensive coverage of all system components with both automated and manual testing procedures.
