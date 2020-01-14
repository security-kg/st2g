# entry point of the package
import argparse
import json
from st2g.process import process_raw_text, output_result
from st2g.representations import processContent, visualizeProcessedContent
from st2g.relation_extraction import runRelationExtraction, convertEntitiesRelationsIntoDot


def main(unparsed_args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", "-v", action="version", version="st2g 0.0")
    parser.add_argument("command", nargs="?", default="run")
    parser.add_argument("--input", "-i", type=str, required=True)
    parser.add_argument("--output", '-o', type=str, required=True)
    parser.add_argument("--entity", '-E', action='store_true')
    parser.add_argument("--relation", '-R', action='store_true')
    parser.add_argument("--no_protect_ioc", '-N', action='store_true')
    if unparsed_args:
        if isinstance(unparsed_args, str):
            unparsed_args = unparsed_args.split(" ")
        args = parser.parse_args(unparsed_args)
    else:
        args = parser.parse_args()

    if args.command == "old_run":
        with open(args.input, 'r') as fin:
            content = fin.read()
        result = process_raw_text(content)
        output_result(result, args.output)
    elif args.command == "run":
        with open(args.input, 'r') as fin:
            content = fin.read()
        result = processContent(content, protect_IOC=bool(not args.no_protect_ioc))
        dot = visualizeProcessedContent(result)
        dot.render(args.output+".dp")
        agg_result = sum(result, [])
        entities, relations = runRelationExtraction(agg_result)
        if args.entity:
            with open(args.output+".e.json", 'w') as fout:
                json.dump(entities, fout)
        if args.relation:
            with open(args.output+".r.json", 'w') as fout:
                json.dump(relations, fout)
        dot = convertEntitiesRelationsIntoDot(entities, relations)
        dot.render(args.output)


if __name__ == "__main__":
    main()
