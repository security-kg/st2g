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
from copy import deepcopy
from spacy.pipeline import EntityRuler
from spacy.tokenizer import Tokenizer
from typing import List, Dict, Tuple, Type, Optional
from graphviz import Digraph

from st2g.util.load_resources import load_ini, load_operations, load_replacements

Span: Type = Tuple[int, int]
NamedEntityType: Type = str
NER_Labels: Type = Dict[NamedEntityType, List[Span]]
ReplacementRecord: Type = Dict[Span, Tuple[str, NamedEntityType]]

TextContent: Type = str
TextBlock: Type = str
Sentence: Type = str
Node: Type = dict
Edge: Type = dict
Nodes: Type = Dict[Span, Node]
Edges: Type = Dict[Tuple[Span, Span], Edge]
SentTree: Type = Tuple[Sentence, Nodes, Edges]

patterns = load_ini(add_pron=False)
operations = load_operations()
replacements = load_replacements()
# SPACY_MODEL = "en_core_web_lg"
SPACY_MODEL = "en_core_web_sm"


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


nlp_NER = spacy.load(SPACY_MODEL)


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
    ret = {k: [] for k in focus}
    l_r_set = set()
    for p in patterns:
        label = p['label']
        if label not in focus:
            continue
        reg = p['pattern'][0]['TEXT']['REGEX']
        for match in re.finditer(reg, block):
            _l, _r = match.span()
            overlap = False
            for l, r in l_r_set:
                if l <= _l <= r or l <= _r <= r:
                    overlap = True
                    break
            if overlap:
                continue
            l_r_set.add(match.span())
            ret[label].append((match.span()))
    for k in ret.keys():
        ret[k] = sorted(ret[k])
    return ret


def replaceSpanUsingNE(block: TextBlock, ne: NER_Labels) -> Tuple[TextBlock, ReplacementRecord]:
    # Dict[Span, Tuple[str, NamedEntityType]]: new span -> (old string, ne type)
    to_be_replaced = {}
    for k, target_word in replacements.items():
        if k not in ne:
            continue  # wrong entry in replacements
        spans = ne[k]
        for s in spans:
            to_be_replaced[s] = (target_word, block[s[0]:s[1]], k)
    # replace part by part
    new_block: TextBlock = ""
    rr = {}
    cur = 0
    for l, r in sorted(to_be_replaced.keys()):
        target_word, old_text, ne_type = to_be_replaced[(l, r)]
        if cur < l:
            new_block = new_block + block[cur: l]
        cur = r
        rr[len(new_block), len(new_block)+len(target_word)] = (old_text, ne_type)
        new_block = new_block + target_word
    if cur < len(block):
        new_block = new_block + block[cur:]
    return new_block, rr


# blockToSentence Init
nlp_bts_dep = spacy.load(SPACY_MODEL)


def blockToSentences(block: TextBlock) -> List[Sentence]:
    doc = nlp_bts_dep(block)
    # debug
    total_len = 0
    ret = []
    for s in doc.sents:
        l, r = s.doc[s.start].idx, (s.doc[s.end-1].idx+len(s.doc[s.end-1]))
        assert l >= total_len
        if l > total_len:
            ret.append(block[total_len:l])
        ret.append(block[l: r])
        total_len = r
    if len(block) > total_len:
        ret.append(block[total_len:])
    return ret


def findCorefs(trees: List[SentTree], start_idx) -> None:
    last_subj = None
    for tree_idx, tree in enumerate(trees):
        sent, nodes, edges = tree
        for span in sorted(nodes.keys()):
            v = nodes[span]
            if "is_pron" in v:  # need resolve
                subj, obj = None, None
                current = span
                while subj is None and current is not None:
                    # check next level
                    for (src, des), ev in edges.items():  # possible improvement: edge saved in nodes
                        if src == current:
                            if 'subj' in ev.get('dep') and des[0] < src[0] and 'ioc' in nodes[des]:
                                subj = des
                                break
                            if 'obj' in ev.get('dep') and des[0] < src[0] and 'ioc' in nodes[des]:
                                obj = des
                    if obj is not None:
                        # should we accept it?
                        pass
                    # go to previous level
                    has_father = False
                    for (src, des), ev in edges.items():  # possible improvement: cache the father
                        if des == current:
                            current = src
                            has_father = True
                            break
                    if not has_father:
                        break
                if subj is None and obj is None:
                    v['resolved'] = last_subj  # if None, then fail
                else:
                    if obj is not None and subj is None:
                        # should we use obj instead?
                        subj = obj
                    last_subj = (tree_idx+start_idx, subj)
                    v['resolved'] = (tree_idx+start_idx, subj)
            if "ioc" in v:
                subj = False
                obj = False
                current = span
                while current is not None and not subj:
                    has_father = False
                    for (src, des), ev in edges.items():  # possible improvement: cache the father
                        if des == current:
                            if "subj" in ev.get("dep"):
                                subj = True
                            if "obj" in ev.get("dep"):
                                obj = True
                            current = src
                            has_father = True
                            break
                    if not has_father:
                        break
                if subj or (obj and last_subj is None):
                    last_subj = (tree_idx+start_idx, span)


