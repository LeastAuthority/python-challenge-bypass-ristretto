let
  sources = import nix/sources.nix;
in
# A basic Python 2.7-based packaging of the Python bindings for the
# Ristretto-based PrivacyPass variant implemented by
# challenge-bypass-ristretto.
{ pkgs ? import sources.nixpkgs { }
# Brave's Ristretto library is not in nixpkgs so provide the package we're
# maintaining.
, challenge-bypass-ristretto-ffi-repo ? sources.challenge-bypass-ristretto-ffi
, challenge-bypass-ristretto-ffi ? pkgs.callPackage ./challenge-bypass-ristretto.nix { inherit challenge-bypass-ristretto-ffi-repo; }
# Choose the Python runtime for which we're building
, pythonPackages ? pkgs.python27Packages
}:
# Build our Python bindings in the usual way, supplying the necessary extra
# dependency.
pythonPackages.callPackage ./python-challenge-bypass-ristretto.nix {
  inherit challenge-bypass-ristretto-ffi;
}
