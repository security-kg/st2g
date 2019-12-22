"""
Text File Content
-- Block Segmentation ->
Text Blocks
-- NER, replacement ->
Text Blocks without IOC
-- sentence segmentation ->
Text Sentences with IOC labels
-- dependency parsing ->
-- tree conversion ->
-- NER, restore ->
List of token trees
-- Coref ->
-- Verb Labeling ->
List of labeled token trees
"""
import re
import spacy
from spacy.pipeline import EntityRuler
from spacy.tokenizer import Tokenizer
from typing import List, Dict, Tuple, Type

from st2g.util.load_resources import load_ini, load_operations

Span: Type = Tuple[int, int]
NamedEntityType: Type = str
NER_Labels: Type = Dict[NamedEntityType, List[Span]]
ReplacementRecord: Type = Dict[Span, Tuple[str, NamedEntityType]]

TextContent: Type = str
TextBlock: Type = str
Sentence: Type = str

patterns = load_ini()
operations = load_operations()


class SentTree:
    pass  # TODO

    def restoreReplacement(self, rr: ReplacementRecord):
        pass  # TODO


def contentToBlocks(content: TextContent) -> List[TextBlock]:
    ret = []
    current = ""
    for line in content.split("\n"):
        current = current + line + "\n"
        if len(line) < 2:
            ret.append(current)
            current = ""
    if len(current) > 1:
        ret.append(current)
    return ret

# init NER tools


nlp_NER = spacy.load('en_core_web_lg')


def custom_tokenizer(nlp):
    """
    Dirty hack targeting tokenizer to make filepath together
    """
    prefix_re = spacy.util.compile_prefix_regex(nlp.Defaults.prefixes)
    suffix_re = spacy.util.compile_suffix_regex(nlp.Defaults.suffixes)
    infix_re = spacy.util.compile_infix_regex(nlp.Defaults.infixes)
    token_match = re.compile(r'(/[^/ ]*)+/?')

    return Tokenizer(nlp.vocab, prefix_search=prefix_re.search,
                     suffix_search=suffix_re.search,
                     infix_finditer=infix_re.finditer,
                     token_match=token_match.match)


nlp_NER.tokenizer = custom_tokenizer(nlp_NER)
ruler_NER = EntityRuler(nlp_NER, overwrite_ents=True)
ruler_NER.add_patterns(patterns)
nlp_NER.add_pipe(ruler_NER)


def runNERinBlock(block: TextBlock,
                  focus=['Pronoun', 'IP', 'Filename', 'WindowsFilepath', 'LinuxFilepath']) -> NER_Labels:
    doc = nlp_NER(block)
    ret = {k: [] for k in focus}
    for entity in doc.ents:
        if entity.label_ not in focus:
            continue
        ret[entity.label_].append((entity.start_char, entity.end_char))
    return ret


def replaceSpanUsingNE(block: TextBlock, ne: NER_Labels) -> Tuple[TextBlock, ReplacementRecord]:
    pass  # TODO


def blockToSentences(block: TextBlock) -> List[Sentence]:
    pass  # TODO


def findCorefs(trees: List[SentTree]) -> None:
    pass  # TODO


def parseDependency(sent: Sentence) -> SentTree:
    pass  # TODO


def labelVerbs(tree: SentTree, operations: List[str]) -> None:
    pass  # TODO


def processSentence(sent: Sentence, rr: ReplacementRecord):
    # dependency parsing
    tree = parseDependency(sent)
    # replacement restore
    tree.restoreReplacement(rr)
    # verb labeling
    labelVerbs(tree)
    return tree


def processBlock(block: TextBlock):
    ne: NER_Labels = runNERinBlock(block)
    new_block, rr = replaceSpanUsingNE(block, ne)
    sentences: List[Sentence] = blockToSentences(new_block)
    # distribute rr into each sentence
    sent_start, sent_end = 0, len(sentences[0])
    rr_for_sent = []
    current_rr = {}
    for span in sorted(rr):
        start, end = span
        assert start >= sent_start
        while start >= sent_end:
            # next sentence
            assert len(rr_for_sent) < len(sentences) - 1
            rr_for_sent.append(current_rr)
            current_rr = {}
            sent_start = sent_end
            sent_end = sent_start + len(sentences[len(rr_for_sent)])
        assert end <= sent_end
        current_rr[(start-sent_start, end-sent_end)] = rr[span]
    rr_for_sent.append(current_rr)  # last sentence
    assert len(rr_for_sent) == len(sentences)
    ret = []
    for sent, rr in zip(sentences, rr_for_sent):
        ret.append(processSentence(sent, rr))
    findCorefs(ret)  # annotate in the trees
    return ret


def processContent(text_input: TextContent):
    blocks: List[TextBlock] = contentToBlocks(text_input)
    ret = []
    for block in blocks:
        ret.append(processBlock(block))
    return ret
