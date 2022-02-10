import dataclasses
import sys

major, minor, patch, level, serial = sys.version_info
slotsAllowed = major >= 3 and minor >= 10


def slottedDataClass(*args, **kwargs):
    if slotsAllowed:
        return dataclasses.dataclass(*args, **kwargs)
    filteredKwargs = {}
    for flag, argument in kwargs.items():
        if flag != "slots":
            filteredKwargs[flag] = argument
    return dataclasses.dataclass(*args, **filteredKwargs)