{
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
