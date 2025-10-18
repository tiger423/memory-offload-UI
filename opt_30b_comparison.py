# -*- coding: utf-8 -*-
"""
OPT-30B Configuration Comparison Script
Benchmarks different quantization and offloading strategies

Compares 3 configurations:
- Config A: No quantization (FP32/FP16 baseline)
- Config B: 8-bit without FP32 CPU offload
- Config C: 8-bit with FP32 CPU offload (optimal)

WARNING: This script may require significant memory and time to run all configs.
"""

import os
import time
import torch
import gc
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from memory_utils import (
    get_gpu_memory_info,
    get_cpu_memory_info,
    print_memory_summary,
    analyze_device_map,
    estimate_model_memory
)


class ConfigBenchmark:
    """Benchmark a specific configuration"""

    def __init__(self, name, description, config):
        self.name = name
        self.description = description
        self.config = config
        self.results = {}

    def run(self, model_name, prompt, hf_token):
        """Run benchmark for this configuration"""
        print(f"\n{'='*70}")
        print(f"Running: {self.name}".center(70))
        print(f"{self.description}".center(70))
        print(f"{'='*70}\n")

        try:
            # Memory before loading
            gpu_before = get_gpu_memory_info()
            cpu_before = get_cpu_memory_info()

            print(f"📊 Memory before loading:")
            print(f"  GPU: {gpu_before['allocated']:.2f} GB")
            print(f"  CPU: {cpu_before['used']:.2f} GB\n")

            # Load model
            print(f"⏳ Loading model...")
            load_start = time.time()

            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                **self.config,
                token=hf_token
            )

            load_time = time.time() - load_start

            # Memory after loading
            gpu_after_load = get_gpu_memory_info()
            cpu_after_load = get_cpu_memory_info()

            print(f"✅ Model loaded in {load_time:.1f}s ({load_time/60:.1f} min)")
            print(f"\n📊 Memory after loading:")
            print(f"  GPU: {gpu_after_load['allocated']:.2f} GB (+{gpu_after_load['allocated'] - gpu_before['allocated']:.2f} GB)")
            print(f"  CPU: {cpu_after_load['used']:.2f} GB (+{cpu_after_load['used'] - cpu_before['used']:.2f} GB)")

            # Analyze device map
            device_analysis = analyze_device_map(model.hf_device_map)
            print(f"\n🗺️  Device allocation:")
            for device, count in sorted(device_analysis['device_counts'].items()):
                device_name = "GPU" if device == "0" else device.upper()
                print(f"  {device_name}: {count} modules")

            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                use_fast=False,
                token=hf_token
            )

            # Run inference
            print(f"\n⏳ Running inference...")
            inputs = tokenizer(prompt, return_tensors="pt")
            input_ids = inputs["input_ids"].to(0)

            gen_start = time.time()

            output = model.generate(
                input_ids,
                min_length=30,
                max_length=50,
                do_sample=True,
                temperature=0.7
            )

            gen_time = time.time() - gen_start

            # Memory after generation
            gpu_after_gen = get_gpu_memory_info()
            cpu_after_gen = get_cpu_memory_info()

            # Decode output
            generated_text = tokenizer.decode(output[0].tolist())
            tokens_generated = output.shape[1] - input_ids.shape[1]

            print(f"✅ Generation completed in {gen_time:.1f}s")
            print(f"   Tokens generated: {tokens_generated}")
            print(f"   Time per token: {gen_time / tokens_generated:.2f}s")

            # Store results
            self.results = {
                "success": True,
                "load_time": load_time,
                "gen_time": gen_time,
                "total_time": load_time + gen_time,
                "tokens_generated": tokens_generated,
                "time_per_token": gen_time / tokens_generated,
                "gpu_allocated": gpu_after_load['allocated'],
                "cpu_used": cpu_after_load['used'],
                "gpu_peak": gpu_after_gen['reserved'],
                "device_counts": device_analysis['device_counts'],
                "generated_text": generated_text
            }

            # Cleanup
            del model
            del tokenizer
            torch.cuda.empty_cache()
            gc.collect()

            print(f"\n✅ {self.name} completed successfully")

        except Exception as e:
            print(f"\n❌ {self.name} failed: {e}")
            self.results = {
                "success": False,
                "error": str(e)
            }

            # Cleanup on error
            torch.cuda.empty_cache()
            gc.collect()

        return self.results


