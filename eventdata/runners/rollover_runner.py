import elasticsearch

def rollover(es, params):
    """
    Runs a rollover operation against Elasticsearch.

    It expects the parameter hash to contain a key "alias" specifying the alias to rollover 
    as well as a key "body" containing the actual rollover request and associated conditions.

    """
    es.indices.rollover(alias=params["alias"], body=params["body"])
    return 1, "ops"
