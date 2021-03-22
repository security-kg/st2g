import os
import pytest
from functools import reduce


class TestDummy:
    dummy_path = reduce(os.path.join, ['.', 'examples', 'data', 'input_only', 'dummy2.txt'])

    @pytest.fixture
    def dummy_raw(self):
        return "Outlook.exe downloads Video.zip. Video.zip self-extracts to Flash_Movie.exe. " \
               "Flash_Movie.exe drops Monkeys.exe and Player.exe under %temp%. " \
               "It first launches Monkeys.exe. It then launches Player.exe. " \
               "Player.exe then collects system information. " \
               "A.exe hits B.exe."

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

    def test_new_run_dummy(self, dummy_raw):
        from pprint import pprint
        from st2g.main import processContent, \
            visualizeProcessedContent, \
            runRelationExtraction, \
            convertEntitiesRelationsIntoDot
        result = processContent(dummy_raw)
        dot_dp = visualizeProcessedContent(result)
        agg_result = sum(result, [])
        entities, relations = runRelationExtraction(agg_result)
        dot_er = convertEntitiesRelationsIntoDot(entities, relations)
        pprint("Entities:")
        pprint(entities)
        pprint("Relations:")
        pprint(relations)

    def test_new_run_dummy_no_verb_limit(self, dummy_raw):
        from pprint import pprint
        from st2g.main import processContent, \
            visualizeProcessedContent, \
            runRelationExtraction, \
            convertEntitiesRelationsIntoDot
        result = processContent(dummy_raw, no_verb_limit=True)
        dot_dp = visualizeProcessedContent(result)
        agg_result = sum(result, [])
        entities, relations = runRelationExtraction(agg_result)
        dot_er = convertEntitiesRelationsIntoDot(entities, relations)
        pprint("Entities:")
        pprint(entities)
        pprint("Relations:")
        pprint(relations)
