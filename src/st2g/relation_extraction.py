from copy import deepcopy
from itertools import permutations, chain
from typing import List, Dict, Any, Type, Tuple
from graphviz import Digraph

from st2g.representations import SentTree, Span


Representations: Type = List[List[SentTree]]
Entity: Type = Dict
EntityId: Type = int
Entities: Type = List[Entity]
Relation: Type = Dict
Relations: Type = List[Relation]


def isSameEntity(text: str, meta: dict, rhs: Entity) -> bool:
    return text == rhs["text"]  # TO BE IMPROVED


def get_entity_id_by_location(location: Tuple[int, Span], entities: Entities) -> int:
    for e in entities:
        if location in e["occurences"] or location in e["ref"]:
            return e["id"]
    raise ValueError("location entity not found")


def extractEntitiesFromSentList(sents: List[SentTree]) -> Entities:
    entities: Entities = []
    for tree_id, tree in enumerate(sents):
        sent, nodes, edges = tree
        for span in sorted(nodes.keys()):
            v = nodes[span]
            if 'ioc' not in v:
                continue
            else:
                location = (tree_id, span)
                text, meta = sent[span[0]:span[1]], v
                # try to figure out if it is an existing entity
                found = -1
                for i, e in enumerate(entities):
                    if isSameEntity(text, meta, e):
                        assert found == -1
                        found = i
                if found == -1:
                    # create a new entry
                    entities.append({
                        "id": len(entities),
                        "text": text,
                        "ioc": v['ioc'],
                        "occurences": [location],
                        "ref": []
                    })
                else:
                    entities[found]["occurences"].append(location)
    for tree_id, tree in enumerate(sents):
        sent, nodes, edges = tree
        for span in sorted(nodes.keys()):
            v = nodes[span]
            if not v.get("resolved"):
                continue
            else:
                location = (tree_id, span)
                _id = get_entity_id_by_location(v["resolved"], entities)
                entities[_id]["ref"].append((location))
    return entities


def extractRelationsFromSent(tree: SentTree, entities: Entities, tree_id: int) -> Relations:
    sent, nodes, edges = tree
    # list all ioc paths
    paths = []
    for span in sorted(nodes.keys()):
        v = nodes[span]
        if "ioc" in v or v.get("resolved"):
            current = span
            node_trace = [current]
            edge_trace = []
            while current is not None:
                has_father = False
                for (src, des), ev in edges.items():
                    if des == current:
                        node_trace.append(src)
                        edge_trace.append(ev.get("dep"))
                        current = src
                        has_father = True
                if not has_father:
                    break
            paths.append((list(reversed(node_trace)), list(reversed(edge_trace))))
    # evaluate all pairs
    ret = []
    have_subj = set()
    # 1. check subj->obj
    for (node_trace_a, edge_trace_a), (node_trace_b, edge_trace_b) in permutations(paths, 2):
        # calc the common path
        # C0, C1, C2, ..., CN -> A0, A1, A2, ...
        # C0, C1, C2, ..., CN -> B0, B1, B2, ...
        n = 0
        while n < min(len(node_trace_a), len(node_trace_b)) and node_trace_a[n] == node_trace_b[n]:
            n += 1
        n -= 1
        assert n >= 0  # at least they share a root
        if not any("subj" in dep for dep in edge_trace_a[n:]):
            continue
        if not any("obj" in dep for dep in edge_trace_b[n:]):
            continue
        for span in node_trace_a[:n+1]:
            have_subj.add(span)
        # go and find the verb
        for span in chain(reversed(node_trace_b), node_trace_a[n+1:]):
            if "is_valid_op" in nodes[span]:
                ent_a = get_entity_id_by_location((tree_id, node_trace_a[-1]), entities)
                ent_b = get_entity_id_by_location((tree_id, node_trace_b[-1]), entities)
                if any("subjpass" in dep for dep in edge_trace_a[n:]) \
                        or any("agent" in dep for dep in edge_trace_b[n:]):
                    ent_a, ent_b = ent_b, ent_a
                ret.append({
                    "entity_a_id": ent_a,
                    "entity_b_id": ent_b,
                    "operation": nodes[span]['lemma'],
                    "occurence": (tree_id, span),
                    "text": nodes[span]['text'],
                })
                break
    # 2. check obj -> obj (human as subj)
    for (node_trace_a, edge_trace_a), (node_trace_b, edge_trace_b) in permutations(paths, 2):
        # calc the common path
        # C0, C1, C2, ..., CN -> A0, A1, A2, ...
        # C0, C1, C2, ..., CN -> B0, B1, B2, ...
        n = 0
        while n < min(len(node_trace_a), len(node_trace_b)) and node_trace_a[n] == node_trace_b[n]:
            n += 1
        n -= 1
        assert n >= 0  # at least they share a root
        if len(node_trace_a) > len(node_trace_b) \
                or (len(node_trace_a) == len(node_trace_b) and node_trace_a[-1][0] > node_trace_b[-1][0]):
            continue  # we prefer the shorter or earlier one as the possible sub
        if any(node in have_subj for node in node_trace_a[:n+1]):
            continue
        if not any("obj" in dep for dep in edge_trace_a):
            continue
        if not any("obj" in dep for dep in edge_trace_b[n:]):
            continue
        # go and find the verb
        for span in chain(reversed(node_trace_b), node_trace_a[n+1:]):
            if "is_valid_op" in nodes[span]:
                ent_a = get_entity_id_by_location((tree_id, node_trace_a[-1]), entities)
                ent_b = get_entity_id_by_location((tree_id, node_trace_b[-1]), entities)
                # no need to deal with passive this time
                if ent_a == ent_b:
                    continue
                ret.append({
                    "entity_a_id": ent_a,
                    "entity_b_id": ent_b,
                    "operation": nodes[span]['lemma'],
                    "occurence": (tree_id, span),
                    "text": nodes[span]['text'],
                })
                break

    return ret


