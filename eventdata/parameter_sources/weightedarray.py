import json
import random
import gzip
import sys
import itertools
import bisect


class WeightedArray:
    # These data sets have a very long tail and we apply a staged approach to  save memory.
    # If we'd just generate one large array, the array length would be in the tens of
    # millions for some of the arrays resulting in an unacceptable memory usage per client.
    #
    # Based on experiments with the current data sets, we settled that one list represents the top 99
    # percent of all items and the other one represents the long tail with the last percent. These
    # values provide an acceptable tradeoff for memory usage.
    CUTOFF_FREQUENCY = 100
    # defines the percentage of values that represents the "bottom" part.
    CUTOFF_PERCENT = 1 / CUTOFF_FREQUENCY

    def __init__(self, json_file):
        with gzip.open(json_file, 'rt') as data_file:
            item_list = json.load(data_file)

        # 1. Calculate a histogram of all weights.
        h = self.histogram(item_list)

        # 2. Calculate the weight that represents the last percent based on the histogram ...
        bottom_percent_weight = self.weight_of_bottom_percent(h, percent=WeightedArray.CUTOFF_PERCENT)

        # 3. ... so we can partition the items into the bottom and top parts.
        #
        # This implementation results in a peak memory usage of one client between 200 and 300 MB.
        self._top_choices = self.create_items(item_list, min_weight=bottom_percent_weight)
        self._bottom_choices = self.create_items(item_list, max_weight=bottom_percent_weight)

        self._counter = 0
        # we increment before accessing the elements
        self._bottom_idx = -1
        self._top_idx = -1
        # Not calculating the length over and over on the hot code path gives us a little bit higher peak throughput
        self._bottom_len = len(self._bottom_choices)
        self._top_len = len(self._top_choices)

    def weight_of_bottom_percent(self, histogram, percent):
        """
        Determines the corresponding weight that represents at most the provided number of percent of all elements.

        :param histogram: A histogram of all elements.
        :param percent: A float representing the maximum number of elements that should be covered. 1.00 is 100% percent.
        """
        total = 0
        for weight, frequency in histogram.items():
            total += weight * frequency

        running_total = 0
        for weight, frequency in histogram.items():
            running_total += weight * frequency
            if running_total > percent * total:
                return weight

    def histogram(self, item_list):
        """
        Creates a histogram of the provided items.

        :param item_list: A list of tuples (weight, data).
        """
        h = {}
        for w, _ in item_list:
            if w not in h:
                h[w] = 0
            h[w] += 1
        return h

    def create_items(self, item_list, min_weight=None, max_weight=None):
        choices = []
        weights = []
        low = sys.maxsize

        for w, c in item_list:
            if (min_weight and w > min_weight) or (max_weight and w <= max_weight):
                low = low if low < w else w
                weights.append(w)
                choices.append(c)

        cumdist = list(itertools.accumulate(weights))
        # choose the size of the resulting array so that the item with the lowest frequency still has a chance to appear (once).
        total = cumdist[-1]
        size = total // low
        # pre-generate the randomly distributed weighted choices as we want to avoid any expensive operations
        # on the fast-path (i.e. in #get_random()).
        #
        return [choices[bisect.bisect(cumdist, random.random() * total)] for _ in range(size)]

    def get_random(self):
        self._counter += 1
        if self._counter < WeightedArray.CUTOFF_FREQUENCY:
            self._top_idx = (self._top_idx + 1) % self._top_len
            return self._top_choices[self._top_idx]
        else:
            # Don't let this counter ever overflow. We're just interested in small counts anyway.
            self._counter = 0
            self._bottom_idx = (self._bottom_idx + 1) % self._bottom_len
            return self._bottom_choices[self._bottom_idx]
