{ pkgs, stdenv, darwin }:
let
  challenge-bypass-ristretto = pkgs.callPackage ./generated-challenge-bypass-ristretto.nix { };
in
  if stdenv.isDarwin then
    challenge-bypass-ristretto.overrideAttrs (old: {
        nativeBuildInputs = [
          darwin.apple_sdk.frameworks.Security
        ];
    })
  else
    challenge-bypass-ristretto
