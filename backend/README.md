# Backend Module

Python backend for LLM inference and fine-tuning, designed to work with the Node.js Express frontend.

## 📁 Structure

```
backend/
├── __init__.py              # Module initialization
├── config.py                # Configuration and model registry
├── inference_engine.py      # Core inference engine
├── inference_api.py         # CLI wrapper for Node.js integration
├── standalone_server.py     # Optional Flask REST API server
└── README.md               # This file
```

## 🎯 Architecture

### Primary Architecture (Recommended)
```
Node.js Express Server (webapp/server.js)
    ↓ spawn child process
Python CLI (backend/inference_api.py)
    ↓ uses
Inference Engine (backend/inference_engine.py)
    ↓ communicates via
JSON stdout messages → WebSocket → Browser
```

### Alternative Architecture (Standalone)
```
Python Flask Server (backend/standalone_server.py)
    ↓ REST API
Browser Frontend
```

## 🔧 Components

### 1. config.py
Centralized configuration management:
- **MODEL_REGISTRY**: Dictionary of all supported models with metadata
- **DEFAULT_INFERENCE_CONFIG**: Default inference parameters
- **BackendConfig**: Configuration class with environment variable handling
- **Helper functions**: Memory parsing, quantization config generation

**Supported Models:**
- OPT-30B (Meta) - 30B parameters
- LLaMA 2 7B - 7B parameters
- LLaMA 2 13B - 13B parameters
- Falcon 7B - 7B parameters

### 2. inference_engine.py
Core inference functionality:
- **InferenceEngine class**: Main inference engine
- **load_model()**: Load model with quantization and offloading
- **generate()**: Generate text with streaming support
- **unload_model()**: Clean up and free memory
- **Progress callbacks**: Real-time updates during loading and generation

**Features:**
- 8-bit and 4-bit quantization support
- FP32 CPU offload for non-quantizable modules
- Automatic device mapping (GPU/CPU/Disk)
- Memory monitoring
- Device map analysis
- Flexible generation parameters

### 3. inference_api.py
Command-line interface for Node.js integration:
- Parses command-line arguments
- Initializes InferenceEngine
- Emits JSON messages to stdout
- Handles errors and cleanup

**Communication Protocol:**
```json
// Status update
{"type": "status", "data": {"status": "loading", "message": "Loading model..."}}

// Progress update
{"type": "progress", "data": {"percent": 50, "message": "Loading weights..."}}

// Memory update
{"type": "memory", "data": {"gpu": {...}, "cpu": {...}}}

// Device map
{"type": "device_map", "data": {...}}

// Result
{"type": "result", "data": {"text": "...", "metrics": {...}}}

// Error
{"type": "error", "data": {"error": "..."}}
```

### 4. standalone_server.py (Optional)
Flask-based REST API server:
- Alternative to Node.js architecture
- REST endpoints for model management
- Session-based inference
- Server-Sent Events (SSE) for streaming
- Thread-based background processing

## 🚀 Usage

### With Node.js (Recommended)

The backend is automatically called by the Node.js server. Just start the webapp:

```bash
cd webapp
npm start
```

### Standalone CLI

Test the backend directly:

```bash
python backend/inference_api.py \
  --model llama2-7b \
  --prompt "Hello, world!" \
  --quantization 8-bit \
  --enable-fp32-cpu-offload \
  --max-length 50 \
  --temperature 0.7 \
  --gpu-memory 6GiB \
  --cpu-memory 12GiB \
  --session-id test-123
```

### Standalone Flask Server

Run the Flask server independently:

```bash
# Install Flask dependencies
pip install flask flask-cors

# Set environment
export HF_TOKEN=your_token_here
export BACKEND_PORT=5000

# Run server
python backend/standalone_server.py
```

