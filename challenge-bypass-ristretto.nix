{ pkgs, stdenv, darwin }:
let
  challenge-bypass-ristretto = pkgs.callPackage ./generated-challenge-bypass-ristretto.nix { };
  addSecurity = drv:
    if stdenv.isDarwin then
      drv.overrideDerivation (old: {
        nativeBuildInputs = [
          darwin.apple_sdk.frameworks.Security
        ];
      })
    else
      drv;
in
  challenge-bypass-ristretto // {
    rootCrate = {
      build = addSecurity challenge-bypass-ristretto.rootCrate.build;
      debug = addSecurity challenge-bypass-ristretto.rootCrate.debug;
    };
  }