def parseDependency(sent: Sentence) -> SentTree:
    doc = nlp_bts_dep(sent)
    nodes: Nodes = {}
    edges: Edges = {}
    get_token_l_r = lambda token: (token.idx, token.idx + len(token))
    for token in doc:
        l, r = get_token_l_r(token)
        nodes[(l, r)] = {"dep_text": token.text}
        if token.pos_ == "PRON" and token.is_alpha \
                and token.tag_ not in ['PRP$', 'WDT'] \
                and token.text.lower() not in ["he", "she"]:
            # we don't want procession like "their" so we ruled out certain tags
            nodes[(l, r)]["is_pron"] = True
            nodes[(l, r)]["tag"] = token.tag_
        ancestors = list(token.ancestors)
        if not ancestors:  # root node
            continue
        father = get_token_l_r(ancestors[0])
        edges[(father, (l, r))] = {"dep": token.dep_}
    return sent, nodes, edges


def restoreReplacement(tree: SentTree, rr: ReplacementRecord) -> SentTree:
    sent, nodes, edges = tree
    new_sent = ""
    cur = 0
    replacement_nodes = {}
    all_node_keys = sorted(nodes.keys())
    current_node = 0
    offset = 0
    for span in sorted(rr.keys()):
        l, r = span
        assert r <= len(sent)
        while current_node < len(all_node_keys) and all_node_keys[current_node][0] < l:
            if all_node_keys[current_node] in replacement_nodes:
                current_node += 1
                continue
            else:
                _l, _r = all_node_keys[current_node]
                replacement_nodes[(_l, _r)] = ((_l+offset, _r+offset), None)
                current_node += 1
        ori_text, type = rr[span]
        assert cur <= l
        if cur < l:
            new_sent = new_sent + sent[cur: l]
        cur = r
        new_l = len(new_sent)
        new_sent = new_sent + ori_text
        new_r = len(new_sent)
        replacement_nodes[(l, r)] = ((new_l, new_r), type)
        # TODO: if there is a node that covers both side of this one, this is a fix for things like something%
        offset = new_r - r
    while current_node < len(all_node_keys):
        if all_node_keys[current_node] in replacement_nodes:
            current_node += 1
            continue
        else:
            _l, _r = all_node_keys[current_node]
            replacement_nodes[(_l, _r)] = ((_l + offset, _r + offset), None)
            current_node += 1

    if cur < len(sent):
        new_sent = new_sent + sent[cur: len(sent)]
    new_nodes: Nodes = {}
    for k, v in nodes.items():
        if k in replacement_nodes:
            k, type = replacement_nodes[k]
            v = deepcopy(v)
            if type is not None:
                v['ioc'] = type
                v.pop('is_pron')
        v['text'] = new_sent[k[0]: k[1]]
        new_nodes[k] = v
    new_edges: Edges = {}
    for (src, des), v in edges.items():
        if src in replacement_nodes:
            src = replacement_nodes[src][0]
        if des in replacement_nodes:
            des = replacement_nodes[des][0]
        new_edges[(src, des)] = deepcopy(v)
    return new_sent, new_nodes, new_edges


def labelVerbs(tree: SentTree,
               protect_IOC: bool=True,
               ne: Optional[NER_Labels]=None,
               offset: int=0,
               ops: List[str]=operations) -> SentTree:
    sent, nodes, edges = tree
    new_sent, new_nodes, new_edges = sent, {}, deepcopy(edges)
    doc = nlp_bts_dep(sent)
    lemmat = {}
    for token in doc:
        lemmat[token.text] = token.lemma_
    for k, v in nodes.items():
        l, r = k
        v = deepcopy(v)
        if new_sent[l: r] in lemmat:
            v['lemma'] = lemmat[new_sent[l: r]]
            if v['lemma'] in ops:
                v['is_valid_op'] = True
        if not protect_IOC:
            # label IOCs
            v['text'] = sent[l: r]
            for ioc_type, spans in ne.items():
                for span in spans:
                    if span == (l+offset, r+offset):
                        v['ioc'] = ioc_type
        new_nodes[k] = v
    return new_sent, new_nodes, new_edges


