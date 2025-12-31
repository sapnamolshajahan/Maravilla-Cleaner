# -*- coding: utf-8 -*-

"""
Utility functions used for generating serial-numbers.
"""


def numeric_decompose(raw):
    """
    Extract the numeric sections from a raw string, eg: 123xxeixo234 returns [123, 234].
    :param raw:
    :return: list of numbers extracted from the string
    """
    result = []
    element = ""
    for c in range(0, len(raw)):
        if raw[c].isdigit():
            element += raw[c]
        elif element:
            result.append(int(element))
            element = ""
    if element:
        result.append(int(element))
    return result


def compute_serial_format(serial_number):
    """
    Compute the format-string of a serial number.

    Expectation is that the last numeric segment in the serial-number will be the mutable part.

    :param serial_number:
    :return:
    """
    n_count = 0
    n_done = False
    result = ""

    ixs = list(range(0, len(serial_number)))
    ixs.reverse()
    for ix in ixs:
        if n_done:
            result = serial_number[ix] + result
            continue
        if serial_number[ix].isdigit():
            n_count = n_count + 1
            continue
        if n_count:
            result = serial_number[ix] + "{:0" + str(n_count) + "d}" + result
            n_done = True
            continue
        # trailing non-numeric
        result = serial_number[ix] + result

    if n_count and not n_done:
        result = "{:0" + str(n_count) + "d}" + result

    return result
