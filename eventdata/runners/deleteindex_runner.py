import elasticsearch

def deleteindex(es, params):
    """
    Deletes all indices in Elasticsearch matching the specified index pattern.

    It expects the parameter hash to contain the following key:
        "index_pattern"        - Specifies the index pattern to delete. Defaults to 'elasticlogs-*'
    """
    if 'index_pattern' in params:
        index_pattern = params['index_pattern']
    else:
        index_pattern = "elasticlogs-*"

    es.indices.delete(index=index_pattern)

    return 1, "ops"
