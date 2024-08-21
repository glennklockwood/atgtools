#!/usr/bin/env python3
import argparse

def main(argv=None):
    parser = argparse.ArgumentParser(description='Convert a FIT rate to an annual failure rate')
    parser.add_argument('fit', type=float, help='FIT rate')
    parser.add_argument('--num', type=int, default=1, help='Number of components')
    args = parser.parse_args()

    single_component_fit = args.fit / args.num
    single_component_mtti_hrs = 1.0e9 / single_component_fit
    single_component_afr = single_component_fit / 1.0e9 * 8766

    system_fit = args.fit
    system_mtti_hrs = 1.0e9 / system_fit
    system_afr = system_fit / 1.0e9 * 8766

    print(f'Single-component FIT: {single_component_fit:,.1f}')
    print(f'Single-component AFR: {100.0 * single_component_afr:.2f}%')
    print(f'Single-component MTTI: {single_component_mtti_hrs:,.4f} hours')
    print(f'System FIT: {system_fit:,.1f}')
    print(f'System AFR: {100.0 * system_afr:.2f}%')
    print(f'System MTTI: {system_mtti_hrs:,.4f} hours')

if __name__ == "__main__":
    main()
