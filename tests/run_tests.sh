#!/usr/bin/env bash
set -Eeuo pipefail

LOCALPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; cd .. ; pwd -P )"
echo $LOCALPATH

python3 $LOCALPATH/scripts/make_dist.py

# Run pre-commit to check lint
shopt -s globstar
pre-commit run --file $LOCALPATH/**/*

python3 -W ignore::DeprecationWarning $LOCALPATH/scripts/validator.py --log-input-files --no-validate-dist
python3 -W ignore::DeprecationWarning $LOCALPATH/scripts/validator.py --log-input-files --validate-dist

pytest $LOCALPATH/tests/
