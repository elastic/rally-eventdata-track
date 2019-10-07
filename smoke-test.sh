#!/usr/bin/env bash

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

# fail this script immediately if any command fails with a non-zero exit code
set -e
# Treat unset env variables as an error
set -u
# fail on pipeline errors, e.g. when grepping
set -o pipefail

readonly ES_VERSION=${ES_VERSION:-6.8.0}
# intentionally not tested (at the moment) because these challenges require running a different challenge first against the same cluster:
#
# * frozen-querying (depends on frozen-data-generation)
# * combined-indexing-and-querying (depends on any challenge that has already created elasticlogs-q* indices)
# * elasticlogs-querying (depends on any challenge that has already created elasticlogs-q* indices)

readonly CHALLENGES=(elasticlogs-continuous-index-and-query document_id_evaluation bulk-update shard-sizing frozen-data-generation index-logs-fixed-daily-volume refresh-interval max-indexing-querying index-and-query-logs-fixed-daily-volume shard-size-on-disk bulk-size-evaluation bulk-size-evaluation-mini bulk-size-concurrency-evaluation generate-historic-data large-shard-sizing large-shard-id-type-evaluation elasticlogs-1bn-load)

esrally list tracks --track-repository=eventdata

for challenge in "${CHALLENGES[@]}"
do
    esrally --test-mode --distribution-version=$ES_VERSION --track-repository=eventdata --track=eventdata --track-params="bulk_indexing_clients:1,number_of_replicas:0,daily_logging_volume:1MB" --challenge="${challenge}" --on-error=abort
done



