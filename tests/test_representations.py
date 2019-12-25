import os
import random
import pytest
from functools import reduce
from pprint import pprint
import st2g.representations as rep


class Test_TC:
    text_path = reduce(os.path.join, ['.', 'examples', 'data', 'TC', 'TC3.3.input.txt'])
    text_path = reduce(os.path.join, ['.', 'examples', 'data', 'demo', '1.txt'])
    if not os.path.exists(text_path):
        pytest.skip("skipping tests without TC", allow_module_level=True)

    @pytest.fixture
    def text_raw(self):
        with open(Test_TC.text_path) as fin:
            return fin.read()

    def test_load_TC(self, text_raw):
        print()
        print("-"*30+" Original "+"-"*30)
        print(text_raw)

    def test_parse_block(self, text_raw):
        blocks = rep.contentToBlocks(text_raw)
        print()
        print(("-"*60+"\n").join(blocks))

    def test_NER_5(self, text_raw):
        blocks = rep.contentToBlocks(text_raw)
        print()
        for _ in range(5):
            some_block = random.choice(blocks)
            print("-"*30+" Original Block "+"-"*30)
            print(('|'+' '*9)*(len(some_block) // 10 + 1))
            print(some_block)
            print("-"*30+" NER result "+"-"*30)
            ne = rep.runNERinBlock(some_block)
            pprint(ne)

    def test_replacement(self, text_raw):
        blocks = rep.contentToBlocks(text_raw)
        # some_block = random.choice(blocks)
        some_block = blocks[0]
        ne = rep.runNERinBlock(some_block)
        new_block, rr = rep.replaceSpanUsingNE(some_block, ne)
        print("-"*30+" Original Block "+"-"*30)
        print(('|'+' '*9)*(len(some_block) // 10 + 1))
        print(some_block)
        print("-"*30+" NER result "+"-"*30)
        pprint(ne)
        print("-"*30+" Replacement result "+"-"*30)
        print(('|'+' '*9)*(len(new_block) // 10 + 1))
        print(new_block)
        print("-"*30+" Replacement record "+"-"*30)
        pprint(rr)

    def test_sentence_seg(self, text_raw):
        blocks = rep.contentToBlocks(text_raw)
        # some_block = random.choice(blocks)
        some_block = blocks[0]
        ne = rep.runNERinBlock(some_block)
        new_block, rr = rep.replaceSpanUsingNE(some_block, ne)
        print("-"*30+" Original Block "+"-"*30)
        print(('|'+' '*9)*(len(some_block) // 10 + 1))
        print(some_block)
        print("-"*30+" Processing "+"-"*30)
        print("len: ", len(new_block))
        sents = rep.blockToSentences(new_block)
        print([len(s) for s in sents])
        print("-"*30+" Sents "+"-"*30)
        pprint(sents)