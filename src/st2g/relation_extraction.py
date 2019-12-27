from copy import deepcopy
from typing import List, Dict, Any, Type, Tuple
from graphviz import Digraph

from st2g.representations import SentTree, Span


Representations: Type = List[List[SentTree]]
Entity: Type = Dict
EntityId: Type = int
Entities: Type = List[Entity]
Relation: Type = Dict
Relations: Type = Dict[Tuple[EntityId, EntityId], Relation]


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
            if "resolved" not in v:
                continue
            else:
                location = (tree_id, span)
                _id = get_entity_id_by_location(v["resolved"], entities)
                entities[_id]["ref"].append((location))
    return entities


def extractRelationsFromSent(tree: SentTree, entities: Entities, tree_id: int, debug=False) -> Relations:
    pivots = {}
    sent, nodes, edges = tree
    # 1. propagation
    for span in sorted(nodes.keys()):
        v = nodes[span]
        if "is_pron" in v or "ioc" in v:
            current = span
            trace = []
            while current is not None:
                has_father = False
                for (src, des), ev in edges.items():
                    if des == current:
                        father = src
                        trace.append(ev.get("dep"))
                        if "is_valid_op" in nodes[father]:
                            if father not in pivots:
                                pivots[father] = []
                            pivots[father].append((span, list(reversed(deepcopy(trace)))))
                            trace.append("|")  # keep a record of all passed valid_ops
                        current = father
                        has_father = True
                        break
                if not has_father:
                    break
    # 2. touch pivot
    pivots = {pivot_span:trace_list for pivot_span, trace_list in pivots.items() if len(trace_list) > 1}
    if debug:
        for pivot_span, trace_list in pivots.items():
            print("-" * 40)
            print("Pivot: ", nodes[pivot_span]['lemma'], tree_id, pivot_span)
            for entity_span, trace in trace_list:
                print(nodes[entity_span]['text'], trace)
    ret = {}
    content_before_first_bar = lambda x: None if "|" not in x else tuple(x[:x.index('|')])
    for pivot_span, trace_list in pivots.items():
        subj_obj = False
        for entity_span_a, trace_a in trace_list:
            subj = any("subj" in t for t in trace_a)
            if not subj:
                continue
            passive = any("subjpass" in t for t in trace_a)
            for entity_span_b, trace_b in trace_list:  # assume a is subj and b is obj
                if entity_span_a == entity_span_b:
                    continue
                if not any("obj" in t for t in trace_b):
                    continue
                if content_before_first_bar(trace_a) and content_before_first_bar(trace_b):
                    if content_before_first_bar(trace_a) == content_before_first_bar(trace_b):
                        continue  # there should be a more proper verb
                location_a = (tree_id, entity_span_a)
                location_b = (tree_id, entity_span_b)
                ent_id_a = get_entity_id_by_location(location_a, entities)
                ent_id_b = get_entity_id_by_location(location_b, entities)
                if passive:
                    ent_id_a, ent_id_b = ent_id_b, ent_id_a
                assert (ent_id_b, ent_id_a) not in ret
                if (ent_id_a, ent_id_b) in ret:
                    ret[(ent_id_a, ent_id_b)]["occurences"].append((tree_id, pivot_span))
                    ret[(ent_id_a, ent_id_b)]["texts"].append(nodes[pivot_span]['text'])
                else:
                    ret[(ent_id_a, ent_id_b)] = {
                        "operation": nodes[pivot_span]['lemma'],
                        "occurences": [(tree_id, pivot_span)],
                        "texts": [nodes[pivot_span]['text']],
                    }
                subj_obj = True
        if not subj_obj:
            # consider obj-obj for
            for entity_span_a, trace_a in trace_list:
                obj = any("obj" in t for t in trace_a)
                if not obj:
                    continue
                for entity_span_b, trace_b in trace_list:  # assume a is subj and b is obj
                    if len(trace_a) >= len(trace_b):
                        continue
                    if tuple(trace_a) != tuple(trace_b[:len(trace_a)]):
                        continue
                    if not any("obj" in t for t in trace_b[len(trace_b) - len(trace_a):]):
                        continue
                    if content_before_first_bar(trace_a) and content_before_first_bar(trace_b):
                        if content_before_first_bar(trace_a) == content_before_first_bar(trace_b):
                            continue  # there should be a more proper verb
                    location_a = (tree_id, entity_span_a)
                    location_b = (tree_id, entity_span_b)
                    ent_id_a = get_entity_id_by_location(location_a, entities)
                    ent_id_b = get_entity_id_by_location(location_b, entities)
                    assert (ent_id_b, ent_id_a) not in ret
                    if (ent_id_a, ent_id_b) in ret:
                        ret[(ent_id_a, ent_id_b)]["occurences"].append((tree_id, pivot_span))
                        ret[(ent_id_a, ent_id_b)]["texts"].append(nodes[pivot_span]['text'])
                    else:
                        ret[(ent_id_a, ent_id_b)] = {
                            "operation": nodes[pivot_span]['lemma'],
                            "occurences": [(tree_id, pivot_span)],
                            "texts": [nodes[pivot_span]['text']],
                        }
    return ret


def extractRelationsFromSentList(trees: List[SentTree], entities: Entities) -> Relations:
    relations: Relations = {}
    for tree_id, tree in enumerate(trees):
        relations_nw = extractRelationsFromSent(tree, entities, tree_id)
        for k, v in relations_nw.items():
            if k in relations:
                relations[k]["occurences"] += v["occurences"]
                relations[k]["texts"] += v["texts"]
            else:
                relations[k] = v
    return relations


def runRelationExtraction(sents: List[SentTree]) -> Tuple[Entities, Relations]:
    entities = extractEntitiesFromSentList(sents)
    relations = extractRelationsFromSentList(sents, entities)
    return entities, relations


def convertEntitiesRelationsIntoDot(entities: Entities, relations: Relations) -> Digraph:
    dot = Digraph(comment="Default Behaviour Graph", format='svg')
    for e in entities:
        dot.node(str(e['id']), e['text'], xlabel=e['ioc'])
    for (src, des), v in relations.items():
        dot.edge(str(src), str(des), v['operation'])
    return dot