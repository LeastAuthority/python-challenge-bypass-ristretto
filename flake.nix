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
        buildSystems = [
          "x86_64-linux"
        ];
        crossSystems = [
          "aarch64-android"
          "armv7a-android-prebuilt"
        ];
      };
    in eachSystemAndCross (system: crossSystem:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        py-module = ps: ps.callPackage ./nix/python-challenge-bypass-ristretto.nix {
          inherit (self.legacyPackages.${system}) libchallenge_bypass_ristretto_ffi;
        };
      in {
        packages = {
          libchallenge_bypass_ristretto_ffi =
            import ./nix/libchallenge-bypass-ristretto-ffi.nix {
              inherit pkgs;
              fenix = fenix.packages.${system};
              naersk = naersk.lib.${system};
              src = libchallenge_bypass_ristretto_ffi-src;
            };

          python38-challenge-bypass-ristretto = py-module pkgs.python38.pkgs;
          python39-challenge-bypass-ristretto = py-module pkgs.python38.pkgs;
          python310-challenge-bypass-ristretto = py-module pkgs.python38.pkgs;
        };

        pkgsCross = {
          libchallenge_bypass_ristretto_ffi =
            import ./nix/libchallenge-bypass-ristretto-ffi.nix {
              pkgs = pkgs.pkgsCross.${crossSystem};
              fenix = fenix.packages.${system};
              naersk = naersk.lib.${system};
              src = libchallenge_bypass_ristretto_ffi-src;
            };
        };

        checks =
          let
            lib = self.packages.${system}.libchallenge_bypass_ristretto_ffi;
            py-env = py: py.withPackages (ps: [ (py-module ps) ]);
            integration = py: pkgs.runCommand
              "${lib.name}-integration"
              { }
              "${py-env py}/bin/python ${./spike.py} > $out";

          in {
            # Run a little integration test that exercises the underlying
            # library via the Python interface.
            integration38 = integration pkgs.python38;
            integration39 = integration pkgs.python39;
            integration310 = integration pkgs.python310;

            # The library should have the correct soname.
            soname = pkgs.runCommand "${lib.name}-soname" { } ''
            ${pkgs.gcc}/bin/readelf -d ${lib}/lib/libchallenge_bypass_ristretto_ffi.so > $out
            grep -E 'Library soname: \[libchallenge_bypass_ristretto_ffi\.so\]' $out
            '';

            # Verify that we are supplying the dynamic libraries in a
            # discoverable way.
            pkgconfig-discovery =
              pkgs.runCommand "${lib.name}-tests" {
                nativeBuildInputs = [
                  # Putting pkg-config here causes the hooks that set
                  # PKG_CONFIG_PATH to be set.
                  pkgs.pkg-config
                  lib
                ];
              } ''
# Be explicit about the name we're using here.  This is part of the project's
# public interface.  We don't want it changing unintentionally.
NAME=libchallenge_bypass_ristretto_ffi

if ! pkg-config --exists $NAME; then
  echo "Failed to discover $NAME with pkg-config"
  pkg-config --list-all
  exit 1
fi
if ! pkg-config --validate $NAME; then
  echo "Failed to validate $NAME.pc with pkg-config"
  pkg-config --list-all
  exit 1
fi

cat >main.c <<EOF
#include "lib.h"
int main(int argc, char** argv) {
    (void)signing_key_random();
    return 0;
}
EOF
${pkgs.clang}/bin/clang $(pkg-config --libs --cflags "$NAME") main.c -o main
./main

echo "passed" > "$out"
'';
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
            cargo
            rustc

            self.packages.${system}.libchallenge_bypass_ristretto_ffi
          ];
        };
      });
}
