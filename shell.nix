{ pkgs ? import <nixpkgs> { } }:
let
pythonPackages = pkgs.python27Packages;
python = pkgs.python27;
ristretto = pkgs.callPackage ./ristretto.nix { };
privacypass = pythonPackages.callPackage ./privacypass.nix { inherit ristretto; };
in
(python.withPackages (ps: [ privacypass ])).env
