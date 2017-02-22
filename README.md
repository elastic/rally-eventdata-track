# rally-eventdata-track

Repository containing a Rally track for simulating event-based data use-cases. The track supports bulk indexing of auto-generated events as well as simulated Kibana queries and a range of management operations to make the track self-contained.

This track can be used as-is, extended or adapted to better match your use case or simply be used as a example of how custom parameter sources and runners can be used to create more complex and realistic simulations and benchmarks.

## Available Challenges

### 1) append-no-conflicts

This is the default challenge, which performs bulk indexing at maximum throughput against a single index for a period of 20 minutes.

### 2) bulk-size-evaluation

This challenge performs bulk-indexing against a single index with varying bulk request sizes, ranging from 125 events/request to 50000 events/request.

### 3) shard-sizing

This challenge indexes 2 million events into an index consisting of a single shard 25 times. After each group of 2 million events has been inserted, 4 different Kibana dashboard configurations are benchmarked against the index. At this time no indexing takes place. There are two different dashboards being simulated, aggregating across 50% and 90% of the data in the shard.

This challenge shows how shard sizing can be performed and how the nature of queries used can impact the results.

### 4) elasticlogs-1bn-load

This challenge indexes 1 billion events into 20 indices of 2 primary shards each, and results in around 200GB of indices being generated on disk. This can vary depending on the environment. It can be used give an idea of how max indexing performance behaves over an extended period of time.

### 5) combined-indexing-and-querying

This challenge assumes that the *elasticlogs-1bn-load* track has been executed as it simulates querying against these indices. It shows how indexing and querying through simulated Kibana dashboards can be combined to provide a more realistic benchmark.

In this challenge rate-limited indexing at varying levels is combined with a fixed level of querying. If metrics from the run are stored in Elasticsearch, it is possible analyse these in Kibana in order to identify how indexing rate affects query latency and vice versa.

## Custom parameter sources

### elasticlogs\_bulk\_source

This parameter source generated bulk indexing requests filled with auto-generated data. This data is generated based on statistics from a subset of real traffic to the elastic.co website. Data has been anonymised and post-processed.

The generator is configurable and allows data to be generated in real-time or against a set date/tine interval. A sample event looks will contain the following fields:

```
{
	"agent": "\"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36\"",
	"useragent": {
		"os": "Windows 7",
		"os_name": "Windows 7",
		"name": "Chrome"
	},
	"geoip": {
		"country_name": "Canada",
		"location": [-79.4167, 43.6667]
	},
	"clientip": "205.210.17.0",
	"referrer": "\"https://www.elastic.co/guide/en/logstash/current/getting-started-with-logstash.html\"",
	"request": "/static/css/token-input.css",
	"bytes": 517,
	"verb": "GET",
	"response": 200,
	"httpversion": "1.1",
	"@timestamp": "2017-02-22T13:09:06.345Z",
	"message": "205.210.17.0 - - [2017-02-22T13:09:06.345Z] \"GET /static/css/token-input.css HTTP/1.1\" 200 517 \"-\" \"https://www.elastic.co/guide/en/logstash/current/getting-started-with-logstash.html\" \"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36\""
}
```

### elasticlogs\_kibana\_source

This parameter source supports simulating two different types of dashboards.

**traffic** - This dashboard contains 7 visualisations and presents different types of traffic statistics. It does aggregate across all records and is therefore a quite 'heavy' dashboard.

**content\_issues** - This dashboard contains 6 visualisations and is designed to be used for analysis of records with a 404 response code, e.g. to find dead internal links or external links that are no longer leading anywhere. This only aggregates across a small subset of the records in an index and is therefore considerably 'lighter' than the **traffic** dashboard.

## Extending and adapting

This track can be used as it is, but was designed so that it would be easy to extend or modify it. There are two directories named **operations** and **challenges**, containing files with the standard components of this track that can be used as an example. The main **track.json** file will automatically load all files with a *.json* suffix from these directories. This makes it simple to add new operations and challenges without having to update or modify any of the original files.

## Elasticsearch Compatibility

This track requires Elasticsearch 5.x. Earlier versions are not supported.

## Versioning Scheme

From time to time, setting and mapping formats change in Elasticsearch. As we want to be able to support multiple versions of Elasticsearch, we also need to version track specifications. Therefore, this repository contains multiple branches. The following examples should give you an idea how the versioning scheme works:

- master: tracks on this branch are compatible with the latest development version of Elasticsearch
- 5.0.0-alpha2: compatible with the released version 5.0.0-alpha2.
- 2: compatible with all Elasticsearch releases with the major release number 2 (e.g. 2.1, 2.2, 2.2.1)
- 1.7: compatible with all Elasticsearch releases with the major release number 1 and minor release number 7 (e.g. 1.7.0, 1.7.1, 1.7.2)

As you can see, branches can match exact release numbers but Rally is also lenient in case settings mapping formats did not change for a few releases. Rally will try to match in the following order:

1. major.minor.patch-extension_label (e.g. 5.0.0-alpha5)
2. major.minor.patch (e.g. 2.3.1)
3. major.minor (e.g. 2.3)
4. major (e.g. 2)

Apart from that, the master branch is always considered to be compatible with the Elasticsearch master branch.

To specify the version to check against, add `--distribution-version` when running Rally. It it is not specified, Rally assumes that you want to benchmark against the Elasticsearch master version. 

Example: If you want to benchmark Elasticsearch 5.1.1, run the following command:

```
esrally --distribution-version=5.1.1
```

How to Contribute
-----------------

If you want to contribute to this track, please ensure that it works against the master version of Elasticsearch (i.e. submit PRs against the master branch). We can then check whether it's feasible to backport the track to earlier Elasticsearch versions.
 
See all details in the [contributor guidelines](https://github.com/elastic/rally/blob/master/CONTRIBUTING.md).

License
-------
 
This software is licensed under the Apache License, version 2 ("ALv2"), quoted below.

Copyright 2015-2017 Elasticsearch <https://www.elastic.co>

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
