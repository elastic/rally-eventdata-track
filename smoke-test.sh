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

readonly RACE_ID=$(uuidgen)
readonly ES_VERSION=${ES_VERSION:-7.3.0}

# the order matters here as later challenges might expect that some indices already exist that have been created by challenges running earlier. In particular, these challenges are affected:
#
# * frozen-querying (depends on frozen-data-generation)
# * combined-indexing-and-querying (depends on any challenge that has already created elasticlogs-q* indices)
# * elasticlogs-querying (depends on any challenge that has already created elasticlogs-q* indices)
readonly CHALLENGES=(frozen-data-generation frozen-querying elasticlogs-continuous-index-and-query bulk-update index-logs-fixed-daily-volume index-and-query-logs-fixed-daily-volume index-fixed-load-and-query elasticlogs-1bn-load combined-indexing-and-querying elasticlogs-querying)

INSTALL_ID=-1

function log {
    local ts=$(date -u "+%Y-%m-%dT%H:%M:%SZ")
    echo "[${ts}] [${1}] ${2}"
}

function info {
    log "INFO" "${1}"
}

function set_up {
  info "preparing cluster"
  INSTALL_ID=$(esrally install --quiet --distribution-version="${ES_VERSION}" --node-name="rally-node-0" --network-host="127.0.0.1" --http-port=39200 --master-nodes="rally-node-0" --seed-hosts="127.0.0.1:39300" | jq --raw-output '.["installation-id"]')
  esrally start --installation-id="${INSTALL_ID}" --race-id="${RACE_ID}"
}

function run_test {
  echo "**************************************** TESTING LIST TRACKS *******************************************"
  esrally list tracks --track-path="${PWD}/eventdata"
  echo "**************************************** TESTING CHALLENGES *******************************************"

  for challenge in "${CHALLENGES[@]}"
  do
      info "Testing ${challenge}"
      esrally race --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --track-path="${PWD}/eventdata" --track-params="bulk_indexing_clients:1,number_of_replicas:0,daily_logging_volume:1MB,rate_limit_max:2,rate_limit_duration_secs:5,p1_bulk_indexing_clients:1,p2_bulk_indexing_clients:1,p1_duration_secs:5,p2_duration_secs:5,verbose:false" --challenge="${challenge}" --on-error=abort
  done
}

function tear_down {
    info "tearing down"
    set +e
    esrally stop --installation-id="${INSTALL_ID}"
    set -e
}

function main {
    set_up
    run_test
}

trap "tear_down" EXIT

main
