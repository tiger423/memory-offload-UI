# -*- coding: utf-8 -*-
"""
Memory monitoring utilities for LLM inference
Provides functions to track GPU, CPU, and disk memory usage
"""

import torch
import psutil
import os
from typing import Dict, List, Tuple
from collections import defaultdict


def get_gpu_memory_info() -> Dict[str, float]:
    """
    Get current GPU memory usage

    Returns:
        dict: GPU memory info in GB
            - allocated: Currently allocated memory
            - reserved: Reserved by PyTorch
            - free: Available memory
            - total: Total GPU memory
    """
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


def get_cpu_memory_info() -> Dict[str, float]:
    """
    Get current CPU/RAM memory usage

    Returns:
        dict: CPU memory info in GB
            - used: Currently used memory
            - available: Available memory
            - total: Total system memory
            - percent: Usage percentage
    """
    mem = psutil.virtual_memory()

    return {
        "used": round(mem.used / 1e9, 2),
        "available": round(mem.available / 1e9, 2),
        "total": round(mem.total / 1e9, 2),
        "percent": round(mem.percent, 1)
    }


def get_disk_usage(path: str = ".") -> Dict[str, float]:
    """
    Get disk usage for offload folder

    Args:
        path: Path to check (default: current directory)

    Returns:
        dict: Disk usage info in GB
    """
    if not os.path.exists(path):
        return {"error": f"Path {path} does not exist"}

    usage = psutil.disk_usage(path)

    return {
        "used": round(usage.used / 1e9, 2),
        "free": round(usage.free / 1e9, 2),
        "total": round(usage.total / 1e9, 2),
        "percent": round(usage.percent, 1)
    }


def analyze_device_map(device_map: Dict[str, any]) -> Dict[str, any]:
    """
    Analyze model's device map to understand layer distribution

    Args:
        device_map: Model's hf_device_map

    Returns:
        dict: Analysis with layer counts and module types per device
    """
    device_counts = defaultdict(int)
    module_types = defaultdict(lambda: defaultdict(int))

    for module_name, device in device_map.items():
        device_counts[str(device)] += 1

        # Categorize module types
        if 'embed' in module_name:
            module_type = 'embedding'
        elif 'norm' in module_name:
            module_type = 'layernorm'
        elif 'lm_head' in module_name:
            module_type = 'lm_head'
        elif 'layers' in module_name:
            module_type = 'decoder_layer'
        elif 'attention' in module_name:
            module_type = 'attention'
        else:
            module_type = 'other'

        module_types[str(device)][module_type] += 1

    return {
        "device_counts": dict(device_counts),
        "module_types": {k: dict(v) for k, v in module_types.items()}
    }


def print_memory_summary(gpu_info: Dict, cpu_info: Dict, title: str = "Memory Status"):
    """
    Print formatted memory summary

    Args:
        gpu_info: GPU memory info from get_gpu_memory_info()
        cpu_info: CPU memory info from get_cpu_memory_info()
        title: Title for the summary
    """
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print(f"{'='*60}")

    if "error" not in gpu_info:
        print(f"\n🎮 GPU Memory (NVIDIA RTX 5060 Ti):")
        print(f"  ├─ Allocated:  {gpu_info['allocated']:>6.2f} GB")
        print(f"  ├─ Reserved:   {gpu_info['reserved']:>6.2f} GB")
        print(f"  ├─ Free:       {gpu_info['free']:>6.2f} GB")
        print(f"  └─ Total:      {gpu_info['total']:>6.2f} GB")
    else:
        print(f"\n🎮 GPU Memory: {gpu_info['error']}")

    print(f"\n💾 CPU Memory (System RAM):")
    print(f"  ├─ Used:       {cpu_info['used']:>6.2f} GB ({cpu_info['percent']}%)")
    print(f"  ├─ Available:  {cpu_info['available']:>6.2f} GB")
    print(f"  └─ Total:      {cpu_info['total']:>6.2f} GB")

    print(f"{'='*60}\n")


def print_device_map_summary(device_map: Dict[str, any], model_name: str = "Model"):
    """
    Print formatted device map summary

    Args:
        device_map: Model's hf_device_map
        model_name: Name of the model
    """
    analysis = analyze_device_map(device_map)

    print(f"\n{'='*60}")
    print(f"Device Map Summary - {model_name}".center(60))
    print(f"{'='*60}")

    print(f"\n📍 Layer Distribution:")
    for device, count in sorted(analysis['device_counts'].items()):
        device_name = "GPU" if device == "0" else device.upper()
        print(f"  {device_name:>8}: {count:>3} modules")

    print(f"\n📦 Module Types by Device:")
    for device, types in sorted(analysis['module_types'].items()):
        device_name = "GPU" if device == "0" else device.upper()
        print(f"\n  {device_name}:")
        for module_type, count in sorted(types.items()):
            print(f"    ├─ {module_type:>15}: {count:>3} modules")

    print(f"{'='*60}\n")


