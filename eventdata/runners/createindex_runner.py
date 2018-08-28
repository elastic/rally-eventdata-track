import logging
import json
import os
import elasticsearch
from eventdata.utils import globals as gs

logger = logging.getLogger("track.eventdata")

def createindex(es, params):
    """
    Creates an index in Elasticsearch with given aliases. It also uploads configured template if configured.
    This runner can be used to set up indices that will use the rollover mechanism at the start of a benchmark.

    It expects the parameter hash to contain the following keys:
        "index_name"           - Specifies the index name to create. Defaults to 'elasticlogs-000001' if not specified.
        "alias"                - Alias to associate with this index. Defaults to 'elasticlogs_write' if not specified.
        "index_template_body"  - Index template body. If the `mappings` field is a string, this will be interpreted as a file 
                                 name the actual mapping should be loaded from.
        "index_template_name"  - Specifies the name of the index template being uploaded if one has been specified through the 
                                 "index_template_body" parameter. Defaults to 'elasticlogs'
    """
    if 'index_template_body' in params:
        if 'index_template_name' in params:
        	template_name = params['index_template_name']
        else:
        	template_name = 'elasticlogs'
        
        if 'mappings' in params['index_template_body'] and isinstance(params['index_template_body']['mappings'], str):
            if params['index_template_body']['mappings'] in gs.global_config.keys():
                mapping = gs.global_config[params['index_template_body']['mappings']]
            else:
                mapping_path = os.path.expandvars(params['index_template_body']['mappings'])
                logger.info("[createindex] Use mapping file: {}".format(mapping_path))
                mapping = json.loads(open(mapping_path, 'rt').read())
                gs.global_config[params['index_template_body']['mappings']] = mapping
        
            params['index_template_body']['mappings'] = mapping

        logger.info("[createindex] Upload index template {} => {}".format(template_name, json.dumps(params['index_template_body'])))

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
    
    logger.info("[createindex] Create index {} => {}".format(index_name, json.dumps(b)))

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=b, ignore=400)

    return 1, "ops"
        