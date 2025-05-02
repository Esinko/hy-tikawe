from typing import List
from werkzeug.datastructures import ImmutableMultiDict


def includes(iterable: ImmutableMultiDict, keys: List[str | int]) -> bool:
    # Handy utility to check if an ImmutableMultiDict has all required keys present
    for key in keys:
        if key not in iterable.keys():
            return False
    return True
