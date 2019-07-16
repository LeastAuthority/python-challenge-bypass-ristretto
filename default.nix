{ pkgs ? import <nixpkgs> { } }:
let
ristretto = pkgs.callPackage ./ristretto.nix { };
in
  pkgs.python27Packages.callPackage ./privacypass.nix {
    inherit ristretto;
  }
