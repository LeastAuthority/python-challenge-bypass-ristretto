# Apply a derivation building function to the product of some build and host
# systems to help with the definition of cross-compiled versions of the
# derivation.
#
# Consider the type aliases::
#
#   System = string
#     The name of a system (as in "x86_64-linux")
#
#   Derivation = attrset
#     A nix derivation value
#
#   PackageName = string
#     The name of a package in a package set
#
#   PackageSet = AttrSet PackageName Derivation
#
#     A collection of named packages.
#
#   CrossPackageSet = AttrSet
#     { packages  :: PackageSet
#     , pkgsCross :: PackageSet
#     , devShells :: PackageSet
#     }
#
# and a builder function::
#
#   f :: System -> System -> CrossPackageSet
#
# this call::
#
#   eachSystemAndCross {
#     inherit (pkgs) lib;
#     buildSystems = [ "x86_64-linux" ];
#     crossSystems = [ "i686-linux" "aarch64-linux" "riscv-linux" ];
#   } f
#
# will return a value which can be returned from a flake `outputs` function
# which defines cross-compiled packages for i686-linux, aarch64-linux, and
# riscv-linux for an x86_64-linux build system.
#
# Derivations in the `packages` attribute in the return value of `f` will be
# present as normal, native-compilation `packages` in the output.
#
# Derivations in the `pkgsCross` attribute in the return value of `f` will be
# exposed via `legacyPackages` beneath `pkgsCross.${crossSystem}`.
#
# Derivations in the `devShells` attribute in the return value of `f` will be
# present as normal, native-compilation `devShells` in the output.
{
# the nixpkgs library
  lib

# A list of nixpkgs system identifiers as strings (tuples, triples, maybe
# quads, who knows) for which builds will be defined.
, buildSystems

# A list of nixpkgs system identifiers as strings (tuples, triples, maybe
# quads, who knows) for which to define cross-compiled packages.
, crossSystems
}:
# Return a function that takes the builder function, which is a function that
# takes a system (the build system) and a cross system (the host system) and
# returns an attrset that includes `pkgsCross` which is an attrset with keys
# giving package names and values giving derivations for cross-compiling that
# package on the build system for the host system.
builder:
let
  f = { system, crossSystem }:
    let
      buildResult = builder system crossSystem;
    in rec {
      legacyPackages.${system} = buildResult.packages // (
        if buildResult ? pkgsCross
        then { pkgsCross.${crossSystem} = buildResult.pkgsCross; }
        else {}
      );

      # Nesting beneath packages makes `nix flake ...` commands angry.  Only
      # put the plain derivations here.
      packages.${system} =
        lib.filterAttrs (k: v: lib.isDerivation v) (legacyPackages.${system});

      # And propagate any devShells defined, ignoring crossSystem because it
      # doesn't make sense for devShells I guess?
      devShells.${system} =
        lib.optionalAttrs (buildResult ? devShells) buildResult.devShells;
    };

  args = lib.cartesianProductOfSets {
    system = buildSystems;
    crossSystem = crossSystems;
  };
in
lib.foldl' lib.recursiveUpdate {} (map f args)
