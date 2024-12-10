"""
this script generates a single json from collecting all the json in a tree
"""

import argparse
import json
import logging
import os
import pathlib

local_path = pathlib.Path(__file__).parent.parent.resolve().as_posix()

logger = logging.getLogger(__name__)


def read_json(input, log_input_files):
    if not input:
        input = os.path.join(local_path, "data")

    entries = []

    walk_dir = os.path.abspath(input)
    logger.debug("walk_dir (absolute) = " + walk_dir)

    for root, subdirs, files in os.walk(walk_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            extension = pathlib.Path(file_path).suffix
            if extension == ".json":
                if log_input_files:
                    logger.info(f"{file_path}")
                with open(file_path) as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        entries += content
                    elif isinstance(content, dict):
                        entries += [content]
                    else:
                        raise Exception(
                            f"Unexpected content type in json file ${file_path}"
                        )
            elif log_input_files:
                logger.warning(f"file {file_path} is not JSON")

    entries.sort(key=lambda x: x["name"] + "  " + "".join(x["urls"]))

    schema = "https://ntrip-catalog.org/schemas/v0.1/ntrip-catalog.schema.json"

    final = {"$schema": schema, "release": 0, "entries": entries}
    return final


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a single json from collecting all the json in a tree."
    )

    parser.add_argument(
        "--input", type=str, help="Folder containing the json data. Defaults to ../data"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Destination file. Defaults to ../dist/ntrip-catalog.json",
    )
    parser.add_argument(
        "--log-input-files",
        help="Log read files to stdout",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--dry-run",
        help="Do not write output, but dump to stdout",
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    return parser.parse_args()


def main():
    args = parse_args()
    final = read_json(args.input, args.log_input_files)
    if args.dry_run:
        logger.info(json.dumps(final, indent=4))
    else:
        outpath = args.output
        if not outpath:
            outpath = os.path.join(local_path, "dist", "ntrip-catalog.json")
        directory = pathlib.Path(outpath).parent
        pathlib.Path(directory).mkdir(parents=True, exist_ok=True)

        with open(outpath, "w") as f:
            json.dump(final, f, indent=4)
            f.write("\n")  # Add newline cause Py JSON does not


if __name__ == "__main__":
    main()
