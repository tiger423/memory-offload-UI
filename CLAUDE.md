# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains a demonstration script for loading and running large language models (LLMs) using HuggingFace Transformers with memory-efficient device mapping and disk offloading. The primary focus is on running models that exceed available GPU/CPU memory by leveraging Accelerate's offloading capabilities.

## Key Concepts

### Memory Management Strategy
The codebase demonstrates a multi-tier memory hierarchy for running large models:
- **GPU Memory**: Limited allocation (e.g., 5GiB) for critical layers
- **CPU Memory**: Secondary buffer (e.g., 20GiB) for additional layers
- **Disk Offloading**: Storage in `./swap` directory for remaining model layers

### Device Map Architecture
The model uses `device_map="auto"` with Accelerate to automatically distribute layers across:
1. GPU (device 0) - embedding layers and output head
2. CPU - first few decoder layers
3. Disk - remaining decoder layers stored in offload_folder

## Running the Code

### Prerequisites
Required Python packages:
- `transformers` (HuggingFace)
- `accelerate` (for device mapping and offloading)
- `torch` (PyTorch)
- Optional: `bitsandbytes` (for quantization support, currently commented out)

### Execution
```bash
python opt-d-1-4.py
```

**Note**: The script contains a HuggingFace API token on line 11 which should be treated as sensitive. Consider using environment variables instead of hardcoding tokens.

### Configuration Parameters
Key parameters in [opt-d-1-4.py](opt-d-1-4.py):
- `my_model`: Model identifier (currently `facebook/opt-30b`)
- `max_memory`: Memory limits per device (line 25)
- `offload_folder`: Directory for disk offloading (line 24)
- Generation parameters: `min_length`, `max_length`, `do_sample` (line 39)

### Expected Behavior
- Model loading takes ~1-2 minutes (checkpoint shards loading)
- Total model size: ~120GB
- Generation time: varies significantly based on hardware and number of offloaded layers
- Output includes generated text and device mapping visualization

## Important Notes

### Security Considerations
- **Line 11 contains a hardcoded HuggingFace token** that should be removed or moved to environment variables before committing to version control
- The swap directory will contain model weights during execution and can grow very large

### Performance Characteristics
- Disk-offloaded layers significantly impact inference speed
- The example output shows ~500 seconds for a 30-token generation with heavy disk offloading
- Adjust `max_memory` parameters based on available hardware resources

### Quantization
The script includes commented-out quantization support using BitsAndBytesConfig (lines 17, 27). This can be enabled for further memory reduction at the cost of model precision.
