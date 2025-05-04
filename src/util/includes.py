from typing import List, Union
from werkzeug.datastructures import ImmutableMultiDict


def includes(iterable: ImmutableMultiDict, keys: List[Union[str, int]]) -> bool:
    # Handy utility to check if an ImmutableMultiDict has all required keys present
    for key in keys:
        if key not in iterable.keys():
            return False
    return True
