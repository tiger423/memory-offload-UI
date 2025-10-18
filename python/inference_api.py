#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python API Wrapper for LLM Inference
Handles model loading and inference, communicating with Node.js via JSON
"""

import os
import sys
import json
import time
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Add parent directory to path to import memory_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from memory_utils import (
    get_gpu_memory_info,
    get_cpu_memory_info,
    analyze_device_map
)


def emit_json(message_type, data):
    """
    Emit JSON message to stdout for Node.js to parse

    Args:
        message_type: Type of message (status, progress, memory, etc.)
        data: Message data (dict)
    """
    message = {
        "type": message_type,
        "data": data
    }
    print(json.dumps(message), flush=True)


def emit_status(status, message=""):
    """Emit status update"""
    emit_json("status", {"status": status, "message": message})


def emit_progress(percent, message=""):
    """Emit progress update"""
    emit_json("progress", {"percent": percent, "message": message})


def emit_memory():
    """Emit memory status"""
    gpu_info = get_gpu_memory_info()
    cpu_info = get_cpu_memory_info()
    emit_json("memory", {"gpu": gpu_info, "cpu": cpu_info})


def emit_device_map(device_map):
    """Emit device map"""
    # Convert device map to serializable format
    serializable_map = {}
    for key, value in device_map.items():
        serializable_map[key] = int(value) if isinstance(value, int) else str(value)
    emit_json("device_map", serializable_map)


def emit_error(error):
    """Emit error message"""
    emit_json("error", {"error": str(error)})


def emit_result(text, prompt, metrics):
    """Emit final result"""
    emit_json("result", {
        "text": text,
        "prompt": prompt,
        "metrics": metrics
    })


def main():
    """Main inference function"""

    parser = argparse.ArgumentParser(description='LLM Inference API')
    parser.add_argument('--model', required=True, help='Model name (e.g., facebook/opt-30b)')
    parser.add_argument('--prompt', required=True, help='Input prompt')
    parser.add_argument('--quantization', default='8-bit', choices=['8-bit', '4-bit', 'none'])
    parser.add_argument('--enable-fp32-cpu-offload', action='store_true', help='Enable FP32 CPU offload')
    parser.add_argument('--max-length', type=int, default=50, help='Max generation length')
    parser.add_argument('--temperature', type=float, default=0.7, help='Temperature')
    parser.add_argument('--top-p', type=float, default=0.9, help='Top-p sampling')
    parser.add_argument('--gpu-memory', default='14GiB', help='GPU memory limit')
    parser.add_argument('--cpu-memory', default='56GiB', help='CPU memory limit')
    parser.add_argument('--session-id', required=True, help='Session ID for tracking')

    args = parser.parse_args()

    try:
        # Step 1: Initialize
        emit_status("loading", "Initializing inference session...")
        emit_progress(0, "Starting...")
        emit_memory()

        # Get HF token
        hf_token = os.environ.get('HF_TOKEN')
        if not hf_token:
            emit_error("HF_TOKEN environment variable not set")
            sys.exit(1)

        # Step 2: Configure quantization
        emit_status("loading", "Configuring quantization...")
        emit_progress(10, "Setting up quantization...")

        quantization_config = None
        if args.quantization == '8-bit':
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_enable_fp32_cpu_offload=args.enable_fp32_cpu_offload
            )
        elif args.quantization == '4-bit':
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4"
            )

        # Step 3: Load model
        emit_status("loading", f"Loading model {args.model}...")
        emit_progress(20, "This may take 1-2 minutes...")

        load_start = time.time()

        model_kwargs = {
            "device_map": "auto",
            "offload_folder": "./offload",
            "max_memory": {
                0: args.gpu_memory,
                "cpu": args.cpu_memory
            },
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True,
            "token": hf_token
        }

        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config

        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            **model_kwargs
        )

        load_time = time.time() - load_start

        emit_status("loading", "Model loaded successfully!")
        emit_progress(60, f"Loaded in {load_time:.1f}s")
        emit_memory()

        # Step 4: Emit device map
        if hasattr(model, 'hf_device_map'):
            emit_device_map(model.hf_device_map)

            # Analyze device distribution
            analysis = analyze_device_map(model.hf_device_map)
            gpu_modules = analysis['device_counts'].get('0', 0)
            cpu_modules = analysis['device_counts'].get('cpu', 0)
        else:
            gpu_modules = 0
            cpu_modules = 0

        # Step 5: Load tokenizer
        emit_status("loading", "Loading tokenizer...")
        emit_progress(70, "Loading tokenizer...")

        tokenizer = AutoTokenizer.from_pretrained(
            args.model,
            use_fast=False,
            token=hf_token
        )

        # Step 6: Tokenize input
        emit_status("loading", "Tokenizing input...")
        emit_progress(80, "Preparing input...")

        inputs = tokenizer(args.prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(0)  # Move to GPU
        input_length = input_ids.shape[1]

        # Step 7: Generate
        emit_status("generating", "Generating text...")
        emit_progress(90, "Running inference...")
        emit_json("generation_start", {"input_length": input_length})

        gen_start = time.time()

        output = model.generate(
            input_ids,
            max_length=args.max_length,
            temperature=args.temperature,
            top_p=args.top_p,
            do_sample=True
        )

        gen_time = time.time() - gen_start

        # Step 8: Decode output
        generated_text = tokenizer.decode(output[0].tolist())
        output_length = output.shape[1]
        tokens_generated = output_length - input_length

        # Step 9: Collect metrics
        gpu_memory = get_gpu_memory_info()
        cpu_memory = get_cpu_memory_info()

        metrics = {
            "loadTime": load_time,
            "genTime": gen_time,
            "totalTime": load_time + gen_time,
            "inputTokens": input_length,
            "outputTokens": output_length,
            "tokensGenerated": tokens_generated,
            "tokensPerSecond": tokens_generated / gen_time if gen_time > 0 else 0,
            "gpuMemoryUsed": gpu_memory.get('allocated', 0),
            "cpuMemoryUsed": cpu_memory.get('used', 0),
            "gpuLayers": gpu_modules,
            "cpuLayers": cpu_modules
        }

        # Step 10: Emit result
        emit_progress(100, "Complete!")
        emit_result(generated_text, args.prompt, metrics)
        emit_status("completed", f"Generated {tokens_generated} tokens in {gen_time:.1f}s")

        sys.exit(0)

    except Exception as e:
        emit_error(str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
