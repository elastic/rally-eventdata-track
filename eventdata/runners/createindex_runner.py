import logging
import json
import elasticsearch

logger = logging.getLogger("track.eventdata")

def createindex(es, params):
    """
    Creates an index in Elasticsearch with given aliases. It also uploads configured template if configured.
    This runner can be used to set up indices that will use the rollover mechanism at the start of a benchmark.

    It expects the parameter hash to contain the following keys:
        "index_name"           - Specifies the index name to create. Defaults to 'elasticlogs-000001' if not specified.
        "alias"                - Alias to associate with this index. Defaults to 'elasticlogs_write' if not specified.
        "index_template_body"  - Index template body.
        "index_template_name"  - Specifies the name of the index template being uploaded if one has been specified through the 
                                 "index_template_body" parameter. Defaults to 'elasticlogs'
    """
    if 'index_template_body' in params:
        if 'index_template_name' in params:
        	template_name = params['index_template_name']
        else:
        	template_name = 'elasticlogs'
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[createindex] Upload index template {} => {}".format(template_name, json.dumps(params['index_template_body'])))

        es.indices.put_template(name=template_name, body=params['index_template_body'])

    if 'alias' in params:
    	b = { 'aliases': {} }
    	b['aliases'][params['alias']] = {}
    else:
        b = { 'aliases': { 'elasticlogs_write': {} } }

    if 'index_name' in params:
        index_name = params['index_name']
    else:
        index_name = 'elasticlogs-000001'
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("[createindex] Create index {} => {}".format(index_name, json.dumps(b)))

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=b, ignore=400)

    return 1, "ops"