**Test with curl:**
```bash
# Get models
curl http://localhost:5000/api/models

# Start inference
curl -X POST http://localhost:5000/api/inference/start \
  -H "Content-Type: application/json" \
  -d '{
    "modelId": "llama2-7b",
    "prompt": "Once upon a time",
    "quantization": "8-bit",
    "maxLength": 30
  }'

# Get session status
curl http://localhost:5000/api/session/<session-id>
```

### Python Module Import

Use the backend as a Python module:

```python
from backend.inference_engine import InferenceEngine
from backend.config import config

# Define callback for progress
def progress_callback(event, data):
    print(f"{event}: {data}")

# Initialize engine
engine = InferenceEngine(
    model_id='llama2-7b',
    progress_callback=progress_callback
)

# Load model
engine.load_model(
    quantization='8-bit',
    enable_fp32_cpu_offload=True,
    gpu_memory='6GiB',
    cpu_memory='12GiB'
)

# Generate text
result = engine.generate(
    prompt="Hello, world!",
    max_length=50,
    temperature=0.7
)

print(result['text'])
print(result['metrics'])

# Cleanup
engine.unload_model()
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required
export HF_TOKEN=your_huggingface_token

# Optional
export HF_CACHE_DIR=./model_cache
export OFFLOAD_DIR=./offload
export LOG_LEVEL=INFO
export CUDA_VISIBLE_DEVICES=0
```

### Adding New Models

Edit `backend/config.py`:

```python
MODEL_REGISTRY = {
    'your-model-id': {
        'id': 'your-model-id',
        'name': 'Your Model Name',
        'hf_name': 'organization/model-name',
        'size_gb': 14,
        'size_gb_int8': 7,
        'size_gb_int4': 3.5,
        'num_params': 7,
        'min_gpu_memory': 8,
        'min_cpu_memory': 16,
        'recommended_gpu': 6,
        'recommended_cpu': 12,
        'supported_tasks': ['inference'],
        'quantization_support': ['8-bit', '4-bit', 'none'],
        'architecture': 'llama',
        'num_layers': 32
    }
}
```

## 📊 Features

### Quantization Support

**8-bit (LLM.int8())**
- 50% memory reduction
- <1% accuracy loss
- Outlier detection (threshold: 6.0)
- Mixed-precision computation

**4-bit (NF4)**
- 75% memory reduction
- 1-3% accuracy loss
- Double quantization support
- FP16 compute dtype

**None (FP16/FP32)**
- Full precision
- Highest accuracy
- Highest memory usage

### Memory Management

**FP32 CPU Offload**
- Offloads non-quantizable modules to CPU
- Frees ~1-2GB GPU memory
- Modules affected:
  - Embeddings
  - LayerNorm
  - lm_head

**Automatic Device Mapping**
- GPU: Most critical layers
- CPU: Overflow layers
- Disk: Emergency offload (if needed)

**Memory Limits**
- GPU: Configurable (e.g., 14GiB)
- CPU: Configurable (e.g., 56GiB)
- Automatic allocation within limits

### Progress Tracking

**Events emitted during inference:**
1. `status` - Current operation status
2. `progress` - Percentage complete with message
3. `memory` - GPU/CPU memory usage
4. `device_map` - Layer allocation across devices
5. `generation_start` - Generation beginning
6. `result` - Final output with metrics
7. `error` - Error messages
8. `complete` - Inference completed

### Metrics Collected

```python
{
    'loadTime': 45.2,              # Model load time (seconds)
    'genTime': 23.7,               # Generation time (seconds)
    'totalTime': 68.9,             # Total time (seconds)
    'inputTokens': 12,             # Input token count
    'outputTokens': 42,            # Output token count
    'tokensGenerated': 30,         # Generated tokens
    'tokensPerSecond': 1.27,       # Generation speed
    'gpuMemoryUsed': 7.2,          # GPU memory (GB)
    'cpuMemoryUsed': 12.5,         # CPU memory (GB)
    'gpuLayers': 28,               # Layers on GPU
    'cpuLayers': 4,                # Layers on CPU
    'diskLayers': 0,               # Layers on disk
    'modelSizeGB': 7.1             # Total model size
}
```

