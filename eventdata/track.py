# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.


from eventdata.parameter_sources.elasticlogs_bulk_source import ElasticlogsBulkSource
from eventdata.parameter_sources.metricbeat_bulk_source import MetricbeatBulkSource
from eventdata.parameter_sources.elasticlogs_kibana_source import ElasticlogsKibanaSource
from eventdata.parameter_sources.metricbeat_kibana_source import MetricbeatKibanaSource
from eventdata.parameter_sources.interval_query_source import IntervalQuerySource
from eventdata.runners import deleteindex_runner
from eventdata.runners import fieldstats_runner
from eventdata.runners import indicesstats_runner
from eventdata.runners import kibana_runner
from eventdata.runners import nodestorage_runner
from eventdata.runners import rollover_runner
from eventdata.schedulers import utilization_scheduler


def register(registry):
    registry.register_param_source("elasticlogs_bulk", ElasticlogsBulkSource)
    registry.register_param_source("metricbeat_bulk", MetricbeatBulkSource)
    registry.register_param_source("elasticlogs_kibana", ElasticlogsKibanaSource)
    registry.register_param_source("metricbeat_kibana", MetricbeatKibanaSource)
    registry.register_param_source("interval_query", IntervalQuerySource)
    registry.register_runner("delete_indices", deleteindex_runner.deleteindex)
    registry.register_runner("fieldstats", fieldstats_runner.fieldstats)
    registry.register_runner("indicesstats", indicesstats_runner.indicesstats)
    registry.register_runner("kibana", kibana_runner.kibana)
    registry.register_runner("node_storage", nodestorage_runner.nodestorage)
    registry.register_runner("rollover", rollover_runner.rollover)
    registry.register_scheduler("utilization", utilization_scheduler.UtilizationBasedScheduler)
