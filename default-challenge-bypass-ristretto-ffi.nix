# Provide a no-argument function for building the underlying
# challenge-bypass-ristretto ffi bindings.
#
# This defaults to pinning a pretty new version of nixpkgs because from around
# 19.09 and older the nixpkgs Rust build system does something weird with the
# library output and I can't figure out how to make packaging consistent
# between 19.09-and-older and newer-than-19.09.
#
# Supply your own nixpkgs if you want, as long as it's newer than 19.09.
let
  nixpkgs = builtins.fetchTarball {
    name = "nixpkgs";
    url = "https://github.com/NixOS/nixpkgs/archive/refs/tags/21.05.tar.gz";
    sha256 = "1ckzhh24mgz6jd1xhfgx0i9mijk6xjqxwsshnvq789xsavrmsc36";
  };
in
{ pkgs ? import nixpkgs }:
pkgs.callPackage ./challenge-bypass-ristretto.nix { }
