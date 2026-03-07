import json

with open("../../../data/anime_relations.jsonl", "r") as f:
    
    relations = [line for line in f]

    # get all unique relation_type fields
    relation_types = set()
    
    for relation in relations:
        relation_type = json.loads(relation)["relation_type"]
        relation_types.add(relation_type)

    print(relation_types)