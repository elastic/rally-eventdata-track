from eventdata.parameter_sources.elasticlogs_bulk_source import ElasticlogsBulkSource
from eventdata.parameter_sources.elasticlogs_kibana_source import ElasticlogsKibanaSource
from eventdata.parameter_sources.sample_based_bulk_source import SampleBasedBulkSource
from eventdata.runners import rollover_runner
from eventdata.runners import createindex_runner
from eventdata.runners import deleteindex_runner 
from eventdata.runners import kibana_runner
from eventdata.runners import indicesstats_runner
from eventdata.runners import fieldstats_runner

def register(registry):
    registry.register_param_source("elasticlogs_bulk", ElasticlogsBulkSource)
    registry.register_param_source("elasticlogs_kibana", ElasticlogsKibanaSource)
    registry.register_param_source("sample_based_bulk", SampleBasedBulkSource)
    registry.register_runner("rollover", rollover_runner.rollover)
    registry.register_runner("createindex", createindex_runner.createindex)
    registry.register_runner("deleteindex", deleteindex_runner.deleteindex)
    registry.register_runner("kibana", kibana_runner.kibana)
    registry.register_runner("indicesstats", indicesstats_runner.indicesstats)
    registry.register_runner("fieldstats", fieldstats_runner.fieldstats)
