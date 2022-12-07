#!/usr/bin/env sh

set -euxo pipefail

PYTHON=$1
shift

# Run the ffi binding tests.
nix flake check

# Build the Python package itself
nix build ".#${PYTHON}-challenge-bypass-ristretto"

# Run what passes for the test suite for our Python code, too.  It would be
# nice to put this into a tests attribute on the Python package derivation,
# probably.
if ! nix-shell -p ./result --run 'cp ./spike.py /tmp; python /tmp/spike.py'; then
    echo "spike failed"
    exit 2
fi
