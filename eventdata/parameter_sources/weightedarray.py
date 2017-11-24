import json
import random
import gzip
import sys
import itertools
import bisect


class WeightedArray:
    def __init__(self, json_file):
        with gzip.open(json_file, 'rt') as data_file:
            item_list = json.load(data_file)

        low = sys.maxsize
        high = -1

        choices = []
        weights = []

        for w, c in item_list:
            low = low if low < w else w
            high = high if high > w else w

            weights.append(w)
            choices.append(c)

        random.seed()
        # choose the size of the resulting array so that the item with the lowest frequency still has a chance to appear (once).
        size = high // low
        cumdist = list(itertools.accumulate(weights))
        # pre-generate the randomly distributed weighted choices as we want to avoid any expensive operations
        # on the fast-path (i.e. in #get_random()).
        self._items = [choices[bisect.bisect(cumdist, random.random() * cumdist[-1])] for _ in range(size)]
        self._idx = 0

    def get_random(self):
        self._idx = (self._idx + 1) % len(self._items)
        return self._items[self._idx]
