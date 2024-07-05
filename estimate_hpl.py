#!/usr/bin/env python3
"""Estimate the HPL performance of a GPU-based supercomputer using Gustafson's law.
"""

import argparse
import numpy
import scipy.optimize

def estimate_hpl(s_frac, num_nodes, single_node_tflops):
    """Applies Gustafson's law to estimate the HPL performance of a GPU-based
    supercomputer.

    Args:
        s_frac (float): Fraction of the HPL performance that scales linearly with the number of GPUs.
        num_nodes (int): Number of nodes in the supercomputer.
        single_node_tflops (float): HPL performance of a single node (in TFLOPS).

    Returns:
        float: The estimated HPL performance of the supercomputer (in TFLOPS).
    """

    return (s_frac + (1 - s_frac) * num_nodes * single_node_tflops)

def parameterize_gustafson(num_nodes, performance_tflops, single_node_tflops):
    """Estimates s_frac and single_node_tflops using Gustafson's law and
    performance scaling data.

    If you have a series of performance scaling data points, you can fit
    them to Gustafson's law to calculate the s_frac and single_node_tflops
    parameters for an application. For example, if you have the following:

        num_nodes = [  512,  800, 1200, 1600, 1800 ]
        performance_tflops = [  163000,  243000,  364000,  491000,  561000 ]

    This will tell you the s_frac (fraction of time spent in non-parallelizable
    execution) based on Gustafson's law:

        Speedup = s_frac + (1 - s_frac) * num_nodes

    Args:
        num_nodes (list): List of the number of nodes.
        performance_tflops (list): List of the performance of the application (in TFLOPS).
        single_node_tflops (float): Performance of the application on a single node (in TFLOPS).

    Returns:
        float: The s_frac parameter.
    """
    speedups = numpy.array(performance_tflops) / single_node_tflops
    def objective(s_frac):
        return speedups - (s_frac + (1 - s_frac) * numpy.array(num_nodes))

    s_frac = scipy.optimize.least_squares(objective, 0.5).x[0]

    return s_frac

if __name__ == '__main__':
    GPUS_PER_NODE = 8
    TFLOPS_PER_GPU_MEASURED = 45.5 # NVIDIA H100 shows 34 TF for FP64 vector,
    # 67 TF for FP64 matrix; this implies Tensor Core gives a 33.8% uplift over
    # FP64 vector

    parser = argparse.ArgumentParser(description="Estimate the HPL performance of a supercomputer using Gustafson's law.")
    parser.add_argument("num_nodes", type=int, help="Number of nodes in the supercomputer.")
    parser.add_argument("-p", "--serial-performance", default=TFLOPS_PER_GPU_MEASURED * GPUS_PER_NODE, type=float, help="HPL performance of a single node (in TFLOPS).")
    parser.add_argument("-s", "--s-frac", default=None, type=float, help="Fraction of the HPL performance that scales linearly with the number of GPUs.")
    args = parser.parse_args()

    if args.s_frac is None:
        NUM_NODES = [ 512,  800, 1200, 1600, 1800 ]
        PERFORMANCE_TFLOPS = numpy.array([163, 243, 364, 491, 561]) * 1000
        SINGLE_NODE_TFLOPS = GPUS_PER_NODE * TFLOPS_PER_GPU_MEASURED
        s_frac = parameterize_gustafson(NUM_NODES, PERFORMANCE_TFLOPS, SINGLE_NODE_TFLOPS)

        print("Assuming the following parameters from HPL at scale:")
        print(f"s_frac: {s_frac}, p_frac: {1 - s_frac}")

    # Example usage of estimate_hpl
    hpl_performance = estimate_hpl(s_frac, args.num_nodes, args.serial_performance)
    print(f"Estimated HPL performance for {args.num_nodes:4d} nodes: {hpl_performance / 1000:.2f} PFLOPS")