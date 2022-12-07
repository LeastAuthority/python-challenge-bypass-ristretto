pkgs:
let
  # Translate from system names as used by nixpkgs to system names as used by
  # the Rust toolchain.
  nixpkgsToRustSystems = {
    "armv7a-android-prebuilt" = "armv7-linux-androideabi";
    "aarch64-android-prebuilt" = "aarch64-linux-android";
  };

  moz_overlay = import (builtins.fetchTarball https://github.com/mozilla/nixpkgs-mozilla/archive/master.tar.gz);
  native-pkgs = pkgs.extend moz_overlay;

  nixpkgsCrossForSystem = native-pkgs: cross-system: import <nixpkgs> {
    crossSystem = native-pkgs.lib.systems.examples.${cross-system};
  };

  rustForNixpkgsSystem = cross-system: native-pkgs:
    native-pkgs.rustChannelOfTargets "stable" null [
      nixpkgsToRustSystems.${cross-system}
    ];

  crateForCrossSystem = native-pkgs: cross-system: crateForPkgs:
    let
      pkgs = nixpkgsCrossForSystem native-pkgs cross-system;
      crate = crateForPkgs pkgs;
    in
      crate.override {
        rust = rustForNixpkgsSystem cross-system native-pkgs;
      };

  eitherForCrossSystem = native-pkgs: cross-system:
    crateForCrossSystem
      native-pkgs
      cross-system
      (pkgs: pkgs.cratesIO.crates.either."1.5.2" {} {});

  ristrettoForCrossSystem = native-pkgs: cross-system:
    crateForCrossSystem
      native-pkgs
      cross-system
      (pkgs: import ./challenge-bypass-ristretto.nix {
        inherit pkgs;
        rustForPkgs = rustForNixpkgsSystem cross-system;
      });

in {
  "armv7a-android-prebuilt" = let system = "armv7a-android-prebuilt"; in {
    either = eitherForCrossSystem native-pkgs system;
    libchallenge_bypass_ristretto_ffi = ristrettoForCrossSystem native-pkgs system;
  };
  "aarch64-android-prebuilt" = let system = "aarch64-android-prebuilt"; in {
    either = eitherForCrossSystem native-pkgs system;
    libchallenge_bypass_ristretto_ffi = ristrettoForCrossSystem native-pkgs system;
  };
}
