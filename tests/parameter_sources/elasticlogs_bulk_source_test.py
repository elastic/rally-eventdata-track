from eventdata.parameter_sources.elasticlogs_bulk_source import ElasticlogsBulkSource


class StaticEventGenerator:
    def __init__(self, index, type, doc, at_most=-1):
        self.index = index
        self.type = type
        self.doc = doc
        self.at_most = at_most

    def generate_event(self):
        if self.at_most == 0:
            raise StopIteration()
        self.at_most -= 1
        return self.doc, self.index, self.type


class StaticTrack:
    def __init__(self):
        self.indices = []


def test_generates_a_complete_bulk():
    expected_bulk_size = 10

    generator = StaticEventGenerator(index="elasticlogs", type="_doc", doc='{"location": [-0.1485188,51.5250666]}')
    param_source = ElasticlogsBulkSource(track=StaticTrack(), params={
        "index": "elasticlogs",
        "bulk-size": expected_bulk_size
    }, random_event=generator)
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)

    generated_params = client_param_source.params()
    assert len(generated_params["body"].split("\n")) == 2 * expected_bulk_size
    assert generated_params["action-metadata-present"] is True
    assert generated_params["bulk-size"] == expected_bulk_size


def test_generates_a_bulk_that_ends_prematurely():
    generator = StaticEventGenerator(index="elasticlogs", type="_doc", doc='{"loc": [-0.14851,51.5250]}', at_most=5)
    param_source = ElasticlogsBulkSource(track=StaticTrack(), params={
        "index": "elasticlogs",
        "bulk-size": 10
    }, random_event=generator)
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)

    generated_params = client_param_source.params()
    # the actual bulk size does not matter but instead that the generator stopped prematurely after 5 items
    assert len(generated_params["body"].split("\n")) == 10
    assert generated_params["action-metadata-present"] is True
    assert generated_params["bulk-size"] == 5
