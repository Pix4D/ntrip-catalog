"""
this script validates the json files against the schema
"""

import argparse
import json
import logging
import os
import pathlib

from jsonschema import Draft202012Validator, validators

local_path = pathlib.Path(__file__).parent.parent.resolve().as_posix()

logger = logging.getLogger(__name__)


def get_schemas_path(schema_version):
    return os.path.join(local_path, "schemas", schema_version)


def get_schema(schema_version, name):
    schema_path = os.path.join(get_schemas_path(schema_version), name + ".schema.json")

    with open(schema_path) as f:
        content = json.load(f)
        return content


def get_entries_schema(schema_version):
    return get_schema(schema_version, "entries")


def get_global_schema(schema_version):
    return get_schema(schema_version, "ntrip-catalog")


def validate_content(content, filename, checkers):
    for entry in content:
        name = entry["name"]
        urls = entry["urls"]
        checkers["names"].setdefault(name, []).append(filename)
        for url in urls:
            checkers["urls"].setdefault(url, []).append(filename)


def validate_jsons(input, log_input_files, schema, validate_dist, schemas_uri):

    resolver = validators.RefResolver(base_uri=schemas_uri, referrer=schema)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, resolver=resolver)

    walk_dir = os.path.abspath(input)
    logger.debug("walk_dir (absolute) = " + walk_dir)

    ok = True
    failing_files = []

    checkers = {
        "urls": {},
        "names": {},
    }

    for root, subdirs, files in os.walk(walk_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            extension = pathlib.Path(file_path).suffix
            if extension == ".json":
                with open(file_path) as f:
                    content = json.load(f)
                    if not validate_dist and isinstance(content, dict):
                        content = [content]
                    try:
                        validator.validate(instance=content)
                        if validate_dist:
                            content = content["entries"]
                        validate_content(content, file_path, checkers)
                        if log_input_files:
                            logger.info(f"{file_path} -- OK!")
                    except Exception as e:
                        logger.error(f"{file_path} -- FAILED!")
                        ok = False
                        failing_files.append(file_path)
                        logger.error("*** >>>>>\n", e, "\n*** <<<<<")

            elif log_input_files:
                logger.warning(f"file {file_path} is not JSON")

    for k, v in checkers["names"].items():
        if len(v) > 1:
            ok = False
            files = ", ".join(v)
            logger.warning(f"Name [{k}] is used in several files: {files}")

    for k, v in checkers["urls"].items():
        if len(v) > 1:
            ok = False
            files = ", ".join(v)
            logger.error(f"URL {k} is used in several files: {files}")

    if len(failing_files) > 0:
        logger.error("\n*** Failing files: \n", "\n".join(failing_files), "\n")
    return ok


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validates the json files in data against the schema."
    )

    parser.add_argument(
        "--input", type=str, help="Folder containing the json data. Defaults to ../data"
    )
    parser.add_argument(
        "--input-dist",
        type=str,
        help="Folder containing the aggregated json data. Defaults to ../dist",
    )
    parser.add_argument(
        "--validate-dist",
        help="Validate the aggregate json, not the partial ones",
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    parser.add_argument(
        "--log-input-files",
        help="Log read files to stdout",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--schema-version",
        help="Version of the schema",
        default="v0.1",
    )
    parser.add_argument("--single-file", help="Validate a single file")  # TB done

    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    if args.validate_dist:
        input = args.input_dist
        if not input:
            input = os.path.join(local_path, "dist")
        schema = get_global_schema(args.schema_version)
    else:
        input = args.input
        if not input:
            input = os.path.join(local_path, "data")
        schema = get_entries_schema(args.schema_version)
    schemas_uri = pathlib.Path(get_schemas_path(args.schema_version)).as_uri() + "/"
    if not validate_jsons(
        input, args.log_input_files, schema, args.validate_dist, schemas_uri
    ):
        raise Exception("Some failures validating data")


if __name__ == "__main__":
    main()

# what about                     "additionalProperties": false,
