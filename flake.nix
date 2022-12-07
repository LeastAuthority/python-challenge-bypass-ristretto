{
  inputs = {
    nixpkgs = {
      url = "github:nixos/nixpkgs?ref=nixos-22.11";
    };
    flake-utils = {
      url = "github:numtide/flake-utils";
    };
    obelisk-src = {
      url = "github:obsidiansystems/obelisk";
      flake = false;
    };
    libchallenge_bypass_ristretto_ffi-src = {
      url = "github:brave-intl/challenge-bypass-ristretto-ffi";
      flake = false;
    };
    fenix = {
      url = "github:nix-community/fenix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    naersk = {
      url = "github:nix-community/naersk";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs =
    { self
    , nixpkgs
    , flake-utils
    , obelisk-src
    , libchallenge_bypass_ristretto_ffi-src
    , fenix
    , naersk
    }:
    let
      eachSystemAndCross = import ./each-system-and-cross.nix {
        inherit flake-utils;
        inherit (nixpkgs) lib;
        crossSystems = [
          "aarch64-android"
          "armv7a-android-prebuilt"
        ];
      };
    in eachSystemAndCross (system: crossSystem:
      let
        # A mapping from system names as understood by nixpkgs to system names as understood by the Rust toolchain.
        _rustTargetTranslation = {
          "aarch64-android"         = "aarch64-linux-android";
          "armv7a-android-prebuilt" = "armv7-linux-androideabi";
        };
        toRustTarget = s: _rustTargetTranslation.${s};

        pkgs = nixpkgs.legacyPackages.${system};
      in {
        pkgsCross.libchallenge_bypass_ristretto_ffi =
          import ./challenge-bypass-ristretto.nix {
            inherit pkgs system fenix naersk crossSystem;
            src = libchallenge_bypass_ristretto_ffi-src;
            rustSystemTarget = toRustTarget crossSystem;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            (pkgs.callPackage obelisk-src { }).command
          ];

          nativeBuildInputs = [
            pkgs.cabal-install
            pkgs.ghc
            pkgs.pkgconfig
            self.packages.${system}.pkgsCross.aarch64-android.libchallenge_bypass_ristretto_ffi
          ];
        };
      });
}
