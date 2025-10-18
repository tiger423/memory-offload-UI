#!/usr/bin/env python3
"""Test backend configuration module"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.config import config, MODEL_REGISTRY, get_quantization_config

def test_model_registry():
    """Test model registry is properly configured"""
    print("Testing Model Registry...")

    # Check required models exist
    required_models = ['opt-30b', 'llama2-7b', 'llama2-13b', 'falcon-7b']
    for model_id in required_models:
        assert model_id in MODEL_REGISTRY, f"Model {model_id} not found"
        model = MODEL_REGISTRY[model_id]

        # Verify required fields
        assert 'id' in model
        assert 'name' in model
        assert 'hf_name' in model
        assert 'size_gb' in model
        assert 'min_gpu_memory' in model
        assert 'min_cpu_memory' in model

    print(f"✅ {len(MODEL_REGISTRY)} models configured")

def test_backend_config():
    """Test backend configuration class"""
    print("\nTesting Backend Config...")

    # Test getting all models
    models = config.get_all_models()
    assert len(models) > 0, "No models found"
    print(f"✅ Found {len(models)} models")

    # Test getting specific model
    model = config.get_model_config('llama2-7b')
    assert model['id'] == 'llama2-7b'
    print("✅ Model retrieval works")

    # Test invalid model
    try:
        config.get_model_config('invalid-model')
        assert False, "Should raise ValueError"
    except ValueError:
        print("✅ Invalid model raises error")

def test_quantization_config():
    """Test quantization configuration"""
    print("\nTesting Quantization Config...")

    # Test 8-bit config
    config_8bit = get_quantization_config('8-bit', True)
    assert config_8bit is not None
    print("✅ 8-bit config created")

    # Test 4-bit config
    config_4bit = get_quantization_config('4-bit', False)
    assert config_4bit is not None
    print("✅ 4-bit config created")

    # Test none config
    config_none = get_quantization_config('none', False)
    assert config_none is None
    print("✅ None config returns None")

if __name__ == '__main__':
    print("="*60)
    print("Backend Configuration Tests")
    print("="*60)

    try:
        test_model_registry()
        test_backend_config()
        test_quantization_config()

        print("\n" + "="*60)
        print("✅ ALL BACKEND CONFIG TESTS PASSED")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
