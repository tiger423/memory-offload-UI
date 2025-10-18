# LLM Inference & Fine-tuning Web UI

A modern web interface for running Large Language Model (LLM) inference with support for quantization, memory offloading, and real-time monitoring.

![Architecture](https://img.shields.io/badge/Stack-Node.js%20%2B%20Express%20%2B%20Python-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 Features

### Current Features (v1.0)
- ✅ **Model Selection** - Choose from multiple pre-configured models
- ✅ **Inference Mode** - Text generation with streaming output
- ✅ **8-bit/4-bit Quantization** - Reduce memory usage by 50-75%
- ✅ **FP32 CPU Offload** - Optimize GPU memory allocation
- ✅ **Real-time Monitoring** - Track GPU/CPU memory usage
- ✅ **Device Map Visualization** - See layer distribution
- ✅ **Performance Metrics** - Load time, generation speed, tokens/sec
- ✅ **WebSocket Updates** - Live progress and status updates

### Coming Soon
- 🔄 **Fine-tuning Mode** - Train models on custom datasets
- 🔄 **Batch Inference** - Process multiple prompts
- 🔄 **Model Comparison** - Compare different configurations
- 🔄 **Result Export** - Save outputs to files

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Browser (Frontend)               │
│  • Bootstrap 5 + Socket.IO             │
│  • Real-time UI updates                  │
└─────────────┬───────────────────────────┘
              │ HTTP + WebSocket
┌─────────────▼───────────────────────────┐
│      Node.js Express Server             │
│  • REST API endpoints                    │
│  • WebSocket server (Socket.IO)   │
│  • Process management                  │
└─────────────┬───────────────────────────┘
              │ Child Process (spawn)
┌─────────────▼───────────────────────────┐
│      Python Backend                         │
│  • HuggingFace Transformers       │
│  • Model loading & inference         │
│  • Memory management                 │
└─────────────────────────────────────────┘
```

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 24.04 (or similar Linux), Windows 10/11
- **GPU**: NVIDIA GPU with CUDA support (16GB+ VRAM recommended)
- **RAM**: 32GB+ (64GB recommended for large models)
- **Storage**: 100GB+ free space (for model caching)

### Software Requirements
- **Node.js**: v18.0.0 or higher
- **Python**: 3.9 or higher
- **CUDA**: 11.8 or higher (for GPU support)

## 🚀 Installation

### 1. Clone Repository

```bash
cd vLLM/webapp
```

### 2. Install Node.js Dependencies

```bash
npm install
```

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install torch transformers accelerate bitsandbytes psutil
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your HuggingFace token
nano .env
```

**Required environment variables:**
```env
PORT=3000
PYTHON_PATH=python  # Or path to your Python executable
HF_TOKEN=your_huggingface_token_here
```

**Get your HuggingFace token:**
1. Go to https://huggingface.co/settings/tokens
2. Create a new token with read access
3. Copy and paste into `.env`

### 5. Test Python Backend

```bash
# Test if Python can import required modules
python -c "import torch, transformers, accelerate, bitsandbytes; print('✅ All modules installed')"

# Test CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## 📦 Available Models

The UI comes pre-configured with these models:

| Model | Size | Min GPU | Min RAM | Quantization |
|-------|------|---------|---------|--------------|
| **OPT-30B** | 30B params (~60GB FP16) | 16GB | 32GB | 8-bit, 4-bit |
| **LLaMA 2 7B** | 7B params (~14GB FP16) | 8GB | 16GB | 8-bit, 4-bit |
| **LLaMA 2 13B** | 13B params (~26GB FP16) | 16GB | 32GB | 8-bit, 4-bit |
| **Falcon 7B** | 7B params (~14GB FP16) | 8GB | 16GB | 8-bit, 4-bit |

**Note**: With 8-bit quantization, memory requirements are reduced by ~50%.

## 🎮 Usage

### Start the Server

```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start
```

The server will start on `http://localhost:3000`

### Using the Web Interface

1. **Open Browser**
   ```
   http://localhost:3000
   ```

2. **Select Task**
   - Choose "Inference" (Fine-tuning coming soon)

3. **Select Model**
   - Pick a model from the dropdown
   - View memory requirements

4. **Configure Options**
   - **Quantization**: 8-bit (recommended), 4-bit, or none
   - **FP32 CPU Offload**: Enable to free GPU memory (~2GB)
   - **Advanced Settings**:
     - GPU Memory Limit: e.g., `14GiB`
     - CPU Memory Limit: e.g., `56GiB`
     - Max Length: Token limit for generation
     - Temperature: 0.0-2.0 (creativity)
     - Top P: 0.0-1.0 (nucleus sampling)

5. **Enter Prompt**
   - Type your text prompt
   - Example: "Hugging Face is pushing the convention that a unicorn with two horns becomes a llama."

6. **Start Inference**
   - Click "Start Inference"
   - Watch real-time progress
   - Monitor GPU/CPU memory usage
   - View generated output

### API Endpoints

The server exposes REST API endpoints:

#### Get Available Models
```bash
GET /api/models
```

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
      "minGpuMemory": "16GB",
      "minRamMemory": "32GB",
      "supportedTasks": ["inference"],
      "quantizationSupport": ["8-bit", "4-bit"]
    }
  ]
}
```

#### Start Inference Session
```bash
POST /api/inference/start
Content-Type: application/json

