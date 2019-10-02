import os
import pytest
from functools import reduce


class TestDummy:
    dummy_path = reduce(os.path.join, ['.', 'examples', 'data', 'input_only', 'dummy2.txt'])
    if not os.path.exists(dummy_path):
        pytest.skip("skipping tests without dummy", allow_module_level=True)

    @pytest.fixture
    def dummy_raw(self):
        with open(TestDummy.dummy_path) as fin:
            return fin.read()

    def test_load_dummy(self, dummy_raw):
        print("Dummy: " + dummy_raw)

    def test_process_dummy(self, dummy_raw):
        from pprint import pprint
        from st2g.process import process_raw_text
        result = process_raw_text(dummy_raw)
        pprint(result['doc_seq'])
        pprint("-------------------------------")
        pprint([{"sent": sent, "ents": sent.ents} for sent in result['doc'].sents])
        pprint("-------------------------------")
        pprint(result['doc']._.svo)
        dot = result['dot']
        dot.render('temp/dummy.gv')

