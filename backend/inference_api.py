#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inference API Wrapper
Command-line interface for the inference engine
Communicates with Node.js via JSON stdout messages
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.inference_engine import InferenceEngine
from backend.config import config

# Configure logging
def setup_logging(session_id: str, log_level: str = 'INFO'):
    """Setup logging to file and stderr"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'inference_{session_id}_{timestamp}.log')

    # Configure logger
    logger = logging.getLogger('inference_api')
    logger.setLevel(getattr(logging, log_level.upper()))

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Stderr handler (won't interfere with stdout JSON)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stderr_handler)

    return logger, log_file


logger = None  # Global logger


def emit_json(message_type: str, data: dict):
    """
    Emit JSON message to stdout for Node.js

    Args:
        message_type: Type of message
        data: Message data
    """
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    json_str = json.dumps(message)

    # Log to file/stderr
    if logger:
        logger.debug(f"EMIT -> {message_type}: {json.dumps(data, indent=2)}")

    # Send to stdout for Node.js
    print(json_str, flush=True)


def main():
    """Main entry point for CLI inference"""
    global logger

    parser = argparse.ArgumentParser(description='LLM Inference API')
    parser.add_argument('--model', required=True, help='Model ID (e.g., opt-30b, llama2-7b)')
    parser.add_argument('--prompt', required=True, help='Input prompt')
    parser.add_argument('--quantization', default='8-bit', choices=['8-bit', '4-bit', 'none'])
    parser.add_argument('--enable-fp32-cpu-offload', action='store_true',
                        help='Enable FP32 CPU offload')
    parser.add_argument('--max-length', type=int, default=50, help='Max generation length')
    parser.add_argument('--temperature', type=float, default=0.7, help='Temperature')
    parser.add_argument('--top-p', type=float, default=0.9, help='Top-p sampling')
    parser.add_argument('--top-k', type=int, default=50, help='Top-k sampling')
    parser.add_argument('--gpu-memory', default='14GiB', help='GPU memory limit')
    parser.add_argument('--cpu-memory', default='56GiB', help='CPU memory limit')
    parser.add_argument('--session-id', required=True, help='Session ID for tracking')
    parser.add_argument('--offload-folder', default='./offload', help='Offload folder path')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])

    args = parser.parse_args()

    # Setup logging
    logger, log_file = setup_logging(args.session_id, args.log_level)
    logger.info("=" * 80)
    logger.info(f"INFERENCE API STARTED - Session: {args.session_id}")
    logger.info("=" * 80)
    logger.info(f"Log file: {log_file}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Prompt: {args.prompt[:100]}...")
    logger.info(f"Quantization: {args.quantization}")
    logger.info(f"FP32 CPU Offload: {args.enable_fp32_cpu_offload}")
    logger.info(f"Max Length: {args.max_length}")
    logger.info(f"Temperature: {args.temperature}")
    logger.info(f"GPU Memory: {args.gpu_memory}")
    logger.info(f"CPU Memory: {args.cpu_memory}")
    logger.info("=" * 80)

    try:
        # Validate model exists
        logger.info(f"Validating model: {args.model}")
        if args.model not in config.MODEL_REGISTRY:
            logger.warning(f"Model {args.model} not found in registry, searching by HF name...")
            # Try to find by HF name
            found = False
            for model_id, model_cfg in config.MODEL_REGISTRY.items():
                if model_cfg['hf_name'] == args.model:
                    args.model = model_id
                    found = True
                    logger.info(f"Found model by HF name: {model_id}")
                    break

            if not found:
                logger.error(f"Model {args.model} not found in registry")
                emit_json('error', {'error': f'Model {args.model} not found in registry'})
                sys.exit(1)

        # Initialize inference engine with callback
        logger.info(f"Initializing InferenceEngine for {args.model}")
        engine = InferenceEngine(
            model_id=args.model,
            progress_callback=emit_json
        )

        # Load model
        logger.info("Starting model loading...")
        emit_json('status', {
            'status': 'initializing',
            'message': f'Initializing inference engine for {args.model}...'
        })

        success = engine.load_model(
            quantization=args.quantization,
            enable_fp32_cpu_offload=args.enable_fp32_cpu_offload,
            gpu_memory=args.gpu_memory,
            cpu_memory=args.cpu_memory,
            offload_folder=args.offload_folder
        )

        if not success:
            logger.error("Model loading failed")
            emit_json('error', {'error': 'Failed to load model'})
            sys.exit(1)

        logger.info("Model loaded successfully, starting text generation")

        # Generate text
        result = engine.generate(
            prompt=args.prompt,
            max_length=args.max_length,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            do_sample=True
        )

        logger.info(f"Generation completed: {result['metrics']['tokensGenerated']} tokens in {result['metrics']['genTime']:.2f}s")

        # Emit completion
        emit_json('complete', {
            'status': 'completed',
            'duration': result['metrics']['totalTime'] * 1000,  # Convert to ms
            'metrics': result['metrics']
        })

        # Cleanup
        logger.info("Cleaning up and unloading model")
        engine.unload_model()

        logger.info("=" * 80)
        logger.info("INFERENCE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("Inference interrupted by user (KeyboardInterrupt)")
        emit_json('status', {
            'status': 'interrupted',
            'message': 'Inference interrupted by user'
        })
        sys.exit(130)

    except Exception as e:
        logger.error(f"EXCEPTION: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        emit_json('error', {'error': str(e)})
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
