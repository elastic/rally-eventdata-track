import operator

from fnmatch import fnmatch

def deleteindex(es, params):
    """
    Deletes all indices in Elasticsearch matching either the specified index pattern or
    the suffix of the index against a more complex pattern.

    :param es: Specifies the index pattern to delete. Defaults to 'elasticlogs-*'
    :type es: str
    :param params: Parameter hash containing one of the keys documented below.
    :type params: dict

        "index_pattern"        - Mandatory.
                                 Specifies the index pattern to delete. Defaults to 'elasticlogs-*'
        "filter_pattern"       - Optional.
                                 Restricts list of indices by comparing the integer suffix (see suffic_separator parameter below)
                                 with a value using an operator.

                                 It is a list specifying a comparison string and integer value.
                                 Comparison is executed against the index suffix extracted using the "suffix_separator" (see below).

                                 Example:

                                 For indices: 'elasticlogs-000001', 'elasticlogs-000002', ... 000010
                                 using:
                                    suffix_separator='-' and
                                    filter_pattern=["ge", 9]

                                will result in deleting indices 'elasticlogs-000009' and 'elasticlogs-000010'

                                The allowed operator string can be one of the following:
                                'lt', 'le', 'eq', 'ne', 'ge', 'gt'

                                and internally uses: https://docs.python.org/3/library/operator.html:

        "suffix_separator"     - Defaults to '-'. Used only when 'filter_pattern' is specified.
                                 Specifies string separator used to extract the index suffix, e.g. '-'.


    """
    def get_suffix(name, separator):
        if separator in name:
            name_parts = name.split(separator)
            if len(name_parts) > 1:
                try:
                    return int(name_parts[-1])
                except ValueError:
                    # log that suffix is not integer
                    return None
        return None

    def compare_index_suffix(name, filter_pattern, suffix_separator):
        allowed_comparison_ops = ['lt', 'le', 'eq', 'ne', 'ge', 'gt']
        suffix = get_suffix(name, suffix_separator)

        if suffix is None:
            return False

        try:
            cmp_operator = filter_pattern[0]
            cmp_value = filter_pattern[1]
            assert cmp_operator in allowed_comparison_ops
            assert hasattr(operator, cmp_operator) is True
            suffix_int = int(suffix)
        except (IndexError, AssertionError, ValueError):
            return False

        if cmp_operator(suffix_int, cmp_value):
            return True
        return False

    index_pattern = params.get('index_pattern', 'elasticlogs-*')
    filter_pattern = params.get('filter_pattern', None)
    suffix_separator = params.get('suffix_separator', '-')

    if filter_pattern:
        indices = es.cat.indices(h='index').split("\n")
        filtered_indices = [
            idx for idx in indices
            if fnmatch(idx, index_pattern) and
            compare_index_suffix(idx, filter_pattern, suffix_separator)
        ]

        es.indices.delete(",".join(filtered_indices))
    else:
        es.indices.delete(index=index_pattern)

    return 1, "ops"
