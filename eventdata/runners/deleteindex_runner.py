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
        "max_indices"          - Optional.
                                 int specifying maximum amount of allowable indices whose name satisfies `index-pattern`.
                                 'suffix_separator' is used to retrieve the integer suffixes to calculate indices to delete.

                                 Example:
                                 For the indices: 'elasticlogs-000001', 'elasticlogs-000002', ... 000010
                                 using:
                                    suffix_separator='-' and
                                    max_indices=8

                                 will result in deleting indices 'elasticlogs-000001' and 'elasticlogs-000002'
        "suffix_separator"     - Defaults to '-'. Used only when 'max_indices' is specified.
                                 Specifies string separator used to extract the index suffix, e.g. '-'.


    """
    def get_suffix(name, separator):
        if separator in name:
            name_parts = name.split(separator)
            if len(name_parts) > 1:
                try:
                    return int(name_parts[-1])
                except ValueError:
                    # TODO: log that suffix is not integer
                    return None
        return None

    index_pattern = params.get('index_pattern', 'elasticlogs-*')
    max_indices = params.get('max_indices', None)
    suffix_separator = params.get('suffix_separator', '-')

    if max_indices:
        indices = es.cat.indices(h='index').split("\n")
        indices_by_suffix = {get_suffix(idx, suffix_separator): idx
            for idx in indices
            if fnmatch(idx, index_pattern) and
            get_suffix(idx, suffix_separator) is not None
        }

        sorted_suffixes = sorted(list(indices_by_suffix.keys()))
        if len(sorted_suffixes) > max_indices:
            indices_to_delete = ",".join([indices_by_suffix[key] for key in sorted_suffixes[:max_indices]])
            es.indices.delete(indices_to_delete)
    else:
        es.indices.delete(index=index_pattern)

    return 1, "ops"
