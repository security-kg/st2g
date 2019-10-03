import os
import sys
# import re
from pprint import pprint
from collections import OrderedDict
from uuid import uuid4
from functools import reduce, partial
import configparser
import spacy
from spacy.pipeline import EntityRuler
from spacy.tokens import Doc, Span, Token
from graphviz import Digraph


# -------------------------------------------- init funcs


def load_operations():
    fpath = reduce(os.path.join, ['.', 'src', 'st2g', 'rules', 'operations.cfg'])
    with open(fpath, 'r') as fin:
        operations = fin.readlines()
    return [_.strip() for _ in operations if len(_.strip())]


def load_ini():
    config = configparser.ConfigParser()
    fpath = reduce(os.path.join, ['.', 'src', 'st2g', 'rules', 'patterns.ini'])
    config.read(fpath)
    patterns, defang = {}, {}
    for ind_type in config.sections():
        try:
            ind_pattern = config.get(ind_type, 'pattern')
        except:
            continue
        if ind_pattern:
            # ind_regex = re.compile(ind_pattern)
            patterns[ind_type] = ind_pattern
        try:
            ind_defang = config.get(ind_type, 'defang')  # defang is for dot replacement? need check later
        except:
            continue
        if ind_defang:
            defang[ind_type] = True
    # convert to spacy pattern format
    ret = []
    for k, v in patterns.items():
        cur = {'label': k, 'pattern': [{"TEXT": {"REGEX": v}}]}
        ret.append(cur)
    # add additional entities
    ret.append({'label': "Pronoun", 'pattern': [{"POS": "PRON"}]})
    return ret


# -------------------------------------------- pipeline funcs


def set_custom_boundaries(doc):
    for token in doc[:-1]:
        if token.text == "%":
            doc[token.i + 1].is_sent_start = False
    return doc


def extract_sentence_root(doc, operations=None, pos_tag_check=True):
    """
    Extract core verb from a whole sentence, not considering which s and o that we care
    """
    ret = doc.root
    if operations:  # check if the verb is within that operation list
        if ret.lemma_.lower() not in operations:
            return None
    if pos_tag_check:
        if ret.pos_ not in ['VERB']:
            return None
    return ret


def extract_relation_identifier(doc, s, o, **kwargs):
    # get lca
    v = doc[doc.get_lca_matrix()[s.i - doc.start][o.i - doc.start]]
    if kwargs['operations']:
        if v.lemma_.lower() not in kwargs['operations']:
            return None
    if 'pos_check' not in kwargs or kwargs['pos_check']:
        if v.pos_ not in ['VERB']:
            return None
    if 'order_check' not in kwargs or kwargs['order_check']:  # imperfect
        if o.i > s.i:
            return None
    if 'dep_check' not in kwargs or kwargs['dep_check']:  # defect: dep_ not accurate for NERs
        print(s.dep_, o.dep_)
        if "sub" not in s.dep_ and "mod" not in s.dep_:
            return None
    return v


