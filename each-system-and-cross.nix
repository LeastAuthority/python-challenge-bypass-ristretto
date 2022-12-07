{
  lib

# A helper for evaluating the builder against a number of build systems.
, flake-utils

# A list of nixpkgs system identifiers as strings (tuples, triples, maybe
# quads, who knows) for which builds will be defined.
, buildSystems ? [ "x86_64-linux" ] # flake-utils.lib.defaultSystems

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
      packages = builder system crossSystem;
    in {
      legacyPackages.${system} = packages // (
        if packages ? pkgsCross
        then { pkgsCross.${crossSystem} = packages.pkgsCross; }
        else {}
      );
    };

  args = lib.cartesianProductOfSets {
    system = buildSystems;
    crossSystem = crossSystems;
  };
in
lib.foldl' lib.recursiveUpdate {} (map f args)