def simplifyTree(tree: SentTree) -> SentTree:
    sent, nodes, edges = tree
    node_useful = set()
    ioc_exist = False
    for span, v in nodes.items():
        if "ioc" in v or "is_pron" in v:
            ioc_exist = True
        if "is_pron" in v or "is_valid_op" in v or "ioc" in v:
            node_useful.add(span)
            current = span
            while current is not None:  # reserve the whole chain
                has_father = False
                for (src, des), ev in edges.items():
                    if des == current:
                        node_useful.add(src)
                        current = src
                        has_father = True
                        break
                if not has_father:
                    break
    new_sent, new_nodes, new_edges = sent, {}, {}
    if not ioc_exist:
        return new_sent, new_nodes, new_edges
    for span, v in nodes.items():
        if span not in node_useful:
            continue
        new_nodes[span] = deepcopy(v)
    for (src, des), v in edges.items():
        if src not in node_useful or des not in node_useful:
            continue
        new_edges[(src, des)] = deepcopy(v)
    return new_sent, new_nodes, new_edges


def processSentence(
        sent: Sentence,
        rr: Optional[ReplacementRecord],
        protect_IOC: bool=True,
        ne: Optional[NER_Labels]=None,
        offset: int=0) -> SentTree:
    # dependency parsing
    tree = parseDependency(sent)
    # replacement restore
    if protect_IOC:
        new_tree = restoreReplacement(tree, rr)
    else:
        new_tree = tree
    # verb labeling
    new_tree = labelVerbs(new_tree, protect_IOC, ne, offset)
    new_tree = simplifyTree(new_tree)
    return new_tree


def processBlock(block: TextBlock, start_idx: int, protect_IOC: bool=True) -> List[SentTree]:
    ne: NER_Labels = runNERinBlock(block)
    if protect_IOC:
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
            current_rr[(start-sent_start, end-sent_start)] = rr[span]
        while len(rr_for_sent) < len(sentences):
            rr_for_sent.append(current_rr)
            current_rr = {}
        assert len(rr_for_sent) == len(sentences)
        ret = []
        for sent, rr in zip(sentences, rr_for_sent):
            ret.append(processSentence(sent, rr, protect_IOC, ne))
    else:
        sentences: List[Sentence] = blockToSentences(block)
        ret = []
        offset = 0
        for sent in sentences:
            ret.append(processSentence(sent, None, protect_IOC, ne, offset=offset))
            offset += len(sent)
    findCorefs(ret, start_idx)  # annotate in the trees
    return ret


def processContent(text_input: TextContent, protect_IOC: bool=True) -> List[List[SentTree]]:
    blocks: List[TextBlock] = contentToBlocks(text_input)
    ret = []
    start_idx = 0
    for block in blocks:
        ret.append(processBlock(block, start_idx, protect_IOC))
        start_idx += len(ret[-1])
    return ret

FONT_SIZE = str(14)

def visualizeProcessedContent(result: List[List[SentTree]]) -> Digraph:
    dot = Digraph(comment="Dependency Parsing", format='svg')
    all_sent_tree = sum(result, [])
    span_to_name = lambda idx, span: "[{}]".format(idx) + str(span[0])+"_"+str(span[1])
    for idx, tree in enumerate(all_sent_tree):
        sent, nodes, edges = tree
        for k, v in nodes.items():
            display = v.get('text', 'NOTEXT')
            if 'ioc' in v:
                display += "|" + v['ioc']
            if 'is_pron' in v:
                display += "|PN"
                if v.get("resolved") is not None:
                    dot.edge(span_to_name(idx, k), span_to_name(v['resolved'][0], v['resolved'][1]), xlabel="ref", style='dotted', fontsize=FONT_SIZE)
            if 'is_valid_op' in v:
                display += "|OP"
            if "|OP" in display:
                dot.node(span_to_name(idx, k), display, style='filled', fillcolor='grey', fontsize=FONT_SIZE)
            elif "|PN" in display or 'ioc' in v:
                dot.node(span_to_name(idx, k), display, style='filled', fillcolor='gold', fontsize=FONT_SIZE)
            else:
                dot.node(span_to_name(idx, k), display, fontsize=FONT_SIZE)
        for (src, des), v in edges.items():
            dot.edge(span_to_name(idx, src), span_to_name(idx, des), xlabel=v.get('dep', "NODEP"), fontsize=FONT_SIZE)
    return dot