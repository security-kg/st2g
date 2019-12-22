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
from typing import List, Dict, Tuple, Type
Span: Type = Tuple[int, int]
NamedEntityType: Type = str
NER_Labels: Type = Dict[NamedEntityType, List[Span]]
ReplacementRecord: Type = Dict[Span, str]

TextContent: Type = str
TextBlock: Type = str
Sentence: Type = str


class SentTree:
    pass  # TODO

    def restoreReplacement(self, rr: ReplacementRecord):
        pass  # TODO


def contentToBlocks(content: TextContent) -> List[TextBlock]:
    pass  # TODO


def runNERinBlock(block: TextBlock) -> NER_Labels:
    pass  # TODO


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