def svo_extraction(doc, focusing=('Pronoun', 'IP', 'Filename'), threshold=0.9, operations=None):
    """
    three pass coreference resolution + svo extraction
    1. high recall detection
    2. high precision match
    3. post-process removing
    +
    4. core verb extraction within sentence
    """
    svo = doc._.svo = {}
    # 1. high recall detection
    # Find all related words, including pronouns
    all_entities = [e for e in doc.ents if e.label_ in focusing]
    # 2. high precision match
    id_entities, reverse_track = OrderedDict(), OrderedDict()
    last = None
    for e in all_entities:
        if e.label_ == "Pronoun":
            # just simply use the last one here
            if last:
                reverse_track[e] = reverse_track[last]
        else:
            for i in id_entities.keys():
                if i.similarity(e) > threshold:  # i & e are the same entity
                    id_entities[i].append(e)
                    id_entities[e] = id_entities[i]  # shallow copy, intended
                    reverse_track[e] = reverse_track[i]
                    break
            if e not in id_entities:  # new one
                id_entities[e] = [e]
                reverse_track[e] = uuid4().hex
            if any([token.dep_ == 'nsubj' for token in e]):
                last = e  # record last entity as nsubj
    # 3. post-process removing *is done together with*
    # 4. core verb extraction within sentence
    idx = 0
    keys = list(reverse_track.keys())
    current = keys[idx] if len(reverse_track) > 0 else None
    results = []
    for sent in doc.sents:
        # print("sent: ", (sent, sent.start, sent.end))
        if idx >= len(reverse_track):
            break
        related = []
        while sent.start <= current.start and current.end <= sent.end:
            related.append(current)  # process current relation
            idx += 1  # next
            if idx >= len(reverse_track):
                break
            current = keys[idx]
        # print("related: ", [(r, r.start, r.end) for r in related])
        if len(related) < 2 or all([e.label_ == "Pronoun" for e in related]):
            continue
        so = [(r, reverse_track[r]) for r in related]
        # we split al v-so pairs so that we can extract verb for each of them
        for s in so:
            for o in so:
                if o[0][0].i == s[0][0].i:  # use the first token to represent the span
                    continue
                v = extract_relation_identifier(sent, s[0][0], o[0][0], operations=operations, dep_check=False)
                if not v:  # invalid root word or no root word
                    continue
                results.append((s, v, o, sent))
    svo['entities'] = reverse_track
    svo['results'] = results
    return doc


setup_cache = None


def setup():
    global setup_cache
    if setup_cache:
        return setup_cache
    nlp = spacy.load('en_core_web_sm')
    patterns = load_ini()
    operations = load_operations()
    ruler = EntityRuler(nlp, overwrite_ents=True)
    ruler.add_patterns(patterns)
    nlp.add_pipe(ruler)
    nlp.add_pipe(set_custom_boundaries, before="parser")
    Doc.set_extension("svo", default=None)
    nlp.add_pipe(partial(svo_extraction, operations=operations), last=True)
    setup_cache = {
        'nlp': nlp,
        'patterns': patterns,
    }

    return setup_cache


def construct_dot(doc, title="Default Behaviour Graph"):
    dot = Digraph(comment=title, format='svg')
    nodes = {}
    for s, v, o, sent in doc._.svo['results']:
        for name, uid in [s, o]:
            if uid in nodes:
                if name not in nodes[uid]:
                    nodes[uid].append(name)
            else:
                nodes[uid] = [name]
    for uid, names in nodes.items():
        def merge_names(names):
            names = list(set(map(str, names)))
            names = sorted(names, key=lambda name: len(name))
            return "{} ({})".format(names[-1], ",".join(names[:-1])) if len(names) > 1 else names[0]

        dot.node(uid, merge_names(names))
    edge_idx = 0
    evidence = {}
    for s, v, o, sent in doc._.svo['results']:
        dot.edge(s[1], o[1], "{} [{}]".format(str(v), edge_idx))
        evidence[edge_idx] = str(sent)
        edge_idx += 1
    return dot, evidence


def run_spacy_pipeline(raw):
    nlp = setup()['nlp']
    doc = nlp(raw)
    return doc


def process_raw_text(raw):
    doc = run_spacy_pipeline(raw)
    dot, evidence = construct_dot(doc)
    return {
        "doc": doc,
        "doc_seq": display_doc(doc),
        "dot": dot,
        "evidence": evidence,
    }


# -------------------------------------------- output funcs


def output_result(result, target="temp.gv"):
    # pprint([{"sent": sent, "ents": sent.ents} for sent in result['doc'].sents if sent.ents])
    dot = result['dot']
    dot.render(target)
    with open(target + ".txt", "w") as fout:
        fout.writelines(["[{}]: {}\n".format(str(k), str(v)) for k, v in result['evidence'].items()])
    print(target + " finished.")
    sys.stdout.flush()


def output_results(results, target=os.path.join(".", "temp")):
    for i, r in results:
        output_result(r, os.path.join(target, str(i) + ".gv"))


def display_doc(doc):
    seq = [("text", "lemma", "pos", "tag", "dep", "shape", "is_alpha", "is_stop")]
    for token in doc:
        current = (token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
                   token.shape_, token.is_alpha, token.is_stop)
        seq.append(current)
    ret = {'ent': [(ent.text, ent.label_) for ent in doc.ents], 'seq': seq}
    return ret
