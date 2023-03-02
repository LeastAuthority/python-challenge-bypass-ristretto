{
  inputs = {
    nixpkgs = {
      url = "github:nixos/nixpkgs?ref=nixos-22.11";
    };

    # The source repository for the crate we're building.
    libchallenge_bypass_ristretto_ffi-src = {
      url = "github:brave-intl/challenge-bypass-ristretto-ffi";
      flake = false;
    };

    # A flake which provides pretty good support for Rust-related packages,
    # including a nice way to customize a build tool chain (eg, for
    # cross-compilation).
    fenix = {
      url = "github:nix-community/fenix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # A flake which provides pretty good support for building Rust crates and
    # which conveniently can consume the Rust toolchain provided by fenix.
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
      # Get a function that helps set up packages that are cross-compiled for
      # other systems.
      eachSystemAndCross = import ./nix/each-system-and-cross.nix {
        inherit (nixpkgs) lib;
        buildSystems = [
          # In principle we could build on many different systems.  In
          # practice all our build systems are probably of this one type and
          # we haven't tested the build anywhere else.
          "x86_64-linux"
        ];
        crossSystems = [
          "aarch64-android"
          # There is only -prebuilt for armv7a so we'll probably use it, if we
          # need armv7.  Unfortunately, it is broken in our pinned version of
          # nixpkgs (in the same way as aarch64-android-prebuilt):
          #
          # error: infinite recursion encountered
          #
          #        at /nix/store/jwk...-source/pkgs/stdenv/generic/default.nix:133:14:
          #
          #           132|
          #           133|       inherit initialPath shell
          #              |              ^
          #           134|         defaultNativeBuildInputs defaultBuildInputs;

          # "armv7a-android-prebuilt"
        ];
      };
    in eachSystemAndCross (system: crossSystem:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        py-module = ps: ps.callPackage ./nix/python-challenge-bypass-ristretto.nix {
          inherit (self.legacyPackages.${system}) libchallenge_bypass_ristretto_ffi;
        };
      in {
        # Define our native-compilation packages.
        packages = {
          libchallenge_bypass_ristretto_ffi =
            import ./nix/libchallenge-bypass-ristretto-ffi.nix {
              inherit pkgs;
              fenix = fenix.packages.${system};
              naersk = naersk.lib.${system};
              src = libchallenge_bypass_ristretto_ffi-src;
            };

          python38-challenge-bypass-ristretto = py-module pkgs.python38.pkgs;
          python39-challenge-bypass-ristretto = py-module pkgs.python39.pkgs;
          python310-challenge-bypass-ristretto = py-module pkgs.python310.pkgs;
        };

        # Define our cross-compiled packages.  This currently does not include
        # the Python package because that cross-compilation fails.
        pkgsCross = {
          libchallenge_bypass_ristretto_ffi =
            import ./nix/libchallenge-bypass-ristretto-ffi.nix {
              pkgs = pkgs.pkgsCross.${crossSystem};
              fenix = fenix.packages.${system};
              naersk = naersk.lib.${system};
              src = libchallenge_bypass_ristretto_ffi-src;
            };
        };

        # Define a bunch of checks that can be run automatically to verify the
        # flake outputs are in good shape.
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

        # Define a basic development environment.  It's focused on working on
        # the Python codebase.
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
        };
      });
}
