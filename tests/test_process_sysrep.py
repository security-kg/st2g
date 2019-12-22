import os
import pytest
from functools import reduce


class TestSysrep:
    sysrep_path = reduce(os.path.join, ['.', 'examples', 'data', 'input_only', 'sysrep_exp_data.txt'])
    if not os.path.exists(sysrep_path):
        pytest.skip("skipping tests without sysrep", allow_module_level=True)

    @pytest.fixture
    def sysrep_raw(self):
        with open(TestSysrep.sysrep_path) as fin:
            return fin.read()

    def test_process_sysrep(self, sysrep_raw):
        from pprint import pprint
        from st2g.process import process_raw_text
        result = process_raw_text(sysrep_raw)
        pprint(result['doc_seq'])
        pprint("-------------------------------")
        pprint([{"sent": sent, "ents": sent.ents} for sent in result['doc'].sents])
        pprint("-------------------------------")
        pprint(result['doc']._.svo)
        dot = result['dot']
        dot.render('temp/sysrep.gv')
