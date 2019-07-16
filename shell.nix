{ pkgs ? import <nixpkgs> { } }:
let
ristretto = pkgs.callPackage ./ristretto.nix { };
privacypass = pkgs.python27Packages.callPackage ./privacypass.nix { inherit ristretto; };
in
(pkgs.python27.withPackages (ps: [ privacypass ])).env
