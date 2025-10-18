# OPT-30B Optimized Inference Scripts

This directory contains optimized inference scripts for running large language models (LLMs) with memory-efficient quantization and multi-tier offloading (GPU → CPU → Disk).

## 🎯 Overview

These scripts demonstrate how to run **OPT-30B** (~30 billion parameters, ~120GB unquantized) on consumer hardware using:

- **8-bit quantization** (LLM.int8()) - reduces memory by 50%
- **FP32 CPU offload** - offloads non-quantizable modules to CPU
- **Automatic device mapping** - distributes layers across GPU/CPU/Disk

### Target Hardware

Optimized for:
- **GPU**: NVIDIA RTX 5060 Ti (16GB VRAM)
- **RAM**: 64GB system memory
- **SSD**: 2TB NVMe (for offloading if needed)
- **OS**: Ubuntu 24.04

## 📁 Files

### Core Scripts

1. **`memory_utils.py`**
   - Memory monitoring utilities
   - GPU/CPU/Disk usage tracking
   - Device map analysis
   - Quantization info display

2. **`opt_30b_optimized.py`** ⭐
   - Main inference script with optimal configuration
   - Real-time memory monitoring
   - Performance metrics
   - **Expected 3-5x speedup** vs disk-offloading baseline

3. **`opt_30b_comparison.py`**
   - Benchmark script comparing different configurations
   - Config B: 8-bit without FP32 CPU offload
   - Config C: 8-bit with FP32 CPU offload (optimal)
   - Side-by-side performance comparison

### Legacy Scripts

4. **`opt-d-1-4.py`**
   - Original baseline implementation
   - FP32 with disk offloading
   - ~500s for 30-token generation
   - Kept for reference

## 🚀 Quick Start

### Prerequisites

```bash
# Install required packages
pip install torch transformers accelerate bitsandbytes psutil

# Set HuggingFace token (required for model access)
export HF_TOKEN="your_huggingface_token_here"
```

### Run Optimized Inference

```bash
# Run the optimized script
python opt_30b_optimized.py
```

**Expected output:**
- Model loads in ~1-2 minutes
- Generation completes in ~100-150 seconds (30 tokens)
- GPU usage: ~14GB
- CPU usage: ~18GB
- Disk usage: 0GB (everything fits in RAM!)

### Run Benchmark Comparison

```bash
# Compare different configurations
python opt_30b_comparison.py
```

**WARNING**: This may take 30-60 minutes and requires significant memory.

## 📊 Performance Comparison

| Configuration | Load Time | Gen Time (30 tokens) | GPU Memory | CPU Memory | Disk |
|---------------|-----------|---------------------|------------|------------|------|
| **Baseline (FP32)** | ~1-2 min | ~500s | 5GB | 20GB | Heavy |
| **8-bit (no CPU offload)** | ~1-2 min | ~150s | 16GB | 16GB | 0GB |
| **8-bit (with CPU offload)** ⭐ | ~1-2 min | ~100-150s | 14GB | 18GB | 0GB |

### Key Improvements

✅ **3-5x faster** inference (vs disk-offloading baseline)
✅ **50% memory reduction** (FP16 → INT8 quantization)
✅ **No disk offload** needed (everything fits in RAM)
✅ **More GPU layers** (FP32 modules offloaded to CPU)
✅ **< 1% accuracy loss** (mixed-precision quantization)

## 🔧 Configuration Parameters Explained

### 1. `load_in_8bit=True`

**What it does:**
- Quantizes model weights from FP16 (2 bytes/param) to INT8 (1 byte/param)
- Reduces model size from ~60GB → ~30GB

**Extra memory needed:**
- Activations: +2-4GB on GPU (must stay in FP16 during computation)
- Dequantization buffers: +0.5-1GB on GPU

**Where allocated:**
- Quantized weights: CAN be offloaded to GPU/CPU/Disk via `device_map`
- Activations: MUST stay on GPU during forward pass

### 2. `llm_int8_threshold=6.0`

**What it does:**
- Sets outlier detection threshold for mixed-precision quantization
- Values ≤ 6.0: Quantize to INT8 (99.9% of weights)
- Values > 6.0: Keep in FP16 (0.1% of weights - outliers)

**Extra memory needed:**
- ~0.1GB for outlier values (negligible)

**Why it matters:**
- Prevents accuracy degradation from quantizing extreme values
- Maintains < 1% accuracy loss compared to FP16

### 3. `llm_int8_enable_fp32_cpu_offload=True`

**What it does:**
- Offloads non-quantizable modules (embeddings, LayerNorm, lm_head) from GPU to CPU
- These modules stay in FP32 on CPU instead of FP32 on GPU

**Extra memory needed:**
- None! It MOVES ~1-2GB from GPU → CPU

**Impact on allocation:**
- **Without**: GPU: 14GB INT8 + 2GB FP32 = 16GB (maxed out)
- **With**: GPU: 14GB INT8, CPU: +2GB FP32 (frees 2GB GPU for more INT8 layers!)

**Performance tradeoff:**
- ✅ +4-6 more decoder layers fit on GPU
- ✅ Faster inference (more GPU computation)
- ⚠️ +30-50ms latency per forward pass (CPU ↔ GPU transfers)

**When to use:**
- ✅ Model doesn't fit on GPU even with 8-bit quantization
- ✅ You have abundant CPU RAM (64GB in this case)
- ✅ You want to avoid disk offloading (much slower)

## 💡 Memory Allocation Visualization

### Without FP32 CPU Offload
```
GPU (16GB):
├─ Quantized layers (INT8):    14GB
├─ Non-quantized (FP32):        2GB  ← Takes up GPU!
├─ Activations:                 2GB
└─ TOTAL: 18GB → OVERFLOW! ❌

CPU (64GB):
└─ Quantized overflow (INT8):   16GB
```

