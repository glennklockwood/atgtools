#!/usr/bin/env python
"""Converts a measure of bytes and a measure of time into a normalized bandwidth metric"""

import argparse

import convert_cloud_storage_pricing

def main(argv=None):
    """Converts a measure of bytes and a measure of time into a normalized bandwidth metric

    Example:
        $ convert-bandwidth.py 1000 GB 1 hour MB/s
        0.278 MB/s
    """
    parser = argparse.ArgumentParser(description='Converts a measure of bytes and a measure of time into a normalized bandwidth metric')
    parser.add_argument('byte_quantity', type=float, help='The quantity of bytes to convert')
    parser.add_argument('byte_unit', type=str, help='The unit of bytes to convert from')
    parser.add_argument('time_quantity', type=float, help='The quantity of time to convert')
    parser.add_argument('time_unit', type=str, help='The unit of time to convert from')
    parser.add_argument('to_byte_unit', type=str, help='The unit of bytes to convert to')
    parser.add_argument('to_time_unit', type=str, nargs='?', default="s", help='The unit of time to convert to (optional)')
    parser.add_argument('-b', '--to-bits', action="store_true", help='Converts the output to bits (multiply by 8) (optional)')

    args = parser.parse_args()

    # convert provided byte quantity and units into to_unit
    converted_bytes = convert_cloud_storage_pricing.convert_bytes(
        args.byte_quantity,
        args.byte_unit,
        args.to_byte_unit)
    converted_time = convert_cloud_storage_pricing.convert_time(
        args.time_quantity,
        args.time_unit,
        args.to_time_unit)
    if args.to_bits:
        converted_bytes *= 8
    print(f"{converted_bytes / converted_time} {args.to_byte_unit}/{args.to_time_unit}")

if __name__ == '__main__':
    main()
