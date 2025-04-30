from typing import List
from werkzeug.datastructures import ImmutableMultiDict

# Handy utility to check if an ImmutableMultiDict has all required keys present
def includes(iterable: ImmutableMultiDict, keys: List[str | int]) -> bool:
    for key in keys:
        if key not in iterable.keys():
            return False
    return True