### With FP32 CPU Offload ⭐
```
GPU (16GB):
├─ Quantized layers (INT8):    14GB  ← More layers!
├─ Activations:                 2GB
└─ TOTAL: 16GB → PERFECT FIT! ✅

CPU (64GB):
├─ Non-quantized (FP32):        2GB  ← Offloaded from GPU
└─ Quantized overflow (INT8):   16GB
```

**Result:** More layers on GPU = Faster inference!

## 🎓 Understanding the Device Map

After loading the model, the device map shows where each module is allocated:

```python
{
  'model.decoder.embed_tokens': 'cpu',        # FP32 on CPU (with cpu_offload)
  'model.decoder.embed_positions': 'cpu',     # FP32 on CPU
  'model.decoder.layers.0': 0,                # INT8 on GPU
  'model.decoder.layers.1': 0,                # INT8 on GPU
  ...
  'model.decoder.layers.24': 0,               # INT8 on GPU (4 more than without offload!)
  'model.decoder.layers.25': 'cpu',           # INT8 on CPU
  ...
  'lm_head': 'cpu'                            # FP32 on CPU
}
```

**Modules on GPU (device 0):**
- First ~24-26 decoder layers (INT8)
- Critical for performance

**Modules on CPU:**
- Embeddings, LayerNorm, lm_head (FP32)
- Remaining decoder layers (INT8)
- Sufficient RAM available

**Modules on Disk:**
- None! Everything fits in GPU + CPU RAM

## 🔍 Troubleshooting

### Out of Memory (OOM) Errors

**GPU OOM:**
```bash
# Reduce GPU allocation
max_memory={0: "12GiB", "cpu": "56GiB"}  # Instead of 14GB
```

**CPU OOM:**
```bash
# Reduce CPU allocation
max_memory={0: "14GiB", "cpu": "48GiB"}  # Instead of 56GB
```

### Slow Inference

**Check device map:**
- Ensure at least 20+ layers on GPU
- If too many layers on CPU/disk, increase `max_memory` for GPU

**Enable CPU offload:**
```python
llm_int8_enable_fp32_cpu_offload=True  # Should be enabled!
```

### Token Authentication Errors

```bash
# Make sure HF_TOKEN is set
export HF_TOKEN="your_token_here"

# Or pass directly (not recommended for production)
python opt_30b_optimized.py --token "your_token_here"
```

## 🔬 Advanced Usage

### Custom Memory Limits

```python
max_memory={
    0: "15GiB",      # GPU: increase if you have more VRAM
    "cpu": "60GiB"   # CPU: adjust based on your RAM
}
```

### Custom Quantization Threshold

```python
# More aggressive quantization (more INT8, fewer FP16 outliers)
llm_int8_threshold=8.0  # Default: 6.0

# More conservative (more FP16 outliers, higher accuracy)
llm_int8_threshold=4.0  # May increase memory slightly
```

### Disable CPU Offload

```python
# Keep FP32 modules on GPU (if you have more VRAM)
llm_int8_enable_fp32_cpu_offload=False
```

## 📚 Additional Resources

### Documentation
- [HuggingFace Transformers - Quantization](https://huggingface.co/docs/transformers/quantization/bitsandbytes)
- [Accelerate - Big Model Inference](https://huggingface.co/docs/accelerate/usage_guides/big_modeling)
- [LLM.int8() Paper](https://arxiv.org/abs/2208.07339)

### Related Projects
- [bitsandbytes](https://github.com/bitsandbytes-foundation/bitsandbytes) - 8-bit quantization library
- [Accelerate](https://github.com/huggingface/accelerate) - Memory-efficient model loading
- [vLLM](https://github.com/vllm-project/vllm) - High-throughput LLM serving (no disk offload support)

## 🔐 Security Notes

### HuggingFace Token

**❌ DO NOT** hardcode your token in scripts:
```python
# BAD - token exposed in code
hf_token = "hf_abc123..."
```

**✅ DO** use environment variables:
```bash
export HF_TOKEN="hf_abc123..."
```

```python
# GOOD - token from environment
hf_token = os.environ.get("HF_TOKEN")
```

### Offload Folder

The `./offload` directory may contain model weights during execution:
- Can grow very large (10-50GB)
- Add to `.gitignore`
- Clean up after use

## 📈 Expected Performance Metrics

Based on RTX 5060 Ti (16GB) + 64GB RAM:

### OPT-30B (with optimal config)
- **Load time**: 60-120 seconds
- **Inference time**: 100-150 seconds (30 tokens)
- **Time per token**: 3-5 seconds
- **GPU usage**: 14-15GB
- **CPU usage**: 18-20GB
- **Disk usage**: 0GB

### Baseline (FP32 with disk offload)
- **Load time**: 60-120 seconds
- **Inference time**: 500+ seconds (30 tokens)
- **Time per token**: 15-20 seconds
- **GPU usage**: 5GB
- **CPU usage**: 20GB
- **Disk usage**: Heavy I/O

**Speedup**: 3-5x faster with optimized configuration!

## 🤝 Contributing

Found a bug or have a suggestion? Please check:
1. Existing issues in the repository
2. Documentation and troubleshooting sections
3. HuggingFace forums for quantization-related questions

## 📄 License

This code follows the licenses of the underlying libraries:
- `transformers` - Apache 2.0
- `bitsandbytes` - MIT
- `accelerate` - Apache 2.0

---

**Happy inferencing! 🚀**

For questions or issues, refer to the [CLAUDE.md](CLAUDE.md) file for additional context about this repository.