def estimate_model_memory(num_parameters: float, dtype: str = "float32") -> float:
    """
    Estimate model memory requirements

    Args:
        num_parameters: Number of parameters in billions
        dtype: Data type (float32, float16, int8)

    Returns:
        float: Estimated memory in GB
    """
    bytes_per_param = {
        "float32": 4,
        "float16": 2,
        "bfloat16": 2,
        "int8": 1,
        "int4": 0.5
    }

    if dtype not in bytes_per_param:
        raise ValueError(f"Unknown dtype: {dtype}")

    return num_parameters * bytes_per_param[dtype]


def print_quantization_info(config):
    """
    Print information about quantization configuration

    Args:
        config: BitsAndBytesConfig object
    """
    print(f"\n{'='*60}")
    print(f"Quantization Configuration".center(60))
    print(f"{'='*60}")

    if hasattr(config, 'load_in_8bit') and config.load_in_8bit:
        print(f"\n✅ 8-bit Quantization Enabled")
        print(f"  ├─ Method: LLM.int8() (mixed-precision)")
        print(f"  ├─ Memory reduction: ~50% (FP16 → INT8)")
        print(f"  └─ Accuracy loss: <1%")

        if hasattr(config, 'llm_int8_threshold'):
            threshold = config.llm_int8_threshold
            print(f"\n🎯 Outlier Threshold: {threshold}")
            print(f"  ├─ Values ≤ {threshold}: Quantized to INT8 (99.9%)")
            print(f"  ├─ Values > {threshold}: Keep in FP16 (0.1%)")
            print(f"  └─ Extra memory: ~0.1GB (negligible)")

        if hasattr(config, 'llm_int8_enable_fp32_cpu_offload') and config.llm_int8_enable_fp32_cpu_offload:
            print(f"\n💾 FP32 CPU Offload Enabled")
            print(f"  ├─ Non-quantizable modules → CPU")
            print(f"  │  ├─ Embeddings (embed_tokens, embed_positions)")
            print(f"  │  ├─ LayerNorm (layer_norm, final_layer_norm)")
            print(f"  │  └─ lm_head (output projection)")
            print(f"  ├─ GPU memory freed: ~1-2GB")
            print(f"  └─ Latency overhead: ~30-50ms per forward pass")
        else:
            print(f"\n💾 FP32 CPU Offload Disabled")
            print(f"  └─ Non-quantizable modules stay on GPU (~1-2GB)")

    elif hasattr(config, 'load_in_4bit') and config.load_in_4bit:
        print(f"\n✅ 4-bit Quantization Enabled")
        print(f"  ├─ Memory reduction: ~75% (FP16 → INT4)")
        print(f"  └─ Accuracy loss: ~1-3%")

    else:
        print(f"\n❌ No Quantization")
        print(f"  └─ Using full precision (FP32 or FP16)")

    print(f"{'='*60}\n")


def monitor_memory_during_inference(func):
    """
    Decorator to monitor memory usage during inference

    Args:
        func: Function to monitor

    Returns:
        Wrapped function with memory monitoring
    """
    def wrapper(*args, **kwargs):
        print(f"\n📊 Starting memory monitoring for: {func.__name__}")

        # Before inference
        gpu_before = get_gpu_memory_info()
        cpu_before = get_cpu_memory_info()

        print(f"\n⏳ Before inference:")
        print(f"  GPU: {gpu_before['allocated']:.2f} GB allocated")
        print(f"  CPU: {cpu_before['used']:.2f} GB used")

        # Run inference
        result = func(*args, **kwargs)

        # After inference
        gpu_after = get_gpu_memory_info()
        cpu_after = get_cpu_memory_info()

        print(f"\n✅ After inference:")
        print(f"  GPU: {gpu_after['allocated']:.2f} GB allocated (+{gpu_after['allocated'] - gpu_before['allocated']:.2f} GB)")
        print(f"  CPU: {cpu_after['used']:.2f} GB used (+{cpu_after['used'] - cpu_before['used']:.2f} GB)")

        return result

    return wrapper
