{
  inputs = {
    nixpkgs = {
      url = "github:nixos/nixpkgs?ref=nixos-22.11";
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
    , libchallenge_bypass_ristretto_ffi-src
    , fenix
    , naersk
    }:
    let
      eachSystemAndCross = import ./nix/each-system-and-cross.nix {
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
          import ./nix/libchallenge-bypass-ristretto-ffi.nix {
            inherit (pkgs) lib;
            pkgsForHost = pkgs;
            fenix = fenix.packages.${system};
            naersk = naersk.lib.${system};
            src = libchallenge_bypass_ristretto_ffi-src;
          };

        python-challenge-bypass-ristretto =
          pkgs.python3.pkgs.callPackage ./nix/python-challenge-bypass-ristretto.nix {
            inherit (self.legacyPackages.${system}) libchallenge_bypass_ristretto_ffi;
          };

        pkgsCross.libchallenge_bypass_ristretto_ffi =
          import ./nix/libchallenge-bypass-ristretto-ffi.nix {
            inherit (pkgs) lib;
            pkgsForHost = pkgs.pkgsCross.${crossSystem};
            fenix = fenix.packages.${system};
            naersk = naersk.lib.${system};
            src = libchallenge_bypass_ristretto_ffi-src;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python3.withPackages (ps: with ps; [
              # TODO: Deduplicate this list / the list in the package definition
              cffi
              attrs

              wheel
              setuptools
              setuptools_scm
              milksnake

              testtools
              hypothesis
            ]))
          ];

          nativeBuildInputs = with pkgs; [
            cabal-install
            ghc
            pkgconfig

            self.packages.${system}.libchallenge_bypass_ristretto_ffi
          ];
        };
      });
}
