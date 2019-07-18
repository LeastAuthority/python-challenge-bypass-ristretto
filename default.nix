# A basic Python 2.7-based packaging of the Python bindings for the
# Ristretto-based PrivacyPass variant.
{ pkgs ? import <nixpkgs> { } }:
let
  # Brave's Ristretto library is not in nixpkgs so provide the package we're
  # maintaining.
  ristretto = pkgs.callPackage ./ristretto.nix { };
in
  # Build our Python bindings in the usual way, supplying the necessary extra
  # dependency.
  pkgs.python27Packages.callPackage ./privacypass.nix {
    inherit ristretto;
  }
