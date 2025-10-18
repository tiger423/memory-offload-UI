# -*- coding: utf-8 -*-
"""
Backend Configuration
Centralized configuration for all backend services
"""

import os
from typing import Dict, List

# =============================================================================
# Model Configurations
# =============================================================================

MODEL_REGISTRY = {
    'opt-30b': {
        'id': 'opt-30b',
        'name': 'OPT-30B (Meta)',
        'hf_name': 'facebook/opt-30b',
        'size_gb': 60,
        'size_gb_int8': 30,
        'size_gb_int4': 15,
        'num_params': 30,
        'min_gpu_memory': 16,
        'min_cpu_memory': 32,
        'recommended_gpu': 14,
        'recommended_cpu': 56,
        'supported_tasks': ['inference'],
        'quantization_support': ['8-bit', '4-bit', 'none'],
        'architecture': 'opt',
        'num_layers': 48
    },
    'llama2-7b': {
        'id': 'llama2-7b',
        'name': 'LLaMA 2 7B',
        'hf_name': 'meta-llama/Llama-2-7b-hf',
        'size_gb': 14,
        'size_gb_int8': 7,
        'size_gb_int4': 3.5,
        'num_params': 7,
        'min_gpu_memory': 8,
        'min_cpu_memory': 16,
        'recommended_gpu': 6,
        'recommended_cpu': 12,
        'supported_tasks': ['inference', 'fine-tuning'],
        'quantization_support': ['8-bit', '4-bit', 'none'],
        'architecture': 'llama',
        'num_layers': 32
    },
    'llama2-13b': {
        'id': 'llama2-13b',
        'name': 'LLaMA 2 13B',
        'hf_name': 'meta-llama/Llama-2-13b-hf',
        'size_gb': 26,
        'size_gb_int8': 13,
        'size_gb_int4': 6.5,
        'num_params': 13,
        'min_gpu_memory': 16,
        'min_cpu_memory': 32,
        'recommended_gpu': 12,
        'recommended_cpu': 24,
        'supported_tasks': ['inference', 'fine-tuning'],
        'quantization_support': ['8-bit', '4-bit', 'none'],
        'architecture': 'llama',
        'num_layers': 40
    },
    'falcon-7b': {
        'id': 'falcon-7b',
        'name': 'Falcon 7B',
        'hf_name': 'tiiuae/falcon-7b',
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
        'architecture': 'falcon',
        'num_layers': 32
    }
}

# =============================================================================
# Default Settings
# =============================================================================

DEFAULT_INFERENCE_CONFIG = {
    'quantization': '8-bit',
    'enable_fp32_cpu_offload': True,
    'max_length': 50,
    'min_length': 10,
    'temperature': 0.7,
    'top_p': 0.9,
    'top_k': 50,
    'do_sample': True,
    'num_return_sequences': 1,
    'gpu_memory': '14GiB',
    'cpu_memory': '56GiB',
    'offload_folder': './offload'
}

# =============================================================================
# Environment Configuration
# =============================================================================

class BackendConfig:
    """Central configuration class for backend services"""

    def __init__(self):
        self.hf_token = os.environ.get('HF_TOKEN')
        self.cache_dir = os.environ.get('HF_CACHE_DIR', './model_cache')
        self.offload_dir = os.environ.get('OFFLOAD_DIR', './offload')
        self.log_level = os.environ.get('LOG_LEVEL', 'INFO')
        self.cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '0')

    def get_model_config(self, model_id: str) -> Dict:
        """Get configuration for a specific model"""
        if model_id not in MODEL_REGISTRY:
            raise ValueError(f"Model {model_id} not found in registry")
        return MODEL_REGISTRY[model_id]

    def get_all_models(self) -> List[Dict]:
        """Get list of all available models"""
        return list(MODEL_REGISTRY.values())

    def validate_memory_config(self, gpu_memory: str, cpu_memory: str, model_id: str) -> bool:
        """Validate memory configuration for a model"""
        model_config = self.get_model_config(model_id)

        # Parse memory strings (e.g., "14GiB" -> 14)
        gpu_gb = int(gpu_memory.replace('GiB', '').replace('GB', ''))
        cpu_gb = int(cpu_memory.replace('GiB', '').replace('GB', ''))

        # Check minimums
        if gpu_gb < model_config['min_gpu_memory']:
            return False
        if cpu_gb < model_config['min_cpu_memory']:
            return False

        return True

    def get_recommended_config(self, model_id: str, quantization: str = '8-bit') -> Dict:
        """Get recommended configuration for a model"""
        model_config = self.get_model_config(model_id)

        config = DEFAULT_INFERENCE_CONFIG.copy()
        config['quantization'] = quantization
        config['gpu_memory'] = f"{model_config['recommended_gpu']}GiB"
        config['cpu_memory'] = f"{model_config['recommended_cpu']}GiB"

        return config


# Global config instance
config = BackendConfig()


# =============================================================================
# Utility Functions
# =============================================================================

def get_quantization_config(quantization_type: str, enable_fp32_cpu_offload: bool = True):
    """
    Get BitsAndBytesConfig for specified quantization type

    Args:
        quantization_type: '8-bit', '4-bit', or 'none'
        enable_fp32_cpu_offload: Enable FP32 CPU offload

    Returns:
        BitsAndBytesConfig or None
    """
    from transformers import BitsAndBytesConfig
    import torch

    if quantization_type == '8-bit':
        return BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0,
            llm_int8_enable_fp32_cpu_offload=enable_fp32_cpu_offload
        )
    elif quantization_type == '4-bit':
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
    else:  # 'none'
        return None


def parse_memory_string(memory_str: str) -> int:
    """
    Parse memory string to GB integer

    Args:
        memory_str: Memory string like "14GiB" or "56GB"

    Returns:
        Integer GB value
    """
    return int(memory_str.replace('GiB', '').replace('GB', '').replace('G', '').strip())


def format_memory_string(gb: int) -> str:
    """
    Format GB integer to memory string

    Args:
        gb: Memory in GB

    Returns:
        Formatted string like "14GiB"
    """
    return f"{gb}GiB"
