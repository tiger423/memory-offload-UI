# Program Control Flow: Frontend → Backend

Complete control flow documentation for every UI function, traced from user action through frontend, Node.js server, Python backend, and back to the UI.

## 📋 Table of Contents

1. [Page Load & Initialization](#1-page-load--initialization)
2. [Loading Available Models](#2-loading-available-models)
3. [Model Selection Change](#3-model-selection-change)
4. [Adjusting Configuration](#4-adjusting-configuration)
5. [Starting Inference](#5-starting-inference)
6. [Real-time Progress Updates](#6-real-time-progress-updates)
7. [Memory Monitoring](#7-memory-monitoring)
8. [Device Map Display](#8-device-map-display)
9. [Generation Completion](#9-generation-completion)
10. [Stopping Inference](#10-stopping-inference)
11. [Error Handling](#11-error-handling)

---

## 1. Page Load & Initialization

### User Action
```
User opens browser → http://localhost:3000
```

### Control Flow

#### Step 1: Browser Requests HTML
```
Browser
  → GET http://localhost:3000/
  → Express Static Middleware
```

**File: webapp/server.js (line 23)**
```javascript
app.use(express.static(path.join(__dirname, 'public')));
```

#### Step 2: Server Responds with HTML
```
Express Server
  → Serves: webapp/public/index.html
  → Response: 200 OK
```

#### Step 3: Browser Loads Assets
```
Browser
  → GET /css/style.css
  → GET /js/app.js
  → GET Bootstrap CSS (CDN)
  → GET Socket.IO client (CDN)
```

#### Step 4: JavaScript Initialization
```
Browser executes: webapp/public/js/app.js
```

**File: webapp/public/js/app.js (line 57-61)**
```javascript
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    loadModels();
    setupEventListeners();
});
```

#### Step 5: WebSocket Connection
```javascript
// File: webapp/public/js/app.js (line 64-68)
function initializeWebSocket() {
    socket = io();  // Connect to server

    socket.on('connect', () => {
        console.log('Connected to server');
        updateServerStatus(true);
    });
}
```

**Flow:**
```
Browser (Socket.IO client)
  → WebSocket handshake
  → Express Server (Socket.IO server)
  → Connection established
```

**File: webapp/server.js (line 208-210)**
```javascript
io.on('connection', (socket) => {
    console.log(`Client connected: ${socket.id}`);
});
```

#### Step 6: UI Initialization Complete
```
Browser
  ✓ HTML loaded
  ✓ CSS applied
  ✓ JavaScript running
  ✓ WebSocket connected
  → Ready for user interaction
```

**Visual Result:**
- Green "Connected" badge appears
- Model dropdown shows "Loading models..."
- UI is interactive

---

## 2. Loading Available Models

### Trigger
```
Automatic after page load (DOMContentLoaded)
```

### Control Flow

#### Step 1: Frontend Requests Models
```javascript
// File: webapp/public/js/app.js (line 143-152)
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();

        if (data.success) {
            models = data.models;
            populateModelSelect(models);
        }
    } catch (error) {
        console.error('Error loading models:', error);
    }
}
```

**HTTP Request:**
```http
GET /api/models HTTP/1.1
Host: localhost:3000
```

#### Step 2: Server Handles Request
```javascript
// File: webapp/server.js (line 62-67)
app.get('/api/models', (req, res) => {
    res.json({
        success: true,
        models: AVAILABLE_MODELS
    });
});
```

**Response Data:**
```json
{
  "success": true,
  "models": [
    {
      "id": "opt-30b",
      "name": "OPT-30B (Meta)",
      "fullName": "facebook/opt-30b",
      "size": "30B parameters (~60GB FP16, ~30GB INT8)",
      "minGpuMemory": "16GB",
      "minRamMemory": "32GB",
      "supportedTasks": ["inference"],
      "quantizationSupport": ["8-bit", "4-bit"]
    },
    {
      "id": "llama2-7b",
      "name": "LLaMA 2 7B",
      ...
    }
  ]
}
```

#### Step 3: Frontend Populates Dropdown
```javascript
// File: webapp/public/js/app.js (line 227-236)
function populateModelSelect(models) {
    elements.modelSelect.innerHTML = '<option value="">-- Select a model --</option>';

    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.name;
        option.dataset.model = JSON.stringify(model);
        elements.modelSelect.appendChild(option);
    });
}
```

**Visual Result:**
```
Dropdown now shows:
  -- Select a model --
  OPT-30B (Meta)
  LLaMA 2 7B
  LLaMA 2 13B
  Falcon 7B
```

---

## 3. Model Selection Change

### User Action
```
User clicks dropdown → Selects "LLaMA 2 7B"
```

### Control Flow

#### Step 1: Change Event Fired
```javascript
// File: webapp/public/js/app.js (line 415)
elements.modelSelect.addEventListener('change', updateModelInfo);
```

#### Step 2: Update Model Info Display
```javascript
// File: webapp/public/js/app.js (line 238-252)
function updateModelInfo() {
    const selectedOption = elements.modelSelect.selectedOptions[0];

    if (!selectedOption || !selectedOption.value) {
        elements.modelInfo.style.display = 'none';
        return;
    }

    const model = JSON.parse(selectedOption.dataset.model);
    elements.modelSize.textContent = model.size;
    elements.modelGpu.textContent = model.minGpuMemory;
    elements.modelRam.textContent = model.minRamMemory;
    elements.modelInfo.style.display = 'block';
}
```

**Visual Result:**
```
Model Info Card appears:
┌─────────────────────────────┐
│ Size: 7B parameters         │
│ Min GPU: 8GB                │
│ Min RAM: 16GB               │
└─────────────────────────────┘
```

**No Server Communication** - Pure client-side update using stored model data.

---

## 4. Adjusting Configuration

### User Actions
```
User adjusts sliders, toggles, inputs
```

### Control Flow (Client-Side Only)

#### Temperature Slider
```javascript
// File: webapp/public/js/app.js (line 419-421)
elements.temperature.addEventListener('input', (e) => {
    elements.tempValue.textContent = e.target.value;
});
```

**Visual Flow:**
```
User drags slider
  → Input event fires
  → Update label text
  → No server call
```

#### Top-P Slider
```javascript
// File: webapp/public/js/app.js (line 424-426)
elements.topP.addEventListener('input', (e) => {
    elements.topPValue.textContent = e.target.value;
});
```

#### FP32 CPU Offload Toggle
```html
<!-- File: webapp/public/index.html (line 85) -->
<input class="form-check-input" type="checkbox" id="fp32CpuOffload" checked>
```

**All configuration changes are stored client-side until "Start Inference" is clicked.**

---

## 5. Starting Inference

### User Action
```
User clicks "Start Inference" button
```

### Complete Control Flow

#### Step 1: Button Click Event
```javascript
// File: webapp/public/js/app.js (line 429)
elements.startBtn.addEventListener('click', startInference);
```

#### Step 2: Frontend Validates & Prepares Request
```javascript
// File: webapp/public/js/app.js (line 154-187)
async function startInference() {
    const modelId = elements.modelSelect.value;
    const prompt = elements.promptInput.value.trim();

    // Validation
    if (!modelId) {
        alert('Please select a model');
        return;
    }

    if (!prompt) {
        alert('Please enter a prompt');
        return;
    }

    // Prepare config
    const config = {
        modelId,
        prompt,
        quantization: elements.quantization.value,
        enableFp32CpuOffload: elements.fp32CpuOffload.checked,
        maxLength: parseInt(elements.maxLength.value),
        temperature: parseFloat(elements.temperature.value),
        topP: parseFloat(elements.topP.value),
        gpuMemory: elements.gpuMemory.value,
        cpuMemory: elements.cpuMemory.value
    };

    // Send request
    const response = await fetch('/api/inference/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
}
```

**HTTP Request:**
```http
POST /api/inference/start HTTP/1.1
Host: localhost:3000
Content-Type: application/json

{
  "modelId": "llama2-7b",
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

#### Step 3: Express Server Receives Request
```javascript
// File: webapp/server.js (line 100-179)
app.post('/api/inference/start', (req, res) => {
    const {
        modelId,
        prompt,
        quantization = '8-bit',
        enableFp32CpuOffload = true,
        maxLength = 50,
        temperature = 0.7,
        topP = 0.9,
        gpuMemory = '14GiB',
        cpuMemory = '56GiB'
    } = req.body;

    // Validate input
    if (!modelId || !prompt) {
        return res.status(400).json({
            success: false,
            error: 'modelId and prompt are required'
        });
    }

    const model = AVAILABLE_MODELS.find(m => m.id === modelId);
    if (!model) {
        return res.status(404).json({
            success: false,
            error: 'Model not found'
        });
    }

    // Create session
    const sessionId = uuidv4();
    const session = {
        id: sessionId,
        modelId,
        modelName: model.fullName,
        prompt,
        config: {
            quantization,
            enableFp32CpuOffload,
            maxLength,
            temperature,
            topP,
            gpuMemory,
            cpuMemory
        },
        status: 'starting',
        startTime: Date.now(),
        output: '',
        metrics: {}
    };

    activeSessions.set(sessionId, session);

    // Start Python inference process
    startInferenceProcess(session);

    res.json({
        success: true,
        sessionId,
        message: 'Inference session started'
    });
});
```

#### Step 4: Server Spawns Python Process
```javascript
// File: webapp/server.js (line 225-280)
function startInferenceProcess(session) {
    const scriptPath = path.join(__dirname, '..', 'backend', 'inference_api.py');

    const args = [
        scriptPath,
        '--model', session.modelId,
        '--prompt', session.prompt,
        '--quantization', session.config.quantization,
        '--max-length', session.config.maxLength.toString(),
        '--temperature', session.config.temperature.toString(),
        '--top-p', session.config.topP.toString(),
        '--gpu-memory', session.config.gpuMemory,
        '--cpu-memory', session.config.cpuMemory,
        '--session-id', session.id,
        '--offload-folder', './offload'
    ];

    if (session.config.enableFp32CpuOffload) {
        args.push('--enable-fp32-cpu-offload');
    }

    const env = { ...process.env };
    if (process.env.HF_TOKEN) {
        env.HF_TOKEN = process.env.HF_TOKEN;
    }

    console.log(`Starting Python process for session ${session.id}`);

    const pythonProcess = spawn(PYTHON_PATH, args, {
        env,
        cwd: path.join(__dirname, '..')
    });

    session.process = pythonProcess;
    session.status = 'loading';

    // Emit initial status via WebSocket
    io.to(`session-${session.id}`).emit('status', {
        status: 'loading',
        message: 'Loading model...'
    });

    // Handle stdout, stderr, exit (see next sections)
}
```

**Command Executed:**
```bash
python backend/inference_api.py \
  --model llama2-7b \
  --prompt "Hello, world!" \
  --quantization 8-bit \
  --enable-fp32-cpu-offload \
  --max-length 50 \
  --temperature 0.7 \
  --top-p 0.9 \
  --gpu-memory 14GiB \
  --cpu-memory 56GiB \
  --session-id abc-123 \
  --offload-folder ./offload
```

#### Step 5: Python Backend Starts
```python
# File: backend/inference_api.py (line 20-50)
def main():
    parser = argparse.ArgumentParser(description='LLM Inference API')
    parser.add_argument('--model', required=True)
    parser.add_argument('--prompt', required=True)
    parser.add_argument('--quantization', default='8-bit')
    parser.add_argument('--enable-fp32-cpu-offload', action='store_true')
    # ... more arguments

    args = parser.parse_args()

    # Initialize inference engine with callback
    engine = InferenceEngine(
        model_id=args.model,
        progress_callback=emit_json
    )
```

#### Step 6: Frontend Receives Session ID
```javascript
// File: webapp/public/js/app.js (line 172-186)
const data = await response.json();

if (data.success) {
    currentSessionId = data.sessionId;
    socket.emit('subscribe', currentSessionId);  // Subscribe to updates

    isRunning = true;
    updateUIForRunning(true);
    clearOutput();
    showStatusCard();
    updateStatus('starting', 'Initializing inference session...');
}
```

#### Step 7: WebSocket Subscription
```javascript
// File: webapp/server.js (line 210-213)
socket.on('subscribe', (sessionId) => {
    socket.join(`session-${sessionId}`);
    console.log(`Client ${socket.id} subscribed to session ${sessionId}`);
});
```

**Visual Result:**
```
UI Changes:
  ✓ "Start Inference" button → Hidden
  ✓ "Stop" button → Visible
  ✓ Status card → Appears
  ✓ Status: "🚀 Starting..."
  ✓ Progress bar → 0%
```

---

## 6. Real-time Progress Updates

### Python Backend Emits Progress

#### Step 1: Model Loading Begins
```python
# File: backend/inference_engine.py (line 50-60)
def load_model(self, quantization='8-bit', ...):
    self._emit('status', {
        'status': 'loading',
        'message': f'Initializing {self.model_config["name"]}...'
    })
    self._emit('progress', {'percent': 0, 'message': 'Starting...'})
```

#### Step 2: Emit JSON to Stdout
```python
# File: backend/inference_engine.py (line 36-38)
def _emit(self, event: str, data: Dict):
    try:
        self.progress_callback(event, data)
    except Exception as e:
        print(f"Error in callback: {e}", file=sys.stderr)
```

```python
# File: backend/inference_api.py (line 15-22)
def emit_json(message_type: str, data: dict):
    message = {
        "type": message_type,
        "data": data
    }
    print(json.dumps(message), flush=True)
```

**Stdout Output:**
```json
{"type": "status", "data": {"status": "loading", "message": "Initializing LLaMA 2 7B..."}}
{"type": "progress", "data": {"percent": 10, "message": "Configuring quantization..."}}
{"type": "progress", "data": {"percent": 20, "message": "Preparing to load model..."}}
{"type": "progress", "data": {"percent": 30, "message": "Loading model weights..."}}
```

#### Step 3: Node.js Captures Stdout
```javascript
// File: webapp/server.js (line 258-275)
pythonProcess.stdout.on('data', (data) => {
    const output = data.toString();
    console.log(`[${session.id}] ${output}`);

    // Parse JSON messages from Python
    const lines = output.split('\n').filter(line => line.trim());
    lines.forEach(line => {
        try {
            const message = JSON.parse(line);
            handlePythonMessage(session, message);
        } catch (e) {
            // Not JSON, treat as regular output
            session.output += output;
            io.to(`session-${session.id}`).emit('output', { text: output });
        }
    });
});
```

#### Step 4: Node.js Handles Messages
```javascript
// File: webapp/server.js (line 296-347)
function handlePythonMessage(session, message) {
    const { type, data } = message;

    switch (type) {
        case 'status':
            session.status = data.status;
            io.to(`session-${session.id}`).emit('status', data);
            break;

        case 'progress':
            io.to(`session-${session.id}`).emit('progress', data);
            break;

        case 'memory':
            session.metrics.memory = data;
            io.to(`session-${session.id}`).emit('memory', data);
            break;

        case 'device_map':
            session.metrics.deviceMap = data;
            io.to(`session-${session.id}`).emit('device_map', data);
            break;

        // ... more cases
    }
}
```

#### Step 5: WebSocket Emits to Browser
```
Node.js
  → io.to(`session-${sessionId}`).emit('progress', data)
  → WebSocket (Socket.IO)
  → Browser
```

#### Step 6: Frontend Receives & Updates UI
```javascript
// File: webapp/public/js/app.js (line 80-83)
socket.on('progress', (data) => {
    console.log('Progress update:', data);
    updateProgress(data.percent, data.message);
});
```

```javascript
// File: webapp/public/js/app.js (line 300-305)
function updateProgress(percent, message) {
    elements.progressBar.style.width = `${percent}%`;
    if (message) {
        elements.statusDetail.textContent = message;
    }
}
```

**Visual Result:**
```
Status Card updates in real-time:
┌──────────────────────────────┐
│ 🚀 Loading...                │
│ Loading model weights...     │
│ [████████░░░░░░░░░░] 30%    │
└──────────────────────────────┘
```

---

## 7. Memory Monitoring

### Python Backend Tracks Memory

#### Step 1: Backend Checks Memory
```python
# File: backend/inference_engine.py (line 95-105)
# Get memory after loading
gpu_mem = get_gpu_memory_info()
cpu_mem = get_cpu_memory_info()

self._emit('memory', {'gpu': gpu_mem, 'cpu': cpu_mem})
```

```python
# File: memory_utils.py (line 15-32)
def get_gpu_memory_info() -> Dict[str, float]:
    if not torch.cuda.is_available():
        return {"error": "CUDA not available"}

    allocated = torch.cuda.memory_allocated(0) / 1e9
    reserved = torch.cuda.memory_reserved(0) / 1e9
    total = torch.cuda.get_device_properties(0).total_memory / 1e9
    free = total - reserved

    return {
        "allocated": round(allocated, 2),
        "reserved": round(reserved, 2),
        "free": round(free, 2),
        "total": round(total, 2)
    }
```

#### Step 2: Emit Memory Data
```json
{"type": "memory", "data": {
  "gpu": {
    "allocated": 7.2,
    "reserved": 7.5,
    "free": 8.5,
    "total": 16.0
  },
  "cpu": {
    "used": 12.5,
    "available": 51.5,
    "total": 64.0,
    "percent": 19.5
  }
}}
```

#### Step 3: Node.js Forwards to Browser
```javascript
// File: webapp/server.js (line 309-312)
case 'memory':
    session.metrics.memory = data;
    io.to(`session-${session.id}`).emit('memory', data);
    break;
```

#### Step 4: Frontend Updates Memory Bars
```javascript
// File: webapp/public/js/app.js (line 85-88)
socket.on('memory', (data) => {
    console.log('Memory update:', data);
    updateMemoryDisplay(data);
});
```

```javascript
// File: webapp/public/js/app.js (line 307-323)
function updateMemoryDisplay(memoryData) {
    if (memoryData.gpu) {
        const gpuPercent = (memoryData.gpu.allocated / memoryData.gpu.total) * 100;
        elements.gpuProgress.style.width = `${gpuPercent}%`;
        elements.gpuText.textContent =
            `${memoryData.gpu.allocated.toFixed(1)} / ${memoryData.gpu.total.toFixed(1)} GB`;
    }

    if (memoryData.cpu) {
        const cpuPercent = memoryData.cpu.percent;
        elements.cpuProgress.style.width = `${cpuPercent}%`;
        elements.cpuText.textContent =
            `${memoryData.cpu.used.toFixed(1)} / ${memoryData.cpu.total.toFixed(1)} GB`;
    }
}
```

**Visual Result:**
```
Hardware Status Card:
┌────────────────────────────┐
│ GPU Memory                 │
│ [████████░░░░] 7.2 / 16.0GB│
│                            │
│ CPU Memory                 │
│ [███░░░░░░░░] 12.5 / 64.0GB│
└────────────────────────────┘
```

---

## 8. Device Map Display

### Python Backend Analyzes Device Map

#### Step 1: Model Loaded, Device Map Available
```python
# File: backend/inference_engine.py (line 107-123)
# Analyze device map
if hasattr(self.model, 'hf_device_map'):
    self.device_map = self.model.hf_device_map
    self._emit('device_map', self._serialize_device_map(self.device_map))

    # Analyze layer distribution
    analysis = analyze_device_map(self.device_map)
    gpu_layers = analysis['device_counts'].get('0', 0)
    cpu_layers = analysis['device_counts'].get('cpu', 0)
    disk_layers = analysis['device_counts'].get('disk', 0)
```

```python
# File: backend/inference_engine.py (line 240-248)
def _serialize_device_map(self, device_map: Dict) -> Dict:
    serializable = {}
    for key, value in device_map.items():
        if isinstance(value, int):
            serializable[key] = value
        else:
            serializable[key] = str(value)
    return serializable
```

#### Step 2: Emit Device Map
```json
{"type": "device_map", "data": {
  "model.decoder.embed_tokens": "cpu",
  "model.decoder.embed_positions": "cpu",
  "model.decoder.layers.0": 0,
  "model.decoder.layers.1": 0,
  "model.decoder.layers.2": 0,
  ...
  "model.decoder.layers.28": 0,
  "model.decoder.layers.29": "cpu",
  "model.decoder.layers.30": "cpu",
  "model.decoder.layers.31": "cpu",
  "lm_head": "cpu"
}}
```

#### Step 3: Node.js Forwards Device Map
```javascript
// File: webapp/server.js (line 317-320)
case 'device_map':
    session.metrics.deviceMap = data;
    io.to(`session-${session.id}`).emit('device_map', data);
    break;
```

#### Step 4: Frontend Displays Device Map
```javascript
// File: webapp/public/js/app.js (line 95-98)
socket.on('device_map', (data) => {
    console.log('Device map:', data);
    displayDeviceMap(data);
});
```

```javascript
// File: webapp/public/js/app.js (line 382-409)
function displayDeviceMap(deviceMap) {
    elements.deviceMapCard.style.display = 'block';
    elements.deviceMapCard.classList.add('card-animate');

    let html = '<div class="row">';

    // Group by device
    const grouped = {};
    for (const [module, device] of Object.entries(deviceMap)) {
        const deviceName = device === 0 ? 'GPU' : device.toString().toUpperCase();
        if (!grouped[deviceName]) {
            grouped[deviceName] = [];
        }
        grouped[deviceName].push(module);
    }

    // Display grouped
    for (const [device, modules] of Object.entries(grouped)) {
        const color = device === 'GPU' ? 'success' : device === 'CPU' ? 'info' : 'warning';
        html += `
            <div class="col-md-6 mb-3">
                <div class="badge bg-${color} w-100 mb-2">${device} (${modules.length} modules)</div>
                <small class="text-muted">
                    ${modules.slice(0, 5).join('<br>')}
                    ${modules.length > 5 ? `<br>... and ${modules.length - 5} more` : ''}
                </small>
            </div>
        `;
    }

    html += '</div>';
    elements.deviceMapContent.innerHTML = html;
}
```

**Visual Result:**
```
Device Map Card:
┌─────────────────────────────┐
│ 🗺️  Device Map              │
├─────────────────────────────┤
│ GPU (29 modules)            │
│ model.decoder.layers.0      │
│ model.decoder.layers.1      │
│ model.decoder.layers.2      │
│ ...and 26 more              │
│                             │
│ CPU (5 modules)             │
│ model.decoder.embed_tokens  │
│ model.decoder.embed_positions│
│ ...and 3 more               │
└─────────────────────────────┘
```

---

## 9. Generation Completion

### Python Backend Finishes Generation

#### Step 1: Text Generation Complete
```python
# File: backend/inference_engine.py (line 186-212)
# Generate
output = self.model.generate(
    input_ids,
    max_length=max_length,
    temperature=temperature,
    top_p=top_p,
    top_k=top_k,
    do_sample=do_sample,
    pad_token_id=self.tokenizer.eos_token_id
)

gen_time = time.time() - gen_start

# Decode
generated_text = self.tokenizer.decode(output[0].tolist(), skip_special_tokens=True)
output_length = output.shape[1]
tokens_generated = output_length - input_length
```

#### Step 2: Collect Metrics
```python
# File: backend/inference_engine.py (line 214-230)
# Collect metrics
gpu_mem = get_gpu_memory_info()
cpu_mem = get_cpu_memory_info()

result = {
    'text': generated_text,
    'prompt': prompt,
    'metrics': {
        'loadTime': self.load_time,
        'genTime': gen_time,
        'totalTime': self.load_time + gen_time,
        'inputTokens': input_length,
        'outputTokens': output_length,
        'tokensGenerated': tokens_generated,
        'tokensPerSecond': tokens_generated / gen_time if gen_time > 0 else 0,
        'gpuMemoryUsed': gpu_mem.get('allocated', 0),
        'cpuMemoryUsed': cpu_mem.get('used', 0),
        'gpuLayers': self.metrics.get('gpu_layers', 0),
        'cpuLayers': self.metrics.get('cpu_layers', 0),
        'diskLayers': self.metrics.get('disk_layers', 0),
        'modelSizeGB': self.metrics.get('model_size_gb', 0)
    }
}
```

#### Step 3: Emit Result
```python
# File: backend/inference_engine.py (line 232-237)
self._emit('result', result)
self._emit('status', {
    'status': 'completed',
    'message': f'Generated {tokens_generated} tokens in {gen_time:.1f}s'
})

return result
```

**JSON Output:**
```json
{"type": "result", "data": {
  "text": "Hello, world! This is a generated text...",
  "prompt": "Hello, world!",
  "metrics": {
    "loadTime": 45.2,
    "genTime": 23.7,
    "totalTime": 68.9,
    "inputTokens": 3,
    "outputTokens": 33,
    "tokensGenerated": 30,
    "tokensPerSecond": 1.27,
    "gpuMemoryUsed": 7.2,
    "cpuMemoryUsed": 12.5,
    "gpuLayers": 28,
    "cpuLayers": 4,
    "diskLayers": 0,
    "modelSizeGB": 7.1
  }
}}
```

#### Step 4: Emit Complete Signal
```python
# File: backend/inference_api.py (line 85-90)
# Emit completion
emit_json('complete', {
    'status': 'completed',
    'duration': result['metrics']['totalTime'] * 1000,
    'metrics': result['metrics']
})
```

#### Step 5: Python Process Exits
```python
# File: backend/inference_api.py (line 92-95)
# Cleanup
engine.unload_model()

sys.exit(0)
```

#### Step 6: Node.js Handles Process Exit
```javascript
// File: webapp/server.js (line 285-295)
pythonProcess.on('close', (code) => {
    console.log(`[${session.id}] Process exited with code ${code}`);

    session.status = code === 0 ? 'completed' : 'failed';
    session.endTime = Date.now();
    session.duration = session.endTime - session.startTime;

    io.to(`session-${session.id}`).emit('complete', {
        status: session.status,
        duration: session.duration,
        metrics: session.metrics
    });
});
```

#### Step 7: Frontend Displays Result
```javascript
// File: webapp/public/js/app.js (line 105-108)
socket.on('result', (data) => {
    console.log('Result:', data);
    displayResult(data);
});
```

```javascript
// File: webapp/public/js/app.js (line 335-365)
function displayResult(data) {
    elements.output.innerHTML = '';

    // Display prompt
    const promptDiv = document.createElement('div');
    promptDiv.className = 'output-prompt';
    promptDiv.textContent = '📝 Prompt: ' + data.prompt;
    elements.output.appendChild(promptDiv);

    // Display separator
    const separator = document.createElement('div');
    separator.className = 'output-separator';
    elements.output.appendChild(separator);

    // Display generated text
    const outputDiv = document.createElement('div');
    outputDiv.className = 'output-generated';
    outputDiv.textContent = data.text;
    elements.output.appendChild(outputDiv);

    // Display metrics
    if (data.metrics) {
        displayMetrics(data.metrics);
    }
}
```

```javascript
// File: webapp/public/js/app.js (line 367-380)
function displayMetrics(metrics) {
    elements.metricsCard.style.display = 'block';
    elements.metricsCard.classList.add('card-animate');

    document.getElementById('metricLoadTime').textContent =
        metrics.loadTime ? `${metrics.loadTime.toFixed(1)}s` : '-';

    document.getElementById('metricGenTime').textContent =
        metrics.genTime ? `${metrics.genTime.toFixed(1)}s` : '-';

    document.getElementById('metricTPS').textContent =
        metrics.tokensPerSecond ? metrics.tokensPerSecond.toFixed(2) : '-';

    document.getElementById('metricGpuLayers').textContent =
        metrics.gpuLayers || '-';

    document.getElementById('metricCpuLayers').textContent =
        metrics.cpuLayers || '-';
}
```

#### Step 8: Frontend Handles Completion
```javascript
// File: webapp/public/js/app.js (line 115-118)
socket.on('complete', (data) => {
    console.log('Complete:', data);
    handleCompletion(data);
});
```

```javascript
// File: webapp/public/js/app.js (line 425-429)
function handleCompletion(data) {
    updateStatus(data.status, `Completed in ${(data.duration / 1000).toFixed(1)}s`);
    isRunning = false;
    updateUIForRunning(false);
}
```

**Visual Result:**
```
Output Card:
┌────────────────────────────────────┐
│ 📝 Prompt: Hello, world!           │
│ ────────────────────────────────   │
│ ✅ Generated: Hello, world! This   │
│    is a generated text demonstra-  │
│    ting the inference capability... │
└────────────────────────────────────┘

Metrics Card:
┌────────────────────────────────────┐
│ Load Time: 45.2s                   │
│ Generation Time: 23.7s             │
│ Tokens/Second: 1.27                │
│ GPU Layers: 28 | CPU Layers: 4    │
└────────────────────────────────────┘

Status: ✅ Complete!
Progress: 100%
Buttons: "Start Inference" visible again
```

---

## 10. Stopping Inference

### User Action
```
User clicks "Stop" button during inference
```

### Control Flow

#### Step 1: Button Click Event
```javascript
// File: webapp/public/js/app.js (line 432)
elements.stopBtn.addEventListener('click', stopInference);
```

#### Step 2: Frontend Sends Stop Request
```javascript
// File: webapp/public/js/app.js (line 203-217)
async function stopInference() {
    if (!currentSessionId) return;

    try {
        const response = await fetch(`/api/session/${currentSessionId}/stop`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            updateStatus('stopped', 'Inference stopped by user');
            isRunning = false;
            updateUIForRunning(false);
        }
    } catch (error) {
        console.error('Error stopping inference:', error);
    }
}
```

**HTTP Request:**
```http
POST /api/session/abc-123/stop HTTP/1.1
Host: localhost:3000
```

#### Step 3: Server Kills Python Process
```javascript
// File: webapp/server.js (line 193-202)
app.post('/api/session/:sessionId/stop', (req, res) => {
    const session = activeSessions.get(req.params.sessionId);
    if (session && session.process) {
        session.process.kill();  // Send SIGTERM to Python process
        session.status = 'stopped';
        res.json({ success: true, message: 'Session stopped' });
    } else {
        res.status(404).json({ success: false, error: 'Session not found' });
    }
});
```

#### Step 4: Python Process Receives SIGTERM
```python
# File: backend/inference_api.py (line 100-105)
except KeyboardInterrupt:
    emit_json('status', {
        'status': 'interrupted',
        'message': 'Inference interrupted by user'
    })
    sys.exit(130)
```

#### Step 5: Node.js Handles Process Exit
```javascript
// File: webapp/server.js (line 285-295)
pythonProcess.on('close', (code) => {
    console.log(`[${session.id}] Process exited with code ${code}`);

    session.status = code === 0 ? 'completed' : 'failed';
    // ... cleanup

    io.to(`session-${session.id}`).emit('complete', {
        status: session.status,
        duration: session.duration
    });
});
```

#### Step 6: Frontend Updates UI
```javascript
// File: webapp/public/js/app.js (line 425-429)
function handleCompletion(data) {
    updateStatus('stopped', 'Inference stopped by user');
    isRunning = false;
    updateUIForRunning(false);
}
```

**Visual Result:**
```
Status: ⏹️ Stopped
"Stop" button → Hidden
"Start Inference" button → Visible
Session cleaned up after 1 hour
```

---

## 11. Error Handling

### Scenario: Model Loading Fails

#### Step 1: Python Backend Encounters Error
```python
# File: backend/inference_engine.py (line 40-92)
try:
    # ... model loading code
    self.model = AutoModelForCausalLM.from_pretrained(...)
except Exception as e:
    self._emit('error', {'error': str(e)})
    import traceback
    traceback.print_exc()
    return False
```

#### Step 2: Emit Error via JSON
```json
{"type": "error", "data": {"error": "CUDA out of memory: tried to allocate 2.5GB"}}
```

#### Step 3: Python Prints Traceback to Stderr
```python
traceback.print_exc()  # Goes to stderr
```

#### Step 4: Node.js Captures Stderr
```javascript
// File: webapp/server.js (line 277-283)
pythonProcess.stderr.on('data', (data) => {
    const error = data.toString();
    console.error(`[${session.id}] ERROR: ${error}`);

    io.to(`session-${session.id}`).emit('error', {
        error: error
    });
});
```

#### Step 5: WebSocket Emits Error to Browser
```
Node.js
  → io.to(`session-${sessionId}`).emit('error', {error: "..."})
  → Browser
```

#### Step 6: Frontend Displays Error
```javascript
// File: webapp/public/js/app.js (line 110-113)
socket.on('error', (data) => {
    console.error('Error:', data);
    displayError(data.error);
});
```

```javascript
// File: webapp/public/js/app.js (line 411-423)
function displayError(error) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'output-error';
    errorDiv.innerHTML = `<strong>❌ Error:</strong><br>${error}`;
    elements.output.appendChild(errorDiv);

    updateStatus('failed', 'Inference failed');
    isRunning = false;
    updateUIForRunning(false);
}
```

**Visual Result:**
```
Output Card:
┌────────────────────────────────────┐
│ ❌ Error:                          │
│ CUDA out of memory: tried to      │
│ allocate 2.5GB. Try reducing GPU  │
│ memory limit or using smaller     │
│ model.                             │
└────────────────────────────────────┘

Status: ❌ Failed
"Start Inference" button visible again
```

---

## 📊 Complete Flow Diagram

```
USER ACTION
    │
    ├── Page Load
    │   └→ Browser → GET / → Express → HTML/CSS/JS
    │       └→ JS Executes → WebSocket Connect
    │           └→ Socket.IO Handshake → Connected ✅
    │
    ├── Load Models
    │   └→ fetch('/api/models')
    │       └→ Express → Return MODEL_REGISTRY
    │           └→ Populate Dropdown ✅
    │
    ├── Select Model
    │   └→ Change Event → Update Model Info (Client-Side) ✅
    │
    ├── Adjust Config
    │   └→ Slider/Toggle Events → Update Values (Client-Side) ✅
    │
    ├── Start Inference ⭐
    │   └→ POST /api/inference/start {config}
    │       └→ Express Validates → Create Session → spawn(python)
    │           └→ Python inference_api.py
    │               └→ InferenceEngine.load_model()
    │                   ├→ emit('status') → stdout → Node.js → WebSocket → Browser ✅
    │                   ├→ emit('progress') → stdout → Node.js → WebSocket → Browser ✅
    │                   ├→ emit('memory') → stdout → Node.js → WebSocket → Browser ✅
    │                   └→ emit('device_map') → stdout → Node.js → WebSocket → Browser ✅
    │               └→ InferenceEngine.generate()
    │                   ├→ emit('generation_start') → stdout → Node.js → WebSocket → Browser ✅
    │                   └→ emit('result') → stdout → Node.js → WebSocket → Browser ✅
    │               └→ emit('complete') → Python Exit
    │                   └→ Node.js Process Exit Handler → WebSocket → Browser
    │                       └→ Display Results & Metrics ✅
    │
    ├── Stop Inference
    │   └→ POST /api/session/:id/stop
    │       └→ Express → process.kill() → SIGTERM → Python
    │           └→ Python Exit → Node.js Handler → WebSocket → Browser ✅
    │
    └── Error Occurs
        └→ Python Exception → emit('error') → stdout/stderr → Node.js → WebSocket → Browser
            └→ Display Error Message ✅
```

---

## 🎯 Summary

### Communication Channels

1. **HTTP REST API** - Frontend ↔ Express Server
   - GET /api/models
   - POST /api/inference/start
   - GET /api/session/:id
   - POST /api/session/:id/stop

2. **WebSocket (Socket.IO)** - Express Server ↔ Browser
   - Bidirectional real-time communication
   - Events: status, progress, memory, device_map, result, error, complete

3. **JSON stdout** - Python ↔ Node.js
   - Unidirectional (Python → Node.js)
   - Structured JSON messages
   - Types: status, progress, memory, device_map, result, error, complete

4. **Process Spawn** - Node.js ↔ Python
   - Child process management
   - stdin/stdout/stderr pipes
   - Exit code handling

### Key Design Patterns

1. **Event-Driven Architecture** - All updates via events
2. **Pub/Sub Pattern** - WebSocket rooms for session isolation
3. **Callback Pattern** - Python progress callbacks
4. **Session Management** - UUID-based tracking
5. **Process Isolation** - Each inference in separate process

### Timing & Performance

| Operation | Duration | Latency |
|-----------|----------|---------|
| Page Load | ~1-2s | N/A |
| Model List | ~10-50ms | <100ms |
| Start Request | ~50-100ms | <200ms |
| Python Spawn | ~100-500ms | <1s |
| Model Load | 60-120s | N/A |
| Generation | 100-150s | N/A |
| WebSocket Update | <50ms | <100ms |
| Stop Request | <100ms | <200ms |

---

This control flow documentation provides complete traceability from every UI action through the full stack to the backend and back to the user interface. Each section includes actual code references, data formats, and visual results.