## 🔍 Debugging

### Enable Debug Output

```bash
# In inference_api.py
python -u backend/inference_api.py ...  # Unbuffered output

# In standalone_server.py
export DEBUG=true
python backend/standalone_server.py
```

### Common Issues

**1. Import errors**
```bash
# Make sure parent directory is in path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**2. HF Token not found**
```bash
# Set token
export HF_TOKEN=your_token_here
```

**3. CUDA out of memory**
```bash
# Reduce GPU memory limit
--gpu-memory 10GiB  # Instead of 14GiB

# Or use more aggressive quantization
--quantization 4-bit  # Instead of 8-bit
```

**4. Model not found**
```bash
# Check model ID
python -c "from backend.config import config; print(list(config.MODEL_REGISTRY.keys()))"
```

## 🧪 Testing

### Test Backend Components

```bash
# Test config
python -c "from backend.config import config; print(config.get_all_models())"

# Test inference engine (requires GPU)
python -c "
from backend.inference_engine import InferenceEngine
engine = InferenceEngine('llama2-7b')
print('Engine initialized:', engine.model_id)
"

# Test CLI
python backend/inference_api.py --help
```

### Integration Test

```bash
# Full end-to-end test
cd webapp
npm start

# In browser: http://localhost:3000
# Select model → Enter prompt → Start inference
```

## 📚 API Reference

### InferenceEngine

```python
class InferenceEngine:
    def __init__(self, model_id: str, progress_callback: Callable = None)

    def load_model(
        self,
        quantization: str = '8-bit',
        enable_fp32_cpu_offload: bool = True,
        gpu_memory: str = '14GiB',
        cpu_memory: str = '56GiB',
        offload_folder: str = './offload'
    ) -> bool

    def generate(
        self,
        prompt: str,
        max_length: int = 50,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        do_sample: bool = True,
        stream: bool = False
    ) -> Dict

    def unload_model(self)

    def get_model_info(self) -> Dict
```

### BackendConfig

```python
class BackendConfig:
    def get_model_config(self, model_id: str) -> Dict
    def get_all_models(self) -> List[Dict]
    def validate_memory_config(self, gpu_memory: str, cpu_memory: str, model_id: str) -> bool
    def get_recommended_config(self, model_id: str, quantization: str = '8-bit') -> Dict
```

## 🔒 Security

- **Token handling**: HF_TOKEN via environment only
- **Input validation**: All parameters validated
- **Process isolation**: Each inference in separate process
- **Memory limits**: Enforced to prevent OOM
- **Error handling**: Comprehensive exception catching

## 📈 Performance

### Expected Performance (OPT-30B on RTX 5060 Ti):

| Configuration | Load Time | Gen Time (30 tokens) |
|---------------|-----------|---------------------|
| 8-bit + CPU offload | 60-120s | 100-150s |
| 4-bit | 60-90s | 80-120s |
| FP16 (baseline) | 60-120s | 500s+ |

### Optimization Tips:

1. **Use 8-bit quantization** - Best balance
2. **Enable FP32 CPU offload** - Frees GPU memory
3. **Adjust memory limits** - Based on hardware
4. **Use smaller models** - For faster iteration
5. **Cache models** - Set HF_CACHE_DIR

## 🤝 Contributing

To add new features:

1. **New model support**: Update `MODEL_REGISTRY` in `config.py`
2. **New inference features**: Extend `InferenceEngine` in `inference_engine.py`
3. **New API endpoints**: Add to `standalone_server.py`
4. **New communication events**: Update `inference_api.py`

## 📄 License

Same as parent project (MIT)

---

**Questions?** Check the main [README](../README_OPTIMIZED.md) or webapp [documentation](../webapp/README.md).
