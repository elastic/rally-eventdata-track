# rally-eventdata-track

Repository containing a Rally track for simulating event-based data use-cases. The track supports bulk indexing of auto-generated events as well as simulated Kibana queries and a range of management operations to make the track self-contained.

This track can be used as-is, extended or adapted to better match your use case or simply be used as an example of how custom parameter sources and runners can be used to create more complex and realistic simulations and benchmarks.

## Installation

Once Rally has been configured, modify the `rally.ini` file to link to the eventdata track repository:

```
[tracks]
default.url = https://github.com/elastic/rally-tracks
eventdata.url = https://github.com/elastic/rally-eventdata-track

```

The track can be run by specifying the following runtime parameters: 
`    --track=eventdata`
`    --track-repository=eventdata`.

Another option is to download the repository and point to it using the `--track-path` command line parameter.

## Track parameters supported by all challenges

Note: In general, track parameters are only defined for a subset of the challenges so please refer to the documentation of the respective challenge for a list of supported track parameters. Only the parameters documented in the table below are guaranteed to work with all challenges as intended.

| Parameter | Explanation | Type | Default Value |
| --------- | ----------- | ---- | ------------- |
| `index_prefix` | The prefix for generated indices. | `str` |  `elasticlogs` |
| `number_of_shards` | The number primary shards generated indices will have. | `int` | 2 |
| `number_of_replicas` | The number replicas generated indices will have. | `int` | 0 |
| `record_raw_event_size` | Adds a new field `_raw_event_size` to the index which contains the size of the raw logging event in bytes. | `bool` | `False` |
| `query_index_prefix` | Start of the index name(s) used in queries for this track. | `str` | `elasticlogs_q` |
| `query_index_pattern` | Index pattern used in queries for this track. | `str` | `$query_index_prefix + "-*"` |
| `refresh_interval` | [Index refresh interval](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules.html#index-modules-settings) | `str` | `5s` |
| `verbose` | Emits additional debug logs. Enable this only when testing changes but not when running regular benchmarks as this influences performance negatively. | `bool` | `False` |

Note: It is recommended to store any track parameters in a json file and pass them to Rally using `--track-params=./params-file.json`. 

Following is an example of a valid parameters json file:
params-file.json
``` json
{
  "number_of_replicas": 1,
  "number_of_shards": 3
}
```

You can specify what challenge you want to run with the `--challenge=YOUR_CHALLENGE_NAME`

## Available Challenges

### elasticlogs-1bn-load

This challenge indexes 1 billion events into a number of indices of 2 primary shards each, and results in around 200GB of indices being generated on disk. This can vary depending on the environment. It can be used to give an idea of how max indexing performance behaves over an extended period of time.

The table below shows the track parameters that can be adjusted along with default values:

| Parameter | Explanation | Type | Default Value |
| --------- | ----------- | ---- | ------------- |
| `number_of_replicas` | Number of index replicas | `int` | `0` |
| `number_of_shards` | Number of primary shards | `int` | `2` |
| `bulk_indexing_clients` | Number of bulk indexing clients/connections | `int` | `20` |
| `disk_type` | Type of disk used. If disk_type is not `ssd`, a single merge scheduler thread will be specified in the index template | `string` | `ssd` |
| `translog_sync` | If value is not `request`, translog will be configured to use `async` mode | `string` | `request` |
| `rollover_enabled` | Enables the automatic rollover of indices after 100 million entries or 1 day. | `bool` | `true` |

### elasticlogs-querying

This challenge runs mixed Kibana queries against the index created in the **elasticlogs-1bn-load** track. No concurrent indexing is performed.

The table below shows the track parameters that can be adjusted along with default values:

| Parameter | Explanation | Type | Default Value |
| --------- | ----------- | ---- | ------------- |
| `query_time_period` | The period to run the parallel query tasks specified in seconds | `int` | `1800` |

### combined-indexing-and-querying

This challenge assumes that the *elasticlogs-1bn-load* track has been executed as it simulates querying against these indices. It shows how indexing and querying through simulated Kibana dashboards can be combined to provide a more realistic benchmark.

In this challenge rate-limited indexing at varying levels is combined with a fixed level of querying. If metrics from the run are stored in Elasticsearch, it is possible to analyse these in Kibana in order to identify how indexing rate affects query latency and vice versa.

The table below shows the track parameters that can be adjusted along with default values:

| Parameter | Explanation | Type | Default Value |
| --------- | ----------- | ---- | ------------- |
| `number_of_replicas` | Number of index replicas | `int` | `0` |
| `number_of_shards` | Number of primary shards | `int` | `2` |
| `bulk_indexing_clients` | Number of bulk indexing clients/connections | `int` | `24` |
| `disk_type` | Type of disk used. If disk_type is not `ssd`, a single merge scheduler thread will be specified in the index template | `string` | `ssd` |
| `translog_sync` | If value is not `request`, translog will be configured to use `async` mode | `string` | `request` |
| `rate_limit_duration_secs` | Duration in seconds for each rate limited benchmark rate_limit_step | `int` | `1200` |
| `rate_limit_step` | Number of requests per second to use as a rate_limit_step. `2` indicates rate limiting will increase in steps of 2k EPS | `int` | `2` |
| `rate_limit_max` | Maximum number of requests per second to use for rate-limiting. `32` indicates a top target indexing rate of 32k EPS | `int` | `32` |

### elasticlogs-continuous-index-and-query

This challenge is suitable for long term execution and runs in two phases. Both phases (`p1`, `p2`) index documents containing auto-generated events, however, `p1` indexes events at the max possible speed, whereas `p2` throttles indexing to a specified rate and in parallel executes four queries simulating Kibana dashboards and queries. The created index gets rolled over after the configured max size. The maximum amount of rolled over indices are also configurable.

The table below shows the track parameters that can be adjusted along with default values:

| Parameter | Explanation | Type | Default Value |
| --------- | ----------- | ---- | ------------- |
| `number_of_replicas` | Number of index replicas | `int` | `0` |
| `number_of_shards` | Number of primary shards | `int` | `2` |
| `p1_bulk_indexing_clients` | Number of [clients](https://esrally.readthedocs.io/en/stable/track.html?highlight=number%20of%20clients#schedule) used to index during phase 1 | `int` | `40` |
| `p1_bulk_size` | The [build-size](https://esrally.readthedocs.io/en/stable/track.html?highlight=number%20of%20clients#bulk) for the autogenerated events during phase 1 | `int` | `1000` |
| `p1_duration_secs` | Duration of phase 1 execution in sec | `int` | `7200` |
| `p2_bulk_indexing_clients` | Number of [clients](https://esrally.readthedocs.io/en/stable/track.html?highlight=number%20of%20clients#schedule) used to index during phase 2 | `int` | `16` |
| `p2_bulk_size` | The [build-size](https://esrally.readthedocs.io/en/stable/track.html?highlight=number%20of%20clients#bulk) for the autogenerated events during phase 2 | `int` | `1000` |
| `p2_ops` | Number of bulk indexing ops/s for phase 2. A value of `10` with `p2_bulk_size=10` throttles indexing to 10000 docs/s | `int` | `10` |
| `rollover_max_size` | Max index size condition for [rollover API](https://www.elastic.co/guide/en/elasticsearch/reference/master/indices-rollover-index.html#indices-rollover-index) | `str` | `30gb` |
| `rollover_max_age` | Max age condition for [rollover API](https://www.elastic.co/guide/en/elasticsearch/reference/master/indices-rollover-index.html#indices-rollover-index) | `str` | `1d` |
| `p2_query1_target_interval` | Frequency of execution (every N sec) of Kibana query: `kibana-traffic-country-dashboard_60m` | `int` | `30` |
| `p2_query2_target_interval` | Frequency of execution (every N sec) of Kibana query: `kibana-discover_30m` | `int` | `30` |
| `p2_query3_target_interval` | Frequency of execution (every N sec) of Kibana query: `kibana-traffic-dashboard_30m` | `int` | `30` |
| `p2_query4_target_interval` | Frequency of execution (every N sec) of Kibana query: `kibana-content_issues-dashboard_30m"` | `int` | `30` |
| `max_rolledover_indices` | Max amount of recently rolled over indices to retain | `int` | `20` |
| `rolledover_indices_suffix_separator` | Separator for extracting suffix to help determining which rolled-over indices to delete  | `str` | `-` |

The indices use the alias `elasticlogs_q_write` (assuming the default value for `query_index_prefix`) and start with `elasticlogs_q-000001`. As an example, for a cluster with rolled over indices:  `elasticlogs-000001`, `elasticlogs-000002`, ... `000010` a value of `max_rolledover_indices=8` results to the removal of `elasticlogs-000001` and `elasticlogs-000002`.

A value of `max_rolledover_indices=20` on a three node bare-metal cluster with the following specifications:

  * CPU: Intel(R) Core(TM) i7-6700 CPU @ 3.40GHz
  * RAM: 32 GB
  * SSD: 2 x Crucial MX200 in RAID-0 configuration
  * OS: Linux Kernel version 4.13.0-38
  * OS tuning:
    * Turbo boost disabled (`/sys/devices/system/cpu/intel_pstate/no_turbo`)
    * THP at default `madvise` (`/sys/kernel/mm/transparent_hugepage/{defrag,enabled}`)
  * JVM: Oracle JDK 1.8.0_131

ends up consuming a constant of `407GiB` per node.

The following is an example of configurable parameters for this challenge.

params-file.json 
``` json
{
  "number_of_replicas": 1,
  "number_of_shards": 3,
  "p1_bulk_indexing_clients": 32,
  "p1_bulk_size": 1000,
  "p1_duration_secs": 28800,
  "p2_bulk_indexing_clients": 12,
  "p2_bulk_size": 1000,
  "p2_ops": 30,
  "max_rolledover_indices": 20,
  "rollover_max_size": "30gb"
}
```

### index-logs-fixed-daily-volume

This challenge indexes a fixed (raw) logging volume of logs per day into daily indices. This challenge will complete tasks as quickly as possible and won't take the amount of days specified in the number_of_days field.  The table below shows the track parameters that can be adjusted along with default values:

| Parameter               | Explanation                                                                                                                            | Type  | Default Value         |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----- | --------------------- |
| `bulk_indexing_clients` | Number of bulk indexing clients/connections                                                                                            | `int` | `8`                   |
| `bulk_size`             | Number of documents to send per bulk                                                                                                   | `int` | `1000`                |
| `daily_logging_volume`  | The raw logging volume. Supported units are bytes (without any unit), `KB`, `MB` and `GB`). For the value, only integers are allowed.  | `str` | `100GB`               |
| `starting_point`        | The first timestamp for which logs should be generated.                                                                                | `str` | `2018-05-01:00:00:00` |
| `number_of_days`        | The number of simulated days for which data should be generated.                                                                       | `int` | `24`                  |
| `number_of_shards`      | Number of primary shards                                                                                                               | `int` | `3`                   |

### index-and-query-logs-fixed-daily-volume

Indexes several days of logs with a fixed (raw) logging volume per day and running queries concurrently. Requires executing `index-logs-fixed-daily-volume` first. This challenge will complete tasks as quickly as possible and won't take into account the amount of days specified in the number_of_days field. The table below shows the track parameters that can be adjusted along with default values:

| Parameter               | Explanation                                                                                                                            | Type  | Default Value         |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----- | --------------------- |
| `bulk_indexing_clients` | Number of bulk indexing clients/connections                                                                                            | `int` | `8`                   |
| `search_clients`        | Number of search clients/connections used by *each** query                                                                             | `int` | `1`                   |
| `bulk_size`             | Number of documents to send per bulk                                                                                                   | `int` | `1000`                |
| `daily_logging_volume`  | The raw logging volume. Supported units are bytes (without any unit), `KB`, `MB` and `GB`). For the value, only integers are allowed.  | `str` | `100GB`               |
| `starting_point`        | The first timestamp for which logs should be generated.                                                                                | `str` | `2018-05-25 00:00:00` |
| `number_of_days`        | The number of simulated days for which data should be generated.                                                                       | `int` | `6`                   |

### index-fixed-load-and-query

Indexes (several days of) logs at a fixed target throughput using a fixed (raw) logging volume per day while running queries concurrently.  Requires executing `index-logs-fixed-daily-volume` first. This challenge will end as soon the indexing task has completed. The table below shows the track parameters that can be adjusted along with default values:

| Parameter                    | Explanation                                                                                                                            | Type  | Default Value         |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----- | --------------------- |
| `bulk_indexing_reqs_per_sec` | Number of bulk indexing requests/sec. Multiply this by bulk_size to understand indexing throughput in docs/s.                          | `int` | `20`                  |                                                    
| `bulk_size`                  | Number of documents to send per bulk                                                                                                   | `int` | `1000`                |
| `bulk_indexing_clients`      | Number of bulk indexing clients/connections                                                                                            | `int` | `8`                   |
| `search_clients`             | Number of search clients/connections used by *each** query                                                                             | `int` | `1`                   |
| `daily_logging_volume`       | The raw logging volume. Supported units are bytes (without any unit), `KB`, `MB` and `GB`). For the value, only integers are allowed.  | `str` | `100GB`               |
| `starting_point`             | The first timestamp for which logs should be generated.                                                                                | `str` | `2018-05-25 00:00:00` |
| `number_of_days`             | The number of simulated days for which data should be generated.                                                                       | `int` | `6`                   |


### query-searchable-snapshot

This challenge can be used to evaluate the performance of [searchable snapshots](https://www.elastic.co/guide/en/elasticsearch/reference/7.10/searchable-snapshots.html). It assumes that an appropriately sized snapshot has already been prepared. It then [mounts a snapshot](https://www.elastic.co/guide/en/elasticsearch/reference/current/searchable-snapshots-api-mount-snapshot.html) so it is searchable and runs queries against it.

| Parameter                                              | Explanation                                                                                                                 | Type   | Default Value |
|--------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|--------|---------------|
| `es_snapshot_repo_name`                                | The name of the snapshot repository from which the snapshot should be mounted.                                              | `str`  | -             |
| `es_snapshot_repo_type`                                | The type of the snapshot repository from which the snapshot should be mounted.                                              | `str`  | -             |
| `es_snapshot_repo_settings`                            | [Snapshot repository settings](https://www.elastic.co/guide/en/elasticsearch/reference/current/put-snapshot-repo-api.html). | `dict` | `{}`          |
| `es_snapshot_name`                                     | The name of the snapshot that should be mounted. All available indices will be mounted with their original name.            | `str`  | -             |
| `query_time_period`                                    | The period to run the parallel query tasks specified in seconds.                                                            | `int` | `1800`         |
| `query_searchable_snapshot_content_issues_50_interval` | Time to wait in seconds between requests to the content issues dashboard covering 50% of the time range.                    | `int` | `30`           |
| `query_searchable_snapshot_content_issues_75_interval` | Time to wait in seconds between requests to the content issues dashboard covering 75% of the time range.                    | `int` | `90`           |
| `query_searchable_snapshot_traffic_50_interval`        | Time to wait in seconds between requests to the traffic dashboard.                                                          | `int` | `40`           |
| `query_searchable_snapshot_discover_50_interval`       | Time to wait in seconds between requests to the discover view.                                                              | `int` | `60`           |

### bulk-update

Index documents into an elasticlogs index. IDs are sequential and 40% are updates, with a uniform ID bias. The table below shows the track parameters that can be adjusted along with default values:

| Parameter                  | Explanation                                 | Type  | Default Value              |
| -------------------------- | --------------------------------------------| ----- | -------------------------- |
| `number_of_replicas`       | Number of index replicas                    | `int` | `0`                        |
| `number_of_shards`         | Number of primary shards                    | `int` | `2`                        |
| `bulk_size`                | Number of documents to send per bulk        | `int` | `1000`                     |
| `bulk_indexing_iterations` | How many requests to send in total          | `int` | `1000000`                  |
| `bulk_indexing_clients`    | Number of bulk indexing clients/connections | `int` | `20`                       |
| `target_throughput`        | Targeted throughput in requests per second  | `int` |  not set, i.e. unthrottled |

## Custom parameter sources

### elasticlogs\_bulk\_source

This parameter source generates bulk indexing requests filled with auto-generated data. This data is generated based on statistics from a subset of real traffic to the elastic.co website. Data has been anonymised and post-processed and is modelled on the format used by the Filebeat Nginx Module.

The generator allows data to be generated in real-time or against a set date/tine interval. A sample event will contain the following fields:

``` json
{
  "@timestamp": "2017-06-01T00:01:08.866644Z",
  "offset": 7631775,
  "user_name": "-",
  "source": "/usr/local/var/log/nginx/access.log",
  "fileset": {
    "module": "nginx",
    "name": "access"
  },
  "input": {
    "type": "log"
  },
  "beat": {
    "version": "6.3.0",
    "hostname": "web-EU-1.elastic.co",
    "name": "web-EU-1.elastic.co"
  },
  "prospector": {
    "type": "log"
  },
  "nginx": {
    "access": {
      "user_agent": {
        "major": "44",
        "os": "Mac OS X",
        "os_major": "10",
        "name": "Firefox",
        "os_name": "Mac OS X",
        "device": "Other"
      },
      "remote_ip": "5.134.208.0",
      "remote_ip_list": [
        "5.134.208.0"
      ],
      "geoip": {
        "continent_name": "Europe",
        "city_name": "Grupa",
        "country_name": "Poland",
        "country_iso_code": "PL",
        "location": {
          "lat": 53.5076,
          "lon": 18.6358
        }
      },
      "referrer": "https://www.elastic.co/guide/en/marvel/current/getting-started.html",
      "url": "/guide/en/kibana/current/images/autorefresh-pause.png",
      "body_sent": {
        "bytes": 2122
      },
      "method": "GET",
      "response_code": "200",
      "http_version": "1.1"
    }
  }
}
```

### elasticlogs\_kibana\_source

This parameter source supports simulating three different types of dashboards. One of the following needs to be selected by specifying the mandatory parameter `dashboard`:

**traffic** - This dashboard contains 7 visualisations and presents different types of traffic statistics. In structure it is similar to the `Nginx Overview` dashboard that comes with the Filebeat Nginx Module. It does aggregate across all records in the index and is therefore a 'heavy' dashboard.

![Eventdata traffic dashboard](eventdata/dashboards/images/eventdata_traffic_dashboard.png)

**content\_issues** - This dashboard contains 5 visualisations and is designed to be used for analysis of records with a 404 response code, e.g. to find links that are no longer leading anywhere. This only aggregates across a small subset of the records in an index and is therefore a 'light' dashboard.

![Eventdata content issues dashboard](eventdata/dashboards/images/eventdata_content_issues_dashboard.png)

**discover** - This simulates querying data through the `Discover` application in Kibana.

## Extending and adapting

This track can be used as it is, but was designed so that it would be easy to extend or modify it. There are two directories named **operations** and **challenges**, containing files with the standard components of this track that can be used as an example. The main **track.json** file will automatically load all files with a *.json* suffix from these directories. This makes it simple to add new operations and challenges without having to update or modify any of the original files.

## Elasticsearch Compatibility

This track requires Elasticsearch 6.x. Earlier versions are not supported.

## Versioning Scheme

From time to time, setting and mapping formats change in Elasticsearch. As we want to be able to support multiple versions of Elasticsearch, we also need to version track specifications. Therefore, this repository contains multiple branches. The following examples should give you an idea how the versioning scheme works:

- master: tracks on this branch are compatible with the latest development version of Elasticsearch
- 6: compatible with all Elasticsearch 6.x releases.
- 2: compatible with all Elasticsearch releases with the major release number 2 (e.g. 2.1, 2.2, 2.2.1)
- 1.7: compatible with all Elasticsearch releases with the major release number 1 and minor release number 7 (e.g. 1.7.0, 1.7.1, 1.7.2)

As you can see, branches can match exact release numbers but Rally is also lenient in case settings mapping formats did not change for a few releases. Rally will try to match in the following order:

1. major.minor.patch-extension_label (e.g. 6.0.0-alpha2)
2. major.minor.patch (e.g. 6.2.3)
3. major.minor (e.g. 6.2)
4. major (e.g. 6)

Apart from that, the master branch is always considered to be compatible with the Elasticsearch master branch.

To specify the version to check against, add `--distribution-version` when running Rally. If the version is not specified, Rally assumes that you want to benchmark against the Elasticsearch master version.

Example: If you want to benchmark Elasticsearch 6.2.4, run the following command:

```
esrally race --distribution-version=6.2.4
```

How to Contribute
-----------------

If you want to contribute to this track, please ensure that it works against the master version of Elasticsearch (i.e. submit PRs against the master branch). We can then check whether it's feasible to backport the track to earlier Elasticsearch versions.

See all details in the [contributor guidelines](https://github.com/elastic/rally/blob/master/CONTRIBUTING.md).

Running tests
-------------

This track contains associated unit tests. In order to run them, please issue the following commands

```
# only required once for the initial setup
make prereq
make install
# to run the tests
make test
```

It also contains an integration test suite that can be run with `make it`.

License
-------

This software is licensed under the Apache License, version 2 ("ALv2"), quoted below.

Copyright 2015-2019 Elasticsearch <https://www.elastic.co>

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
