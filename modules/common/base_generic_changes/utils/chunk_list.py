# -*- coding: utf-8 -*-

def chunk_list(big_list, chunk_size):
    """
    Yield successive chunks from a list.
    Ref: http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    Args:
        big_list: big list of items.
        chunk_size: number of items in each chunk max.
    Returns:
        A list representing the next chunk of big_list.
    """
    for i in range(0, len(big_list), chunk_size):
        yield big_list[i:i + chunk_size]
