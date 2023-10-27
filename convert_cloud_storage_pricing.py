#!/usr/bin/env python
"""Converts a price expressed in one capacity per unit time into another per
unit time. Useful for converting between GB/month and TB/hour.

For example, if you have a price of $0.145 per GB per month and want to
convert to a price per TB per hour, you would run:

$ convert-cloud-storage-pricing.py 0.145 GB/mo TB/h
"""

import argparse

def decode_unit(unit):
    """Converts a unit to a tuple of (base, exponent)

    Args:
        unit: A string representing a unit of bytes or time. For example,
        GB or TiB.
    
    Returns:
        A tuple of (base, exponent) where base is the base of the unit (1000 or
        1024) and exponent is the exponent of the unit (0 for bytes, 1 for
        kilobytes, 2 for megabytes, etc.)
    """

    unit = unit.lower().strip()

    if len(unit) > 1 and unit[1] == "i":
        base = 1024
    else:
        base = 1000

    if unit[0] == "k":
        exponent = 1
    elif unit[0] == "m":
        exponent = 2
    elif unit[0] == "g":
        exponent = 3
    elif unit[0] == "t":
        exponent = 4
    elif unit[0] == "p":
        exponent = 5
    elif unit[0] == "e":
        exponent = 6
    else:
        exponent = 0

    return (base, exponent)


def convert_bytes(quantity, from_unit, to_unit):
    """Converts quantity bytes from from_unit to to_unit

    Args:
        quantity: A float representing the quantity of bytes to convert
        from_unit: A string representing the unit of bytes to convert from
            such as GB or TiB
        to_unit: A string representing the unit of bytes to convert to such
            as GB or TiB

    Returns:
        A float representing the quantity of bytes expressed in to_unit
    """
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()

    # convert quantity to bytes
    base, exponent = decode_unit(from_unit)
    quantity = quantity * base ** exponent

    # then convert quantity to to_unit
    base, exponent = decode_unit(to_unit)
    quantity = quantity / base ** exponent

    return quantity

def to_seconds(quantity, unit):
    """Converts a quantity of time into seconds

    Args:
        quantity: A float representing the quantity of time to convert
        unit: A string representing the unit of time to convert from such as
            sec, h, mo, ms, y, etc.

    Returns:
        A float representing the quantity of time expressed in seconds.
    """
    unit = unit.lower().strip()

    # convert quantity to seconds
    if unit[0] == "s":
        pass
    elif unit[0] == "u":
        quantity = quantity / 1000000
    elif unit[0] == "m":
        if len(unit) > 1:
            if unit[:2] == "ms":
                quantity = quantity / 1000
            elif unit[:2] == "mo":
                quantity = quantity * 60 * 60 * 24 * 30
            else:
                raise ValueError("Unit must be m, ms, or mo")
        else:
            quantity = quantity * 60
    elif unit[0] == "h":
        quantity = quantity * 60 * 60
    elif unit[0] == "d":
        quantity = quantity * 60 * 60 * 24
    elif unit[0] == "w":
        quantity = quantity * 60 * 60 * 24 * 7
    elif unit[0] == "y":
        quantity = quantity * 60 * 60 * 24 * 365
    else:
        raise ValueError("Invalid unit: " + unit)
    return quantity

def convert_time(quantity, from_unit, to_unit):
    """Converts a unit of time from from_unit to to_unit

    For example, convert_time(10, "h", "m") would return 600

    Args:
        quantity: A float representing the quantity of time to convert
        from_unit: A string representing the unit of time to convert from
            such as sec, h, mo, ms, y, etc.
        to_unit: A string representing the unit of time to convert to such
            as sec, h, mo, ms, y, etc.

    Returns:
        A float representing the quantity of time expressed in to_unit.
    """
    qty_in_seconds = to_seconds(quantity, from_unit)
    return qty_in_seconds / to_seconds(1, to_unit)

def main(argv=None):
    """Converts a price expressed in one capacity per time into another.

    For example, if you have a price of $0.145 per GB per month and want to
    convert to a price per TB per hour, you would run:

    $ convert-cloud-storage-pricing.py 0.145 GB/mo TB/h
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("price", type=float, help="Price in dollars")
    parser.add_argument("from_unit", type=str, help="Unit of price per time to convert from")
    parser.add_argument("to_unit", type=str, help="Unit of price per time to convert to")
    args = parser.parse_args()

    from_capacity, from_time = args.from_unit.split("/")
    to_capacity, to_time = args.to_unit.split("/")

    converted_price = args.price / convert_bytes(1, from_capacity, to_capacity)
    converted_time = convert_time(1, from_time, to_time)

    print("${0:.3f}/{1}/{2} is ${3:.5f}/{4}/{5}".format(
        args.price,
        from_capacity,
        from_time,
        converted_price / converted_time,
        to_capacity,
        to_time))

if __name__ == "__main__":
    main()
