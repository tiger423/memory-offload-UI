#!/usr/bin/env python3
"""Test memory utilities"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from memory_utils import (
    get_gpu_memory_info,
    get_cpu_memory_info,
    get_disk_usage,
    analyze_device_map,
    estimate_model_memory
)

def test_gpu_memory():
    """Test GPU memory info"""
    print("Testing GPU Memory Info...")

    info = get_gpu_memory_info()

    if 'error' in info:
        print("⚠️  CUDA not available, skipping GPU test")
        return

    assert 'allocated' in info
    assert 'reserved' in info
    assert 'free' in info
    assert 'total' in info

    assert info['total'] > 0
    print(f"✅ GPU: {info['total']} GB total")

def test_cpu_memory():
    """Test CPU memory info"""
    print("\nTesting CPU Memory Info...")

    info = get_cpu_memory_info()

    assert 'used' in info
    assert 'available' in info
    assert 'total' in info
    assert 'percent' in info

    assert info['total'] > 0
    print(f"✅ CPU: {info['total']} GB total")

def test_disk_usage():
    """Test disk usage"""
    print("\nTesting Disk Usage...")

    info = get_disk_usage('.')

    assert 'used' in info
    assert 'free' in info
    assert 'total' in info

    assert info['total'] > 0
    print(f"✅ Disk: {info['total']} GB total")

def test_device_map_analysis():
    """Test device map analysis"""
    print("\nTesting Device Map Analysis...")

    # Mock device map
    device_map = {
        'model.layer.0': 0,
        'model.layer.1': 0,
        'model.layer.2': 'cpu',
        'model.layer.3': 'cpu',
        'model.norm': 0
    }

    analysis = analyze_device_map(device_map)

    assert 'device_counts' in analysis
    assert 'module_types' in analysis

    assert analysis['device_counts']['0'] == 3
    assert analysis['device_counts']['cpu'] == 2

    print("✅ Device map analysis works")

def test_model_memory_estimation():
    """Test model memory estimation"""
    print("\nTesting Model Memory Estimation...")

    # Test 7B model
    fp32_size = estimate_model_memory(7, 'float32')
    fp16_size = estimate_model_memory(7, 'float16')
    int8_size = estimate_model_memory(7, 'int8')

    assert fp32_size == 28.0  # 7B * 4 bytes
    assert fp16_size == 14.0  # 7B * 2 bytes
    assert int8_size == 7.0   # 7B * 1 byte

    print(f"✅ 7B model: FP32={fp32_size}GB, FP16={fp16_size}GB, INT8={int8_size}GB")

if __name__ == '__main__':
    print("="*60)
    print("Memory Utilities Tests")
    print("="*60)

    try:
        test_gpu_memory()
        test_cpu_memory()
        test_disk_usage()
        test_device_map_analysis()
        test_model_memory_estimation()

        print("\n" + "="*60)
        print("✅ ALL MEMORY UTILS TESTS PASSED")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
