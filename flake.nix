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
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        libchallenge_bypass_ristretto_ffi =
          import ./libchallenge-bypass-ristretto-ffi.nix {
            inherit (pkgs) lib;
            pkgsForHost = pkgs;
            fenix = fenix.packages.${system};
            naersk = naersk.lib.${system};
            src = libchallenge_bypass_ristretto_ffi-src;
          };

        python-challenge-bypass-ristretto =
          pkgs.python3.pkgs.callPackage ./python-challenge-bypass-ristretto.nix {
            inherit (self.legacyPackages.${system}) libchallenge_bypass_ristretto_ffi;
          };

        pkgsCross.libchallenge_bypass_ristretto_ffi =
          import ./libchallenge-bypass-ristretto-ffi.nix {
            inherit (pkgs) lib;
            pkgsForHost = pkgs.pkgsCross.${crossSystem};
            fenix = fenix.packages.${system};
            naersk = naersk.lib.${system};
            src = libchallenge_bypass_ristretto_ffi-src;
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