{
  "modelId": "opt-30b",
  "prompt": "Your prompt here",
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

#### Get Session Status
```bash
GET /api/session/:sessionId
```

#### Stop Session
```bash
POST /api/session/:sessionId/stop
```

### WebSocket Events

Connect to Socket.IO for real-time updates:

```javascript
const socket = io('http://localhost:3000');

// Subscribe to session
socket.emit('subscribe', sessionId);

// Listen for events
socket.on('status', (data) => {
  console.log('Status:', data.status, data.message);
});

socket.on('progress', (data) => {
  console.log('Progress:', data.percent);
});

socket.on('memory', (data) => {
  console.log('GPU:', data.gpu.allocated, 'GB');
  console.log('CPU:', data.cpu.used, 'GB');
});

socket.on('result', (data) => {
  console.log('Generated text:', data.text);
  console.log('Metrics:', data.metrics);
});
```

## 🎨 Screenshots

### Main Interface
- Model selection dropdown
- Task selection (Inference/Fine-tuning)
- Quantization options
- Advanced configuration panel
- Real-time hardware monitoring

### Output Display
- Streaming text generation
- Performance metrics
- Device map visualization
- Memory usage graphs

## ⚙️ Configuration

### Customizing Available Models

Edit `server.js` to add more models:

```javascript
const AVAILABLE_MODELS = [
    {
        id: 'your-model-id',
        name: 'Your Model Name',
        fullName: 'huggingface/model-name',
        size: '7B parameters',
        minGpuMemory: '8GB',
        minRamMemory: '16GB',
        supportedTasks: ['inference'],
        quantizationSupport: ['8-bit', '4-bit']
    }
];
```

### Adjusting Memory Limits

For different hardware configurations:

**16GB GPU + 64GB RAM (Recommended):**
```javascript
max_memory: {
    0: "14GiB",    // Leave 2GB for CUDA overhead
    "cpu": "56GiB" // Leave 8GB for OS
}
```

**24GB GPU + 128GB RAM (High-end):**
```javascript
max_memory: {
    0: "22GiB",
    "cpu": "120GiB"
}
```

**8GB GPU + 32GB RAM (Budget):**
```javascript
max_memory: {
    0: "6GiB",
    "cpu": "28GiB"
}
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Server won't start
```bash
# Check if port is in use
netstat -ano | findstr :3000  # Windows
lsof -i :3000                 # Linux

# Kill process or change PORT in .env
```

#### 2. Python process fails
```bash
# Check Python path
which python  # Linux
where python  # Windows

# Update PYTHON_PATH in .env
```

#### 3. CUDA errors
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Update CUDA drivers
# Reinstall torch with correct CUDA version
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

#### 4. Out of Memory (OOM)
- Reduce `gpuMemory` limit in advanced settings
- Enable 8-bit or 4-bit quantization
- Enable FP32 CPU offload
- Choose a smaller model

#### 5. HuggingFace token errors
```bash
# Verify token is set
echo $HF_TOKEN  # Linux
echo %HF_TOKEN% # Windows

# Re-export token
export HF_TOKEN="your_token_here"
```

### Debug Mode

Enable detailed logging:

```bash
# In server.js, add:
const DEBUG = true;

# Run with verbose output
NODE_ENV=development npm start
```

## 📊 Performance Tips

### For Optimal Performance:

1. **Use 8-bit quantization** - Best balance of speed and accuracy
2. **Enable FP32 CPU offload** - Frees ~2GB GPU memory
3. **Use NVMe SSD** - For faster disk offloading (if needed)
4. **Close other GPU apps** - Free up VRAM
5. **Monitor memory usage** - Adjust limits accordingly

### Expected Performance (OPT-30B on RTX 5060 Ti):

| Configuration | Load Time | Gen Time (30 tokens) | Speedup |
|---------------|-----------|---------------------|---------|
| FP32 + Disk offload | 1-2 min | ~500s | 1x (baseline) |
| 8-bit + CPU offload | 1-2 min | ~100-150s | **3-5x faster** |

## 🔐 Security Considerations

1. **Never commit `.env` file** - Contains sensitive tokens
2. **Use environment variables** - Don't hardcode credentials
3. **Restrict network access** - Use firewall for production
4. **Keep dependencies updated** - Run `npm audit` regularly
5. **Validate user input** - Implemented in API routes

## 📝 Development

### Project Structure

```
webapp/
├── server.js              # Express server + WebSocket
├── package.json           # Node.js dependencies
├── .env                   # Environment config (gitignored)
├── .env.example          # Example configuration
├── public/
│   ├── index.html        # Main UI
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── app.js        # Frontend JavaScript
└── README.md             # This file

../python/
├── inference_api.py      # Python inference wrapper
└── ...

../
├── memory_utils.py       # Memory monitoring utilities
├── opt_30b_optimized.py  # Standalone inference script
└── ...
```

### Adding New Features

1. **New API endpoint** - Add route in `server.js`
2. **New UI component** - Update `index.html` and `app.js`
3. **New Python feature** - Modify `inference_api.py`
4. **New model support** - Add to `AVAILABLE_MODELS` in `server.js`

### Testing

```bash
# Test Node.js server
npm start

# Test Python backend directly
python ../python/inference_api.py \
  --model facebook/opt-30b \
  --prompt "Test prompt" \
  --quantization 8-bit \
  --session-id test-123
```

## 📄 License

MIT License - See parent directory for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: See parent [CLAUDE.md](../CLAUDE.md) and [README_OPTIMIZED.md](../README_OPTIMIZED.md)
- **Community**: HuggingFace Forums

---

**Built with ❤️ using Node.js, Express, Socket.IO, and HuggingFace Transformers**
