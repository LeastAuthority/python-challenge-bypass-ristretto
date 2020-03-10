{ pkgs ? import <nixpkgs> { } }:
let
  pythonPackages = pkgs.python27Packages;
  python = pkgs.python27;
  ristretto = (pkgs.callPackage ./ristretto.nix { }).rootCrate.build;
  challenge-bypass-ristretto = pythonPackages.callPackage ./python-challenge-bypass-ristretto.nix {
    inherit ristretto;
  };
in
  (python.withPackages (ps: [ challenge-bypass-ristretto ])).env