def extractRelationsFromSentList(trees: List[SentTree], entities: Entities, use_ttp_drill: bool=False) -> Relations:
    relations: Relations = []
    for tree_id, tree in enumerate(trees):
        if use_ttp_drill:
            relations_nw = extractRelationsFromSentTTPDrill(tree, entities, tree_id)
        else:
            relations_nw = extractRelationsFromSent(tree, entities, tree_id)
        relations += relations_nw
    for i, r in enumerate(relations):
        r['id'] = i
    return relations


def runRelationExtraction(sents: List[SentTree], use_ttp_drill: bool=False) -> Tuple[Entities, Relations]:
    entities = extractEntitiesFromSentList(sents)
    relations = extractRelationsFromSentList(sents, entities, use_ttp_drill)
    return entities, relations


def convertEntitiesRelationsIntoDot(entities: Entities, relations: Relations) -> Digraph:
    dot = Digraph(comment="Default Behaviour Graph", format='svg')
    for e in entities:
        dot.node(str(e['id']), e['text'], xlabel=e['ioc'])
    for v in relations:
        src = v['entity_a_id']
        des = v['entity_b_id']
        dot.edge(str(src), str(des), v['operation'], xlabel="[{}]".format(v['id']))
    return dot


def extractRelationsFromSentTTPDrill(tree: SentTree, entities: Entities, tree_id: int) -> Relations:
    """
        In TTP Drill, the subject is always the malware, here we use the subject of the sentence
        And in TTP Drill, the governor verb is always directly linked to the subj and obj
        There's no nmod in spacy, so we replace that with prep->pobj combination
        Related relation: nsubj, dobj, nsubjpass, nmod
        prep limited to: from, to, with, via, over, for, through, using, into
    """
    sent, nodes, edges = tree
    # list all ioc paths
    paths = []
    for span in sorted(nodes.keys()):
        v = nodes[span]
        if "ioc" in v or v.get("resolved"):
            current = span
            node_trace = [current]
            edge_trace = []
            while current is not None:
                has_father = False
                for (src, des), ev in edges.items():
                    if des == current:
                        node_trace.append(src)
                        edge_trace.append(ev.get("dep"))
                        current = src
                        has_father = True
                if not has_father:
                    break
            paths.append((list(reversed(node_trace)), list(reversed(edge_trace))))
    # evaluate all pairs
    ret = []
    have_subj = set()
    # 1. check subj->......
    for (node_trace_a, edge_trace_a), (node_trace_b, edge_trace_b) in permutations(paths, 2):
        # calc the common path
        # C0, C1, C2, ..., CN -> A0, A1, A2, ...
        # C0, C1, C2, ..., CN -> B0, B1, B2, ...
        n = 0
        while n < min(len(node_trace_a), len(node_trace_b)) and node_trace_a[n] == node_trace_b[n]:
            n += 1
        n -= 1
        assert n >= 0  # at least they share a root
        if len(edge_trace_a) <= n or not "subj" in edge_trace_a[n]:
            continue
        if len(edge_trace_b) <= n or not any((_ in edge_trace_b[n]) for _ in ["nsubj", "dobj", "nsubjpass", "nmod", "prep"]):
            continue
        if edge_trace_b[n] == "prep" and (len(edge_trace_b) != n+2 or edge_trace_b[n+1] != "pobj"):
            continue
        for span in node_trace_a[:n+1]:
            have_subj.add(span)
            
        # go and find the verb
        span = node_trace_a[n]  # must be the governer
        if "is_valid_op" in nodes[span]:
            ent_a = get_entity_id_by_location((tree_id, node_trace_a[-1]), entities)
            ent_b = get_entity_id_by_location((tree_id, node_trace_b[-1]), entities)
            if any("nsubj" in dep for dep in edge_trace_b[n:]) or any("nmod" in dep for dep in edge_trace_b[n:]):
                ent_a, ent_b = ent_b, ent_a
            ret.append({
                "entity_a_id": ent_a,
                "entity_b_id": ent_b,
                "operation": nodes[span]['lemma'],
                "occurence": (tree_id, span),
                "text": nodes[span]['text'],
            })

    return ret