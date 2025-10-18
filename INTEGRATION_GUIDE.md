# Frontend-Backend Integration Guide

Complete guide for the Node.js Express frontend + Python backend architecture.

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (User Interface)                 │
│  • HTML/CSS/JavaScript (Bootstrap 5)                        │
│  • Socket.IO client for real-time updates                   │
│  • REST API calls for operations                            │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP POST/GET + WebSocket
┌────────────────▼────────────────────────────────────────────┐
│              Node.js Express Server (webapp/)               │
│  • REST API endpoints (/api/*)                              │
│  • WebSocket server (Socket.IO)                             │
│  • Session management                                        │
│  • Python process spawning & management                      │
└────────────────┬────────────────────────────────────────────┘
                 │ Child Process (spawn)
┌────────────────▼────────────────────────────────────────────┐
│           Python Backend (backend/)                         │
│  • inference_api.py (CLI wrapper)                           │
│  • inference_engine.py (Core engine)                        │
│  • config.py (Model registry)                               │
│  • JSON stdout → Node.js stdin                              │
└────────────────┬────────────────────────────────────────────┘
                 │ HuggingFace Transformers
┌────────────────▼────────────────────────────────────────────┐
│                   GPU/CPU/Disk Resources                    │
│  • Model loading & inference                                │
│  • Memory management                                         │
│  • Quantization (8-bit/4-bit)                               │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Complete File Structure

```
vLLM/
├── backend/                      # Python backend (NEW)
│   ├── __init__.py              # Module initialization
│   ├── config.py                # Model registry & configuration
│   ├── inference_engine.py      # Core inference engine
│   ├── inference_api.py         # CLI wrapper for Node.js
│   ├── standalone_server.py     # Optional Flask server
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Backend documentation
│
├── webapp/                       # Node.js frontend
│   ├── server.js                # Express server + WebSocket
│   ├── package.json             # Node.js dependencies
│   ├── .env                     # Environment config
│   ├── .env.example            # Environment template
│   ├── .gitignore              # Git ignore rules
│   ├── README.md               # Frontend documentation
│   ├── QUICKSTART.md           # Quick setup guide
│   └── public/                 # Static frontend files
│       ├── index.html          # Main UI
│       ├── css/
│       │   └── style.css       # Custom styles
│       └── js/
│           └── app.js          # Frontend JavaScript
│
├── memory_utils.py              # Shared memory utilities
├── opt_30b_optimized.py         # Standalone inference script
├── opt_30b_comparison.py        # Comparison script
├── opt-d-1-4.py                 # Original baseline
├── CLAUDE.md                    # Project instructions
├── README_OPTIMIZED.md          # Optimized scripts docs
├── WEBAPP_SUMMARY.md            # Web UI summary
└── INTEGRATION_GUIDE.md         # This file
```

## 🔄 Data Flow

### 1. Starting an Inference Session

```
User Action (Browser)
    ↓
    1. User clicks "Start Inference"
    ↓
Frontend (app.js)
    ↓
    2. POST /api/inference/start
    ↓
Express Server (server.js)
    ↓
    3. Create session with UUID
    4. Spawn Python child process
    ↓
Python Backend (inference_api.py)
    ↓
    5. Parse command-line arguments
    6. Initialize InferenceEngine
    7. Load model with quantization
    8. Emit JSON progress to stdout
    ↓
Node.js (server.js)
    ↓
    9. Parse JSON from Python stdout
    10. Emit via WebSocket to browser
    ↓
Frontend (app.js)
    ↓
    11. Update UI in real-time
    12. Display progress, memory, output
```

### 2. Communication Protocol

#### Python → Node.js (stdout)

```json
{"type": "status", "data": {"status": "loading", "message": "Loading model..."}}
{"type": "progress", "data": {"percent": 50, "message": "Loading weights..."}}
{"type": "memory", "data": {"gpu": {"allocated": 7.2, "total": 16.0}, "cpu": {...}}}
{"type": "device_map", "data": {"model.layer.0": 0, "model.layer.1": "cpu", ...}}
{"type": "result", "data": {"text": "...", "prompt": "...", "metrics": {...}}}
{"type": "error", "data": {"error": "Error message"}}
{"type": "complete", "data": {"status": "completed", "duration": 123000}}
```

#### Node.js → Browser (WebSocket)

```javascript
socket.emit('status', {status: 'loading', message: 'Loading model...'});
socket.emit('progress', {percent: 50, message: 'Loading weights...'});
socket.emit('memory', {gpu: {...}, cpu: {...}});
socket.emit('device_map', {...});
socket.emit('result', {text: '...', metrics: {...}});
socket.emit('error', {error: '...'});
socket.emit('complete', {status: 'completed', duration: 123000});
```

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
# Node.js dependencies
cd webapp
npm install

# Python dependencies
cd ..
pip install -r backend/requirements.txt
```

### Step 2: Configure Environment

```bash
cd webapp
cp .env.example .env
```

Edit `.env`:
```env
PORT=3000
PYTHON_PATH=python
HF_TOKEN=your_huggingface_token_here
```

### Step 3: Verify Setup

```bash
# Test Node.js
node --version  # Should be v18+

# Test Python
python --version  # Should be 3.9+

# Test Python imports
python -c "from backend.inference_engine import InferenceEngine; print('✅ Backend OK')"

# Test CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### Step 4: Start Server

```bash
cd webapp
npm start
```

Open browser: http://localhost:3000

## 🔧 Configuration

### Backend Configuration (backend/config.py)

**Model Registry:**
```python
MODEL_REGISTRY = {
    'opt-30b': {
        'id': 'opt-30b',
        'name': 'OPT-30B (Meta)',
        'hf_name': 'facebook/opt-30b',
        'size_gb': 60,
        'min_gpu_memory': 16,
        'min_cpu_memory': 32,
        ...
    }
}
```

**Default Settings:**
```python
DEFAULT_INFERENCE_CONFIG = {
    'quantization': '8-bit',
    'enable_fp32_cpu_offload': True,
    'max_length': 50,
    'temperature': 0.7,
    ...
}
```

### Frontend Configuration (webapp/server.js)

**Available Models:**
```javascript
const AVAILABLE_MODELS = [
    {
        id: 'opt-30b',
        name: 'OPT-30B (Meta)',
        fullName: 'facebook/opt-30b',
        ...
    }
];
```

**Python Process Configuration:**
```javascript
const pythonProcess = spawn(PYTHON_PATH, args, {
    env: { ...process.env, HF_TOKEN: process.env.HF_TOKEN },
    cwd: path.join(__dirname, '..')
});
```

## 📊 API Reference

### REST Endpoints

#### GET /api/models
Get list of available models.

**Response:**
```json
{
  "success": true,
  "models": [
    {
      "id": "opt-30b",
      "name": "OPT-30B (Meta)",
      "fullName": "facebook/opt-30b",
      "size": "30B parameters",
      ...
    }
  ]
}
```

#### POST /api/inference/start
Start inference session.

**Request:**
```json
{
  "modelId": "opt-30b",
  "prompt": "Hello, world!",
  "quantization": "8-bit",
  "enableFp32CpuOffload": true,
  "maxLength": 50,
  "temperature": 0.7,
  "topP": 0.9,
  "gpuMemory": "14GiB",
  "cpuMemory": "56GiB"
}
```

**Response:**
```json
{
  "success": true,
  "sessionId": "uuid-here",
  "message": "Inference session started"
}
```

#### GET /api/session/:sessionId
Get session status.

**Response:**
```json
{
  "success": true,
  "session": {
    "id": "uuid-here",
    "status": "generating",
    "output": "...",
    "metrics": {...}
  }
}
```

### WebSocket Events

#### Client → Server

```javascript
// Subscribe to session updates
socket.emit('subscribe', sessionId);
```

#### Server → Client

```javascript
// Status update
socket.on('status', (data) => {
  // data: {status: 'loading', message: '...'}
});

// Progress update
socket.on('progress', (data) => {
  // data: {percent: 50, message: '...'}
});

// Memory update
socket.on('memory', (data) => {
  // data: {gpu: {...}, cpu: {...}}
});

// Device map
socket.on('device_map', (data) => {
  // data: {layerName: device, ...}
});

// Result
socket.on('result', (data) => {
  // data: {text: '...', metrics: {...}}
});

// Error
socket.on('error', (data) => {
  // data: {error: '...'}
});

// Complete
socket.on('complete', (data) => {
  // data: {status: 'completed', duration: 123000}
});
```

## 🧪 Testing

### Test Individual Components

**1. Test Backend Directly:**
```bash
python backend/inference_api.py \
  --model llama2-7b \
  --prompt "Test prompt" \
  --quantization 8-bit \
  --enable-fp32-cpu-offload \
  --session-id test-123
```

**2. Test Frontend API:**
```bash
# Start server
cd webapp
npm start

# In another terminal
curl http://localhost:3000/api/models
```

**3. Test WebSocket:**
```javascript
// In browser console
const socket = io();
socket.on('connect', () => console.log('Connected'));
```

### Integration Testing

**End-to-End Test:**
1. Start server: `npm start`
2. Open browser: http://localhost:3000
3. Select model: LLaMA 2 7B
4. Enter prompt: "Hello, world!"
5. Click "Start Inference"
6. Verify:
   - Status updates appear
   - Progress bar moves
   - Memory usage updates
   - Output displays
   - Metrics show

## 🐛 Debugging

### Enable Debug Logging

**Frontend:**
```javascript
// In webapp/public/js/app.js
console.log('Debug:', data);  // Add logging
```

**Backend:**
```python
# In backend/inference_engine.py
import sys
print(f"DEBUG: {message}", file=sys.stderr, flush=True)
```

**Node.js:**
```javascript
// In webapp/server.js
console.log(`[DEBUG] ${message}`);
```

### Common Issues

**1. Python process not found**
```bash
# Check PYTHON_PATH in .env
which python  # Linux/Mac
where python  # Windows

# Update .env
PYTHON_PATH=/full/path/to/python
```

**2. Module import errors**
```bash
# Verify backend can be imported
python -c "from backend import InferenceEngine; print('OK')"

# If fails, check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**3. WebSocket not connecting**
```javascript
// Check browser console
// Should see: "Connected to server"

// If not, verify:
// - Server is running
// - Port 3000 is open
// - No CORS issues
```

**4. JSON parse errors**
```bash
# Check Python stdout for non-JSON output
# All prints should be JSON format:
print(json.dumps({"type": "...", "data": {...}}), flush=True)
```

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit `.env` file
   - Use `.env.example` as template
   - Store tokens securely

2. **Input Validation**
   - Validate all user inputs
   - Sanitize prompts
   - Check memory limits

3. **Process Management**
   - Limit concurrent sessions
   - Timeout long-running processes
   - Clean up on exit

4. **Error Handling**
   - Catch all exceptions
   - Don't expose stack traces to frontend
   - Log errors securely

## 📈 Performance Optimization

### Backend Optimizations

1. **Model Loading**
   - Cache models in HF_CACHE_DIR
   - Reuse loaded models (if implementing model pool)
   - Pre-download models

2. **Memory Management**
   - Adjust GPU/CPU limits based on hardware
   - Use appropriate quantization
   - Enable FP32 CPU offload

3. **Generation Speed**
   - Increase batch size (if supported)
   - Optimize memory limits for more GPU layers
   - Use smaller models for testing

### Frontend Optimizations

1. **WebSocket**
   - Batch updates
   - Debounce rapid updates
   - Compress large messages

2. **UI Rendering**
   - Virtual scrolling for long outputs
   - Lazy load components
   - Optimize re-renders

## 🚀 Deployment

### Development
```bash
cd webapp
npm run dev  # With auto-reload
```

### Production

**1. Build Assets (if needed)**
```bash
# Currently using CDN assets, no build needed
```

**2. Start Production Server**
```bash
cd webapp
NODE_ENV=production npm start
```

**3. Use Process Manager**
```bash
# Install PM2
npm install -g pm2

# Start with PM2
pm2 start server.js --name llm-ui

# View logs
pm2 logs llm-ui

# Monitor
pm2 monit
```

**4. Nginx Reverse Proxy (Optional)**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /socket.io/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}
```

## 📚 Additional Resources

- [Backend README](backend/README.md) - Python backend details
- [Frontend README](webapp/README.md) - Node.js frontend details
- [Quick Start](webapp/QUICKSTART.md) - 5-minute setup
- [Web App Summary](WEBAPP_SUMMARY.md) - Implementation overview
- [Optimized Scripts](README_OPTIMIZED.md) - Standalone Python scripts

## 🤝 Contributing

To extend the system:

1. **Add new model**: Update `backend/config.py` and `webapp/server.js`
2. **Add new feature**: Implement in `backend/inference_engine.py`
3. **Add new endpoint**: Add to `webapp/server.js`
4. **Add new UI component**: Update `webapp/public/index.html` and `app.js`

## ✅ Verification Checklist

- [ ] Node.js v18+ installed
- [ ] Python 3.9+ installed
- [ ] CUDA available (check: `nvidia-smi`)
- [ ] Dependencies installed (npm + pip)
- [ ] .env file configured with HF_TOKEN
- [ ] Backend imports work (`python -c "from backend import InferenceEngine"`)
- [ ] Server starts without errors
- [ ] Browser can access http://localhost:3000
- [ ] WebSocket connects (check browser console)
- [ ] Models load successfully
- [ ] Inference generates text
- [ ] Memory monitoring updates
- [ ] Device map displays

## 🎉 Success!

If all checks pass, you have a fully functional LLM inference web UI with:
- ✅ Real-time frontend-backend communication
- ✅ Python backend with model management
- ✅ WebSocket streaming updates
- ✅ Memory monitoring
- ✅ Multiple model support
- ✅ Quantization options
- ✅ Performance metrics

**Enjoy inferencing! 🚀**

---

For questions or issues, refer to the individual component READMEs or create an issue on GitHub.
