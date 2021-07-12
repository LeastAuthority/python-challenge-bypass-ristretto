#!/usr/bin/env sh

set -euxo pipefail

# An explicit build step so build failures can be seen separately from the rest.
LIB=$(nix-build default-challenge-bypass-ristretto-ffi.nix -A lib)

# Check to see if we successfully exported the pkg-config configuration.
# `--exists` will exit with error status if we have not and we will propagate
# that error status.  It might be better if this were the checkPhase for the
# ffi bindings derivation.
nix-shell -p "${LIB}" pkg-config --run 'pkg-config --exists libchallenge_bypass_ristretto'


# Run what passes for the test suite for our Python code, too.  Ditto here
# about checkPhase.
nix-shell shell.nix --run 'mv ./spike.py /tmp; python /tmp/spike.py'
