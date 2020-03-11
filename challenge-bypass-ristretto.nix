{ pkgs, stdenv, lib, darwin }:
let
  withSecurity = attrs: {
    buildInputs = lib.optional stdenv.isDarwin darwin.apple_sdk.frameworks.Security;
  };
  defaultCrateOverrides = pkgs.defaultCrateOverrides // {
    curve25519-dalek = withSecurity;
    challenge-bypass-ristretto-ffi = withSecurity;
  };
  challenge-bypass-ristretto = pkgs.callPackage ./generated-challenge-bypass-ristretto.nix {
    inherit defaultCrateOverrides;
  };
in
  challenge-bypass-ristretto
