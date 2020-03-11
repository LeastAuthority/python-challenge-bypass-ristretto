{ pkgs, stdenv, lib, darwin }:
let
  defaultCrateOverrides = pkgs.defaultCrateOverrides // {
    curve25519-dalek = attrs: {
      buildInputs = lib.optional stdenv.isDarwin darwin.apple_sdk.frameworks.Security;
    };
  };
  challenge-bypass-ristretto = pkgs.callPackage ./generated-challenge-bypass-ristretto.nix {
    inherit defaultCrateOverrides;
  };
in
  challenge-bypass-ristretto
