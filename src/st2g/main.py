# entry point of the package
import argparse
from st2g.process import process_raw_text


def main(unparsed_args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", "-v", action="version", version="st2g 0.0")
    parser.add_argument("command", nargs="?", default="run")
    parser.add_argument("--input", "-i", type=str, required=True)
    parser.add_argument("--output", '-o', type=str, required=True)
    if unparsed_args:
        if isinstance(unparsed_args, str):
            unparsed_args = unparsed_args.split(" ")
        args = parser.parse_args(unparsed_args)
    else:
        args = parser.parse_args()

    if args.command == "run":
        with open(args.input, 'r') as fin:
            content = fin.read()
        result = process_raw_text(content)
        dot = result['dot']
        dot.render(args.output)


if __name__ == "__main__":
    main()
