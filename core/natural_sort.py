"""Natural sorting for filenames and serial numbers."""

import re
from typing import Any, Callable, Iterable, List, TypeVar

T = TypeVar("T")

_NATURAL_SPLIT_REGEX = re.compile(r"(\d+)")


def natural_key(text: str) -> List[Any]:
    """
    Produce a sorting key list where integer sequences are converted to integers,
    enabling natural sorting (e.g. 'item2' comes before 'item10').
    Strings are converted to lower-case for case-insensitive ordering.
    """
    if text is None:
        return []
    text_str = str(text).strip()
    parts = _NATURAL_SPLIT_REGEX.split(text_str)
    key: List[Any] = []
    for part in parts:
        if not part:
            continue
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.casefold())
    return key


def natural_sort(items: Iterable[T], key: Callable[[T], str] | None = None) -> List[T]:
    """
    Return a new list of items sorted naturally.
    If key is provided, it extracts the string to sort by.
    """
    if key is None:
        return sorted(items, key=lambda x: natural_key(str(x)))
    return sorted(items, key=lambda x: natural_key(key(x)))
