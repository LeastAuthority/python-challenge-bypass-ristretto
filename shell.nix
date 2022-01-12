let
  sources = import nix/sources.nix;
in
{ pkgs ? import sources.nixpkgs { }
, python ? pkgs.python2
}:
let
  challenge-bypass-ristretto-ffi = pkgs.callPackage ./challenge-bypass-ristretto.nix {
    inherit pkgs;
  };
  python-challenge-bypass-ristretto = pkgs.callPackage ./. {
    inherit pkgs challenge-bypass-ristretto-ffi;
    pythonPackages = python.pkgs;

  };
in
pkgs.mkShell {
  nativeBuildInputs = with pkgs; [
    cargo
    pkgconfig
    challenge-bypass-ristretto-ffi.lib
  ];
  buildInputs = [
    (python.withPackages (ps: with ps; [
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
}
