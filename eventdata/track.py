from eventdata.parameter_sources.elasticlogs_bulk_source import ElasticlogsBulkSource
from eventdata.parameter_sources.metricbeat_bulk_source import MetricbeatBulkSource
from eventdata.parameter_sources.elasticlogs_kibana_source import ElasticlogsKibanaSource
from eventdata.parameter_sources.metricbeat_kibana_source import MetricbeatKibanaSource
from eventdata.parameter_sources.interval_query_source import IntervalQuerySource
from eventdata.parameter_sources.sample_based_bulk_source import SampleBasedBulkSource
from eventdata.runners import deleteindex_runner
from eventdata.runners import fieldstats_runner
from eventdata.runners import indicesstats_runner
from eventdata.runners import kibana_runner
from eventdata.runners import nodestorage_runner
from eventdata.runners import rollover_runner


def register(registry):
    registry.register_param_source("elasticlogs_bulk", ElasticlogsBulkSource)
    registry.register_param_source("metricbeat_bulk", MetricbeatBulkSource)
    registry.register_param_source("elasticlogs_kibana", ElasticlogsKibanaSource)
    registry.register_param_source("metricbeat_kibana", MetricbeatKibanaSource)
    registry.register_param_source("interval_query", IntervalQuerySource)
    registry.register_param_source("sample_based_bulk", SampleBasedBulkSource)
    registry.register_runner("delete_indices", deleteindex_runner.deleteindex)
    registry.register_runner("fieldstats", fieldstats_runner.fieldstats)
    registry.register_runner("indicesstats", indicesstats_runner.indicesstats)
    registry.register_runner("kibana", kibana_runner.kibana)
    registry.register_runner("node_storage", nodestorage_runner.nodestorage)
    registry.register_runner("rollover", rollover_runner.rollover)
