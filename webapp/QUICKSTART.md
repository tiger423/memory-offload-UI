# Quick Start Guide

Get the LLM Inference UI running in 5 minutes!

## ⚡ Prerequisites Check

```bash
# Check Node.js (need v18+)
node --version

# Check Python (need 3.9+)
python --version

# Check if you have a GPU
nvidia-smi
```

## 🚀 Installation (5 Steps)

### Step 1: Navigate to webapp directory
```bash
cd vLLM/webapp
```

### Step 2: Install Node.js packages
```bash
npm install
```

### Step 3: Install Python packages
```bash
pip install torch transformers accelerate bitsandbytes psutil
```

### Step 4: Configure environment
```bash
# Copy example file
cp .env.example .env

# Edit the file and add your HuggingFace token
# Get token from: https://huggingface.co/settings/tokens
nano .env  # or use any text editor
```

**Required `.env` content:**
```env
PORT=3000
PYTHON_PATH=python
HF_TOKEN=hf_your_token_here
```

### Step 5: Start the server
```bash
npm start
```

## 🎯 First Inference

1. Open browser: http://localhost:3000

2. Select model: **LLaMA 2 7B** (smallest, fastest to load)

3. Keep defaults:
   - Task: Inference
   - Quantization: 8-bit
   - FP32 CPU Offload: ✅ Enabled

4. Enter prompt:
   ```
   Once upon a time, in a land far away,
   ```

5. Click **"Start Inference"**

6. Watch the magic happen! ✨
   - Model loads in ~30-60 seconds
   - Generation takes ~20-30 seconds
   - Real-time memory monitoring

## 📊 What You'll See

### During Loading:
```
🚀 Starting...
📥 Loading model...
⏳ This may take 1-2 minutes...
✅ Model loaded successfully!
```

### During Generation:
```
✍️ Generating text...
💾 GPU Memory: 7.2 / 16.0 GB
💾 CPU Memory: 12.5 / 64.0 GB
```

### Final Output:
```
📝 Prompt: Once upon a time, in a land far away,

✅ Generated: Once upon a time, in a land far away,
there lived a brave knight who protected the kingdom...

📊 Metrics:
  Load Time: 45.2s
  Generation Time: 23.7s
  Tokens/Second: 1.27
  GPU Layers: 28
  CPU Layers: 4
```

## 🎛️ Recommended First-Time Settings

### For Quick Testing (Fastest):
- Model: **LLaMA 2 7B**
- Quantization: **8-bit**
- Max Length: **30**
- GPU Memory: **6GiB**
- CPU Memory: **28GiB**

### For Best Quality:
- Model: **LLaMA 2 13B**
- Quantization: **8-bit**
- FP32 CPU Offload: ✅ **Enabled**
- Max Length: **50**
- Temperature: **0.7**

### For Largest Model:
- Model: **OPT-30B**
- Quantization: **8-bit**
- FP32 CPU Offload: ✅ **Enabled**
- GPU Memory: **14GiB**
- CPU Memory: **56GiB**

## ❓ Common First-Time Issues

### "Cannot find module 'express'"
```bash
# Install dependencies
npm install
```

### "HF_TOKEN not configured"
```bash
# Get token from https://huggingface.co/settings/tokens
# Add to .env file
echo 'HF_TOKEN=hf_your_token_here' >> .env
```

### "CUDA not available"
```bash
# Check GPU
nvidia-smi

# Install CUDA-enabled PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### "Port 3000 already in use"
```bash
# Change port in .env
echo 'PORT=3001' >> .env
```

### Python process fails
```bash
# Check Python path
which python  # Linux/Mac
where python  # Windows

# Update in .env
PYTHON_PATH=/path/to/your/python
```

## 🎓 Next Steps

Once you've run your first inference:

1. **Try different models** - Compare LLaMA, OPT, Falcon
2. **Experiment with settings** - Adjust temperature, top-p
3. **Monitor performance** - Check GPU/CPU usage
4. **View device map** - See layer distribution
5. **Compare configurations** - 8-bit vs 4-bit quantization

## 📚 Learn More

- [Full README](README.md) - Complete documentation
- [API Reference](README.md#api-endpoints) - REST endpoints
- [Troubleshooting](README.md#troubleshooting) - Common issues
- [Performance Tips](README.md#performance-tips) - Optimization guide

## 💡 Pro Tips

1. **Start with small models** - LLaMA 2 7B loads faster
2. **Enable 8-bit quantization** - Best balance of speed/quality
3. **Use FP32 CPU offload** - Frees GPU memory
4. **Monitor memory usage** - Adjust limits as needed
5. **Keep browser console open** - See WebSocket messages

## 🎉 Success Checklist

- [ ] Server starts without errors
- [ ] Can access http://localhost:3000
- [ ] Models load successfully
- [ ] Inference generates text
- [ ] Memory monitoring shows usage
- [ ] No CUDA errors
- [ ] Output looks reasonable

If all checks pass - **Congratulations!** 🎊 You're ready to explore LLM inference!

---

**Need help?** Check the [full README](README.md) or open an issue on GitHub.
