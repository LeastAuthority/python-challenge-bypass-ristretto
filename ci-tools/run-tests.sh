#!/usr/bin/env sh

set -euxo pipefail

nix-build --arg pkgs 'import <nixpkgs> {}' challenge-bypass-ristretto.nix -A tests

# Run what passes for the test suite for our Python code, too.  Ditto here
# about checkPhase.
if ! nix-shell shell.nix --run 'cp ./spike.py /tmp; python /tmp/spike.py'; then
    echo "spike failed"
    exit 2
fi
