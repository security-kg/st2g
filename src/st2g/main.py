# entry point of the package
import sys
import argparse


def main(unparsed_args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", "-v", action="version", version="st2g 0.0")
    parser.add_argument("commands", nargs="?", default="run")
    parser.add_argument("--input", "-i", type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument("--output", '-o', type=argparse.FileType('w'), default=sys.stdout)
    if unparsed_args:
        if isinstance(unparsed_args, str):
            unparsed_args = unparsed_args.split(" ")
        args = parser.parse_args(unparsed_args)
    else:
        args = parser.parse_args()
    print("input: ", args.input)
    print("Here's the output (default to stdout).")


if __name__ == "__main__":
    main()
