import json
import random
import gzip

class WeightedArray:
    def __init__(self, json_file):
        with gzip.open(json_file, 'rt') as data_file:    
            item_list = json.load(data_file)

        self._items = []
        self._totals = []
        self._sum = 0

        for item in item_list:
            self._sum += item[0]
            self._items.append(item[1])
            self._totals.append(self._sum)

        random.seed()

    def get_random(self):
        return self._items[self.__random_index()]

    def __random_index(self):
        minimumIndex = 0
        maximumIndex = len(self._totals) - 1
        total = 0

        rand = random.random() * self._sum

        while maximumIndex > minimumIndex:
            if self._totals[minimumIndex] > rand:
                break

            middleIndex = (int)((maximumIndex + minimumIndex) / 2)
            total = self._totals[middleIndex]

            if total > rand:
                maximumIndex = middleIndex
            else:
                if middleIndex > minimumIndex:
                    minimumIndex = middleIndex
                else:
                    minimumIndex += 1
                
        return minimumIndex
