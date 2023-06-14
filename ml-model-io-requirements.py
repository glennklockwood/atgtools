#!/usr/bin/env python3
"""Estimates the I/O throughput required by a given deep learning model and GPU.
"""

import argparse

FLOPS_PER_SAMPLE = {
    "cosmoflow":  247.0 * 1024**3,
    "deepcam":   2887.0 * 1024**3,
    "resnet50":    31.0 * 1024**3,
}
SAMPLE_SIZE_BYTES = {
    "cosmoflow":   16.0 * 1024**2,
    "deepcam":     27.0 * 1024**2,
    "resnet50":    0.14 * 1024**2,
}
GPU_FLOPS = {
    "v100":  130.0 * 1000**4,
    "a100":  312.0 * 1000**4, # fp16
    "h100": 3958.0 * 1000**4, # fp8
    "8x-v100": 8 *  130.0 * 1000**4,
    "8x-a100": 8 * 312.0 * 1000**4, # fp16
    "8x-h100": 8 * 3958.0 * 1000**4, # fp8
    # from https://ieeexplore.ieee.org/document/9652793
    "v100-cosmoflow-lo": 35.0 * 1000**4,
    "v100-cosmoflow-hi": 50.0 * 1000**4,
}

def human_readable_bytes(qty, base=2):
    """Converts bytes to human readable unit

    Args:
        qty (float): number of bytes
        base (int): base of the unit (2 or 10)
    
    Returns:
        Tuple of float (number of bytes in the most appropriate unit) and str
        (unit of the returned value)
    """
    if base == 2:
        units = ["bytes", "KiB", "MiB", "GiB", "TiB"]
        divisor = 1024
    elif base == 10:
        units = ["bytes", "KB", "MB", "GB", "TB"]
        divisor = 1000
    else:
        raise ValueError("base must be 2 or 10")

    unit = 0
    while qty > divisor and unit < len(units) - 1:
        qty /= divisor
        unit += 1
    return qty, units[unit]

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=FLOPS_PER_SAMPLE.keys())
    parser.add_argument("--gpu", choices=GPU_FLOPS.keys(), default="v100")
    parser.add_argument("--base", choices=[2, 10], type=int, default=2)
    args = parser.parse_args(argv)

    required_bytes_sec = GPU_FLOPS[args.gpu] / FLOPS_PER_SAMPLE[args.model] * SAMPLE_SIZE_BYTES[args.model]

    print("Model: {:s}".format(args.model))
    print("GPU:   {:s}".format(args.gpu))
    print("FLOPS/sample: {:.2f}".format(FLOPS_PER_SAMPLE[args.model]))
    print("FLOPS/GPU:    {:.2f}".format(GPU_FLOPS[args.gpu]))
    print("Samples/sec:  {:.2f}".format(GPU_FLOPS[args.gpu] / FLOPS_PER_SAMPLE[args.model]))
    print("{:s} on {:s} requires {:.2f} {:s}/s".format(
        args.model,
        args.gpu,
        *human_readable_bytes(required_bytes_sec, base=args.base)))

if __name__ == "__main__":
    main()
