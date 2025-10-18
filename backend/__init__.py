# -*- coding: utf-8 -*-
"""
Backend Module for LLM Inference Web UI
Provides unified interface for model loading, inference, and fine-tuning
"""

__version__ = '1.0.0'
__author__ = 'LLM Inference Backend'

from backend.config import config, MODEL_REGISTRY, DEFAULT_INFERENCE_CONFIG
from backend.inference_engine import InferenceEngine

__all__ = [
    'config',
    'MODEL_REGISTRY',
    'DEFAULT_INFERENCE_CONFIG',
    'InferenceEngine'
]
