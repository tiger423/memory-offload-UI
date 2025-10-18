# -*- coding: utf-8 -*-
"""
Unified Inference Engine
Handles model loading, inference, and memory management for web UI
"""

import os
import sys
import time
import json
import torch
from typing import Dict, Optional, Callable
from transformers import AutoModelForCausalLM, AutoTokenizer

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from memory_utils import (
    get_gpu_memory_info,
    get_cpu_memory_info,
    analyze_device_map
)
from backend.config import config, get_quantization_config


class InferenceEngine:
    """
    Unified inference engine for LLM models
    Supports streaming output and progress callbacks
    """

    def __init__(self, model_id: str, progress_callback: Optional[Callable] = None):
        """
        Initialize inference engine

        Args:
            model_id: Model identifier from MODEL_REGISTRY
            progress_callback: Optional callback for progress updates
        """
        self.model_id = model_id
        self.model_config = config.get_model_config(model_id)
        self.hf_model_name = self.model_config['hf_name']
        self.progress_callback = progress_callback or self._default_callback

        self.model = None
        self.tokenizer = None
        self.device_map = None
        self.load_time = 0
        self.metrics = {}

    def _default_callback(self, event: str, data: Dict):
        """Default callback that prints to stdout"""
        print(json.dumps({"type": event, "data": data}), flush=True)

    def _emit(self, event: str, data: Dict):
        """Emit event via callback"""
        try:
            self.progress_callback(event, data)
        except Exception as e:
            print(f"Error in callback: {e}", file=sys.stderr)

    def load_model(self, quantization: str = '8-bit',
                   enable_fp32_cpu_offload: bool = True,
                   gpu_memory: str = '14GiB',
                   cpu_memory: str = '56GiB',
                   offload_folder: str = './offload'):
        """
        Load model with specified configuration

        Args:
            quantization: '8-bit', '4-bit', or 'none'
            enable_fp32_cpu_offload: Enable FP32 CPU offload
            gpu_memory: GPU memory limit
            cpu_memory: CPU memory limit
            offload_folder: Folder for disk offloading

        Returns:
            True if successful, False otherwise
        """
        try:
            self._emit('status', {
                'status': 'loading',
                'message': f'Initializing {self.model_config["name"]}...'
            })
            self._emit('progress', {'percent': 0, 'message': 'Starting...'})

            # Check HF token
            if not config.hf_token:
                raise ValueError("HF_TOKEN not set in environment")

            # Get memory info before loading
            self._emit('memory', {
                'gpu': get_gpu_memory_info(),
                'cpu': get_cpu_memory_info()
            })

            # Configure quantization
            self._emit('progress', {'percent': 10, 'message': 'Configuring quantization...'})
            quantization_config = get_quantization_config(quantization, enable_fp32_cpu_offload)

            if quantization_config:
                self._emit('status', {
                    'status': 'loading',
                    'message': f'Using {quantization} quantization'
                })

            # Prepare model loading arguments
            self._emit('progress', {'percent': 20, 'message': 'Preparing to load model...'})

            model_kwargs = {
                "device_map": "auto",
                "offload_folder": offload_folder,
                "max_memory": {
                    0: gpu_memory,
                    "cpu": cpu_memory
                },
                "torch_dtype": torch.float16,
                "low_cpu_mem_usage": True,
                "token": config.hf_token
            }

            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config

            # Load model
            self._emit('status', {
                'status': 'loading',
                'message': f'Loading {self.hf_model_name}... (this may take 1-2 minutes)'
            })
            self._emit('progress', {'percent': 30, 'message': 'Loading model weights...'})

            load_start = time.time()

            self.model = AutoModelForCausalLM.from_pretrained(
                self.hf_model_name,
                **model_kwargs
            )

            self.load_time = time.time() - load_start

            self._emit('progress', {'percent': 70, 'message': f'Model loaded in {self.load_time:.1f}s'})
            self._emit('status', {
                'status': 'loading',
                'message': 'Model loaded successfully!'
            })

            # Get memory after loading
            gpu_mem = get_gpu_memory_info()
            cpu_mem = get_cpu_memory_info()

            self._emit('memory', {'gpu': gpu_mem, 'cpu': cpu_mem})

            # Analyze device map
            if hasattr(self.model, 'hf_device_map'):
                self.device_map = self.model.hf_device_map
                self._emit('device_map', self._serialize_device_map(self.device_map))

                # Analyze layer distribution
                analysis = analyze_device_map(self.device_map)
                gpu_layers = analysis['device_counts'].get('0', 0)
                cpu_layers = analysis['device_counts'].get('cpu', 0)
                disk_layers = analysis['device_counts'].get('disk', 0)

                self.metrics['gpu_layers'] = gpu_layers
                self.metrics['cpu_layers'] = cpu_layers
                self.metrics['disk_layers'] = disk_layers

                self._emit('status', {
                    'status': 'loading',
                    'message': f'GPU: {gpu_layers} layers, CPU: {cpu_layers} layers, Disk: {disk_layers} layers'
                })

            # Load tokenizer
            self._emit('progress', {'percent': 80, 'message': 'Loading tokenizer...'})

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.hf_model_name,
                use_fast=False,
                token=config.hf_token
            )

            self._emit('progress', {'percent': 90, 'message': 'Tokenizer loaded'})

            # Get final model size
            if hasattr(self.model, 'get_memory_footprint'):
                model_size_gb = self.model.get_memory_footprint() / 1e9
                self.metrics['model_size_gb'] = round(model_size_gb, 2)

            self._emit('progress', {'percent': 100, 'message': 'Ready for inference'})
            self._emit('status', {
                'status': 'ready',
                'message': f'Model ready! Loaded in {self.load_time:.1f}s'
            })

            return True

        except Exception as e:
            self._emit('error', {'error': str(e)})
            import traceback
            traceback.print_exc()
            return False

    def generate(self, prompt: str, max_length: int = 50,
                 temperature: float = 0.7, top_p: float = 0.9,
                 top_k: int = 50, do_sample: bool = True,
                 stream: bool = False) -> Dict:
        """
        Generate text from prompt

        Args:
            prompt: Input prompt
            max_length: Maximum generation length
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            do_sample: Enable sampling
            stream: Enable streaming output

        Returns:
            Dictionary with generated text and metrics
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            self._emit('status', {
                'status': 'generating',
                'message': 'Tokenizing input...'
            })

            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt")
            input_ids = inputs["input_ids"].to(0)  # Move to GPU
            input_length = input_ids.shape[1]

            self._emit('generation_start', {
                'input_length': input_length,
                'max_length': max_length
            })

            # Generate
            self._emit('status', {
                'status': 'generating',
                'message': f'Generating text... (up to {max_length} tokens)'
            })

            gen_start = time.time()

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

            self._emit('result', result)
            self._emit('status', {
                'status': 'completed',
                'message': f'Generated {tokens_generated} tokens in {gen_time:.1f}s'
            })

            return result

        except Exception as e:
            self._emit('error', {'error': str(e)})
            import traceback
            traceback.print_exc()
            raise

    def _serialize_device_map(self, device_map: Dict) -> Dict:
        """Convert device map to JSON-serializable format"""
        serializable = {}
        for key, value in device_map.items():
            if isinstance(value, int):
                serializable[key] = value
            else:
                serializable[key] = str(value)
        return serializable

    def unload_model(self):
        """Unload model and free memory"""
        if self.model:
            del self.model
            self.model = None

        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None

        torch.cuda.empty_cache()

        self._emit('status', {
            'status': 'unloaded',
            'message': 'Model unloaded and memory freed'
        })

    def get_model_info(self) -> Dict:
        """Get current model information"""
        return {
            'model_id': self.model_id,
            'model_config': self.model_config,
            'loaded': self.model is not None,
            'load_time': self.load_time,
            'metrics': self.metrics,
            'device_map': self._serialize_device_map(self.device_map) if self.device_map else None
        }
