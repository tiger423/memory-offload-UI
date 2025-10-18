# -*- coding: utf-8 -*-
"""
Optimized OPT-30B Inference Script
Configured for RTX 5060 Ti (16GB) + 64GB RAM + 2TB SSD

Features:
- 8-bit quantization (LLM.int8())
- FP32 CPU offload for non-quantizable modules
- Real-time memory monitoring
- Device map visualization
- Performance metrics

Expected Performance:
- GPU usage: ~14GB
- CPU usage: ~18GB
- Disk usage: 0GB (everything fits in RAM!)
- Inference time: ~100-150s for 30 tokens (vs 500s without optimization)
"""

import os
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from memory_utils import (
    get_gpu_memory_info,
    get_cpu_memory_info,
    print_memory_summary,
    print_device_map_summary,
    print_quantization_info,
    estimate_model_memory
)


def main():
    """Main inference function with optimized configuration"""

    # ============================================================
    # Configuration
    # ============================================================

    # Get HuggingFace token from environment variable (secure!)
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("⚠️  Warning: HF_TOKEN not found in environment variables.")
        print("   Set it using: export HF_TOKEN='your_token_here'")
        print("   Attempting to proceed without authentication...\n")

    model_name = 'facebook/opt-30b'
    offload_folder = './offload'

    # Hardware specifications
    hardware_config = {
        "gpu": "NVIDIA RTX 5060 Ti",
        "gpu_memory": "16GB",
        "cpu_memory": "64GB",
        "disk": "2TB SSD"
    }

    print(f"\n{'='*60}")
    print(f"OPT-30B Optimized Inference".center(60))
    print(f"{'='*60}")
    print(f"\n🖥️  Hardware Configuration:")
    print(f"  ├─ GPU: {hardware_config['gpu']} ({hardware_config['gpu_memory']})")
    print(f"  ├─ RAM: {hardware_config['cpu_memory']}")
    print(f"  └─ SSD: {hardware_config['disk']}")
    print(f"\n📦 Model: {model_name}")
    print(f"{'='*60}\n")

    # ============================================================
    # Step 1: Check Initial Memory
    # ============================================================

    print("\n🔍 Step 1: Checking initial memory status...")
    gpu_initial = get_gpu_memory_info()
    cpu_initial = get_cpu_memory_info()
    print_memory_summary(gpu_initial, cpu_initial, "Initial Memory Status")

    # ============================================================
    # Step 2: Configure Quantization
    # ============================================================

    print("\n⚙️  Step 2: Configuring 8-bit quantization...")

    quantization_config = BitsAndBytesConfig(
        load_in_8bit=True,                       # Enable 8-bit quantization
        llm_int8_threshold=6.0,                  # Outlier detection threshold
        llm_int8_enable_fp32_cpu_offload=True   # Offload FP32 modules to CPU
    )

    print_quantization_info(quantization_config)

    # Memory estimation
    print("\n📊 Memory Estimation:")
    print(f"  OPT-30B without quantization:")
    print(f"    ├─ FP32: {estimate_model_memory(30, 'float32'):.1f} GB")
    print(f"    └─ FP16: {estimate_model_memory(30, 'float16'):.1f} GB")
    print(f"  OPT-30B with 8-bit quantization:")
    print(f"    ├─ INT8: {estimate_model_memory(30, 'int8'):.1f} GB")
    print(f"    └─ Savings: ~{estimate_model_memory(30, 'float16') - estimate_model_memory(30, 'int8'):.1f} GB (50%)")

    # ============================================================
    # Step 3: Load Model with Optimized Configuration
    # ============================================================

    print(f"\n{'='*60}")
    print("\n🚀 Step 3: Loading model with optimized configuration...")
    print("   This may take 1-2 minutes...\n")

    load_start = time.time()

    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",                    # Automatic layer distribution
            offload_folder=offload_folder,        # SSD fallback (likely unused)
            max_memory={
                0: "14GiB",      # RTX 5060 Ti: 14GB for model, 2GB for activations
                "cpu": "56GiB"   # System RAM: 56GB for model, 8GB for OS
            },
            quantization_config=quantization_config,
            torch_dtype=torch.float16,            # Base dtype for non-quantized ops
            low_cpu_mem_usage=True,               # Efficient loading
            token=hf_token
        )

        load_time = time.time() - load_start

        print(f"✅ Model loaded successfully in {load_time:.1f} seconds")
        print(f"   ({load_time/60:.1f} minutes)")

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return

    # ============================================================
    # Step 4: Analyze Memory After Loading
    # ============================================================

    print(f"\n{'='*60}")
    print("\n📊 Step 4: Analyzing memory allocation...")

    gpu_loaded = get_gpu_memory_info()
    cpu_loaded = get_cpu_memory_info()
    print_memory_summary(gpu_loaded, cpu_loaded, "Memory After Model Loading")

    # Calculate actual memory usage
    print(f"\n📈 Memory Usage Increase:")
    print(f"  GPU: +{gpu_loaded['allocated'] - gpu_initial['allocated']:.2f} GB")
    print(f"  CPU: +{cpu_loaded['used'] - cpu_initial['used']:.2f} GB")

    # Model size
    model_size = model.get_memory_footprint() / 1e9
    print(f"\n💾 Model Footprint: {model_size:.2f} GB")

    # ============================================================
    # Step 5: Analyze Device Map
    # ============================================================

    print(f"\n{'='*60}")
    print("\n🗺️  Step 5: Analyzing device map...")

    print_device_map_summary(model.hf_device_map, "OPT-30B")

    # Detailed device map (first 10 and last 10 modules)
    print(f"\n📋 Detailed Device Map (sample):")
    device_map_items = list(model.hf_device_map.items())

    print(f"\n  First 10 modules:")
    for module_name, device in device_map_items[:10]:
        device_display = "GPU" if device == 0 else str(device).upper()
        print(f"    {module_name:.<50} {device_display:>8}")

    if len(device_map_items) > 20:
        print(f"  ...")
        print(f"\n  Last 10 modules:")
        for module_name, device in device_map_items[-10:]:
            device_display = "GPU" if device == 0 else str(device).upper()
            print(f"    {module_name:.<50} {device_display:>8}")

    # ============================================================
    # Step 6: Load Tokenizer
    # ============================================================

    print(f"\n{'='*60}")
    print("\n🔤 Step 6: Loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        use_fast=False,
        token=hf_token
    )

    print("✅ Tokenizer loaded successfully")

    # ============================================================
    # Step 7: Run Inference
    # ============================================================

    print(f"\n{'='*60}")
    print("\n🎯 Step 7: Running inference...")

    # Test prompt
    prompt = "Hugging Face is pushing the convention that a unicorn with two horns becomes a llama."
    print(f"\n📝 Prompt: \"{prompt}\"")

    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs["input_ids"].to(0)  # Move to GPU

    print(f"   Input tokens: {input_ids.shape[1]}")

    # Generation parameters
    generation_config = {
        "min_length": 30,
        "max_length": 50,
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.9
    }

    print(f"\n⚙️  Generation config:")
    for key, value in generation_config.items():
        print(f"    {key}: {value}")

    # Check memory before generation
    gpu_before_gen = get_gpu_memory_info()
    cpu_before_gen = get_cpu_memory_info()

    print(f"\n⏳ Generating... (this may take 1-2 minutes)")
    gen_start = time.time()

    try:
        output = model.generate(
            input_ids,
            **generation_config
        )
        gen_time = time.time() - gen_start

        print(f"✅ Generation completed in {gen_time:.1f} seconds")

    except Exception as e:
        print(f"❌ Error during generation: {e}")
        return

    # Decode output
    generated_text = tokenizer.decode(output[0].tolist())
    output_tokens = output.shape[1]

    print(f"\n{'='*60}")
    print(f"Generated Output".center(60))
    print(f"{'='*60}")
    print(f"\n{generated_text}\n")
    print(f"{'='*60}")

    # ============================================================
    # Step 8: Performance Metrics
    # ============================================================

    print(f"\n{'='*60}")
    print(f"Performance Metrics".center(60))
    print(f"{'='*60}")

    tokens_generated = output_tokens - input_ids.shape[1]
    time_per_token = gen_time / tokens_generated if tokens_generated > 0 else 0

    print(f"\n⏱️  Timing:")
    print(f"  ├─ Model loading: {load_time:.1f}s ({load_time/60:.1f} min)")
    print(f"  ├─ Generation: {gen_time:.1f}s ({gen_time/60:.1f} min)")
    print(f"  └─ Total: {load_time + gen_time:.1f}s ({(load_time + gen_time)/60:.1f} min)")

    print(f"\n📊 Token Statistics:")
    print(f"  ├─ Input tokens: {input_ids.shape[1]}")
    print(f"  ├─ Generated tokens: {tokens_generated}")
    print(f"  ├─ Total output tokens: {output_tokens}")
    print(f"  └─ Time per token: {time_per_token:.2f}s")

    # Final memory check
    gpu_after_gen = get_gpu_memory_info()
    cpu_after_gen = get_cpu_memory_info()

    print(f"\n💾 Memory During Generation:")
    print(f"  GPU:")
    print(f"    ├─ Before: {gpu_before_gen['allocated']:.2f} GB")
    print(f"    ├─ After:  {gpu_after_gen['allocated']:.2f} GB")
    print(f"    └─ Peak:   {gpu_after_gen['reserved']:.2f} GB (reserved)")
    print(f"  CPU:")
    print(f"    ├─ Before: {cpu_before_gen['used']:.2f} GB")
    print(f"    └─ After:  {cpu_after_gen['used']:.2f} GB")

    # ============================================================
    # Step 9: Comparison with Baseline
    # ============================================================

    print(f"\n{'='*60}")
    print(f"Comparison with Baseline".center(60))
    print(f"{'='*60}")

    # Baseline from opt-d-1-4.py
    baseline_time = 501.0  # seconds from original script

    print(f"\n📈 Performance Improvement:")
    print(f"  Baseline (FP32 + disk offload):")
    print(f"    └─ Time: {baseline_time:.1f}s ({baseline_time/60:.1f} min)")
    print(f"  Optimized (INT8 + CPU offload):")
    print(f"    └─ Time: {gen_time:.1f}s ({gen_time/60:.1f} min)")
    print(f"  Speedup: {baseline_time / gen_time:.1f}x faster")

    print(f"\n💡 Key Optimizations:")
    print(f"  ✅ 8-bit quantization: ~50% memory reduction")
    print(f"  ✅ FP32 CPU offload: +2GB GPU freed for more layers")
    print(f"  ✅ No disk offload needed: Everything fits in RAM!")
    print(f"  ✅ More layers on GPU: Faster inference")

    print(f"\n{'='*60}")
    print(f"✨ Inference Complete!".center(60))
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