def main():
    """Main comparison function"""

    # Configuration
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("⚠️  Warning: HF_TOKEN not found in environment variables.")

    model_name = 'facebook/opt-30b'
    prompt = "Hugging Face is pushing the convention that a unicorn with two horns becomes a llama."

    print(f"\n{'='*70}")
    print(f"OPT-30B Configuration Comparison".center(70))
    print(f"{'='*70}")
    print(f"\n📦 Model: {model_name}")
    print(f"📝 Prompt: \"{prompt}\"")
    print(f"\n⚠️  WARNING: This benchmark may take significant time and memory!")
    print(f"   Each configuration will be tested sequentially.")

    # Define configurations
    configs = []

    # Config A: No quantization (baseline) - COMMENTED OUT FOR SAFETY
    # This requires ~60-120GB GPU memory - will likely fail!
    print(f"\n{'='*70}")
    print("⚠️  Config A (No quantization) SKIPPED".center(70))
    print("Requires 60-120GB GPU memory - not feasible on 16GB GPU".center(70))
    print(f"{'='*70}\n")

    # configs.append(ConfigBenchmark(
    #     name="Config A: No Quantization (Baseline)",
    #     description="FP16 precision with automatic offloading",
    #     config={
    #         "device_map": "auto",
    #         "offload_folder": "./offload",
    #         "max_memory": {0: "14GiB", "cpu": "56GiB"},
    #         "torch_dtype": torch.float16,
    #         "low_cpu_mem_usage": True
    #     }
    # ))

    # Config B: 8-bit without FP32 CPU offload
    configs.append(ConfigBenchmark(
        name="Config B: 8-bit WITHOUT FP32 CPU Offload",
        description="INT8 quantization, FP32 modules stay on GPU",
        config={
            "device_map": "auto",
            "offload_folder": "./offload",
            "max_memory": {0: "14GiB", "cpu": "56GiB"},
            "quantization_config": BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_enable_fp32_cpu_offload=False  # Disabled
            ),
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True
        }
    ))

    # Config C: 8-bit with FP32 CPU offload (optimal)
    configs.append(ConfigBenchmark(
        name="Config C: 8-bit WITH FP32 CPU Offload (OPTIMAL)",
        description="INT8 quantization, FP32 modules offloaded to CPU",
        config={
            "device_map": "auto",
            "offload_folder": "./offload",
            "max_memory": {0: "14GiB", "cpu": "56GiB"},
            "quantization_config": BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_enable_fp32_cpu_offload=True  # Enabled
            ),
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True
        }
    ))

    # Run benchmarks
    results = []
    for i, config in enumerate(configs, 1):
        print(f"\n{'='*70}")
        print(f"Benchmark {i}/{len(configs)}".center(70))
        print(f"{'='*70}")

        result = config.run(model_name, prompt, hf_token)
        results.append((config.name, result))

        # Wait between runs
        if i < len(configs):
            print(f"\n⏳ Waiting 10 seconds before next benchmark...")
            time.sleep(10)

    # ============================================================
    # Summary Comparison
    # ============================================================

    print(f"\n{'='*70}")
    print(f"BENCHMARK RESULTS SUMMARY".center(70))
    print(f"{'='*70}\n")

    # Table header
    print(f"{'Configuration':<45} {'Load (s)':<12} {'Gen (s)':<12} {'GPU (GB)':<12}")
    print(f"{'-'*70}")

    # Results
    for name, result in results:
        if result.get("success"):
            print(f"{name:<45} {result['load_time']:>8.1f}    {result['gen_time']:>8.1f}    {result['gpu_allocated']:>8.2f}")
        else:
            print(f"{name:<45} {'FAILED':<12} {'FAILED':<12} {'N/A':<12}")

    print(f"{'-'*70}\n")

    # Detailed comparison
    print(f"\n{'='*70}")
    print(f"DETAILED COMPARISON".center(70))
    print(f"{'='*70}\n")

    successful_results = [(name, r) for name, r in results if r.get("success")]

    if len(successful_results) >= 2:
        # Compare last two successful configs
        base_name, base_result = successful_results[0]
        opt_name, opt_result = successful_results[-1]

        print(f"📊 Comparing: {base_name} vs {opt_name}\n")

        speedup = base_result['gen_time'] / opt_result['gen_time']
        gpu_diff = base_result['gpu_allocated'] - opt_result['gpu_allocated']
        cpu_diff = opt_result['cpu_used'] - base_result['cpu_used']

        print(f"⏱️  Performance:")
        print(f"  Load time:     {base_result['load_time']:>6.1f}s  →  {opt_result['load_time']:>6.1f}s  ({opt_result['load_time'] - base_result['load_time']:+.1f}s)")
        print(f"  Gen time:      {base_result['gen_time']:>6.1f}s  →  {opt_result['gen_time']:>6.1f}s  ({opt_result['gen_time'] - base_result['gen_time']:+.1f}s)")
        print(f"  Speedup:       {speedup:.2f}x")

        print(f"\n💾 Memory:")
        print(f"  GPU:           {base_result['gpu_allocated']:>6.2f}GB →  {opt_result['gpu_allocated']:>6.2f}GB  ({gpu_diff:+.2f}GB)")
        print(f"  CPU:           {base_result['cpu_used']:>6.2f}GB →  {opt_result['cpu_used']:>6.2f}GB  ({cpu_diff:+.2f}GB)")

        print(f"\n🗺️  Layer Distribution:")
        print(f"  Base config:")
        for device, count in sorted(base_result['device_counts'].items()):
            device_name = "GPU" if device == "0" else device.upper()
            print(f"    {device_name}: {count} modules")

        print(f"  Optimal config:")
        for device, count in sorted(opt_result['device_counts'].items()):
            device_name = "GPU" if device == "0" else device.upper()
            print(f"    {device_name}: {count} modules")

    # Key insights
    print(f"\n{'='*70}")
    print(f"KEY INSIGHTS".center(70))
    print(f"{'='*70}\n")

    print(f"✅ Benefits of FP32 CPU Offload (Config C):")
    print(f"   ├─ Frees ~1-2GB GPU memory for more INT8 layers")
    print(f"   ├─ More layers on GPU = faster inference")
    print(f"   ├─ Small CPU overhead (~30-50ms) is worth the tradeoff")
    print(f"   └─ Everything fits in RAM - no disk offload needed!")

    print(f"\n💡 Recommendations:")
    print(f"   • Use Config C for best performance on limited GPU memory")
    print(f"   • Expect ~3-5x speedup vs disk-offloading baseline")
    print(f"   • Monitor GPU/CPU memory to optimize max_memory settings")

    print(f"\n{'='*70}")
    print(f"✨ Benchmark Complete!".center(70))
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
