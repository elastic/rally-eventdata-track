import logging
import json
import elasticsearch

logger = logging.getLogger("track.elasticlogs")

def loadtemplate(es, params):
    """
    Creates an index in Elasticsearch with given aliases. It also uploads configured template if configured.
    This runner can be used to set up indices that will use the rollover mechanism at the start of a benchmark.

    It expects the parameter hash to contain the following keys:
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

    return 1, "ops"
