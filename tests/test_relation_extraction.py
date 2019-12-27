import os
import random
import pytest
from typing import List
from functools import reduce
from pprint import pprint
import st2g.representations as rep
import st2g.relation_extraction as rele  # to distinguish from re


class Test_RE:
    text_path = reduce(os.path.join, ['.', 'examples', 'data', 'TC', 'TC3.3.input.txt'])
    text_path = reduce(os.path.join, ['.', 'examples', 'data', 'demo', '2.txt'])
    text_path = reduce(os.path.join, ['.', 'examples', 'data', 'TC', 'TC_C_2.txt'])
    if not os.path.exists(text_path):
        pytest.skip("skipping tests without TC", allow_module_level=True)

    @pytest.fixture
    def text_raw(self):
        with open(Test_RE.text_path) as fin:
            return fin.read()

    def test_load_TC(self, text_raw):
        print()
        print("-"*30+" Original "+"-"*30)
        print(text_raw)

    def test_rep_pipeline(self, text_raw):
        print()
        print("-"*30+" Original "+"-"*30)
        print(text_raw)
        print("-"*30+" Processed "+"-"*30)
        result = rep.processContent(text_raw)
        pprint(result)
        dot = rep.visualizeProcessedContent(result)
        dot.render('temp/dp.gv')

    def test_whole_pipeline(self, text_raw):
        print()
        result: List[List[rep.SentTree]] = rep.processContent(text_raw)
        agg_result: List[rep.SentTree] = sum(result, [])
        entities, relations = rele.runRelationExtraction(agg_result)
        print("-" * 30 + " entities " + "-" * 30)
        pprint(entities)
        print("-" * 30 + " relations " + "-" * 30)
        pprint(relations)

    def test_output_behavior_graph(self, text_raw):
        print()
        result: List[List[rep.SentTree]] = rep.processContent(text_raw)
        agg_result: List[rep.SentTree] = sum(result, [])
        entities, relations = rele.runRelationExtraction(agg_result)
        dot = rele.convertEntitiesRelationsIntoDot(entities, relations)
        dot.render('temp/bh.gv')