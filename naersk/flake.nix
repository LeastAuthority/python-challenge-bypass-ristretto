{
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    naersk.url = "github:nix-community/naersk";
    challenge-bypass-ristretto-ffi-src = {
      url = "github:brave-intl/challenge-bypass-ristretto-ffi?rev=f88d942ddfaf61a4a6703355a77c4ef71bc95c35";
      flake = false;
    };
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, flake-utils, naersk, nixpkgs, challenge-bypass-ristretto-ffi-src }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = (import nixpkgs) {
          inherit system;
        };

        naersk' = pkgs.callPackage naersk {};

      in rec {
        # For `nix build` & `nix run`:
        defaultPackage = naersk'.buildPackage {
          src = challenge-bypass-ristretto-ffi-src;
        };
      }
    );
}
