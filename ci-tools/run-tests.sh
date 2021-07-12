#!/usr/bin/env sh

set -euxo pipefail

# An explicit build step so build failures can be seen separately from the rest.
LIB=$(nix-build default-challenge-bypass-ristretto-ffi.nix -A lib)

# Check to see if we successfully exported the pkg-config configuration.
# `--exists` will exit with error status if we have not.  It might be better
# if this were the checkPhase for the ffi bindings derivation.
if ! nix-shell -p "${LIB}" pkg-config --run 'pkg-config --exists libchallenge_bypass_ristretto_ffi'; then
    echo "pkg-config does not know about the library"
    exit 1
fi

# Run what passes for the test suite for our Python code, too.  Ditto here
# about checkPhase.
if ! nix-shell shell.nix --run 'mv ./spike.py /tmp; python /tmp/spike.py'; then
    echo "spike failed"
    exit 2
fi
