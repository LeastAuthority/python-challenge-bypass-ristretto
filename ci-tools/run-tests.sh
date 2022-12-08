#!/usr/bin/env sh

set -euxo pipefail

PYTHON=$1
shift

# Run the ffi binding tests.
nix flake check

# Build the Python package itself
nix build ".#${PYTHON}-challenge-bypass-ristretto"
