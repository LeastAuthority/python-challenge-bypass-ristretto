#!/usr/bin/env sh

set -euxo pipefail

PYTHON=$1
shift

# On CI, explicitly pass a value for nixpkgs so that the build respects the
# nixpkgs revision CI is trying to test.  Otherwise, accept the default
# nixpkgs defined by the packaging expressions.
if [ -v CI ]; then
    pkgsArg=(--arg pkgs "import <nixpkgs> {}")
else
    pkgsArg=()
fi

# Run the ffi binding tests.
nix-build \
    -A tests \
    --out-link ffi-tests \
    "${pkgsArg[@]}" \
    --argstr python "$PYTHON" \
    challenge-bypass-ristretto.nix

# Build the Python package itself
nix-build --out-link result "${pkgsArg[@]}"

# Run what passes for the test suite for our Python code, too.  It would be
# nice to put this into a tests attribute on the Python package derivation,
# probably.
if ! nix-shell -p ./result --run 'cp ./spike.py /tmp; python /tmp/spike.py'; then
    echo "spike failed"
    exit 2
fi
