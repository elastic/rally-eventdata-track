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

class MountSearchableSnapshotRunner:
    async def __call__(self, es, params):
        repository_name = params["repository"]
        snapshot_name = params["snapshot"]
        snapshots = await es.snapshot.get(repository_name, snapshot_name)
        for snapshot in snapshots["snapshots"]:
            for index in snapshot["indices"]:
                await es.transport.perform_request(method="POST",
                                                   url=f"/_snapshot/{repository_name}/{snapshot_name}/_mount",
                                                   body={"index": index})
