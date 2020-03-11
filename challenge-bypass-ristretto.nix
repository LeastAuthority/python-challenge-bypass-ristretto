{ pkgs, stdenv, lib, darwin }:
let
  withSecurity = attrs: {
    buildInputs = lib.optional stdenv.isDarwin darwin.apple_sdk.frameworks.Security;
  };
  defaultCrateOverrides = pkgs.defaultCrateOverrides // {
    curve25519-dalek = withSecurity;
    challenge-bypass-ristretto-ffi = withSecurity;
  };
  challenge-bypass-ristretto = pkgs.callPackage ./generated-challenge-bypass-ristretto.nix {
    inherit defaultCrateOverrides;
  };
in
challenge-bypass-ristretto.rootCrate.build.overrideAttrs (old: rec {
  pname = "libchallenge_bypass_ristretto";
  version = "1.0.0-pre.1";
  postInstall = ''
  mkdir $out/include
  cp src/lib.h $out/include/

  mkdir $out/lib/pkgconfig
  cat > $out/lib/pkgconfig/${pname}.pc <<EOF
prefix=$out
exec_prefix=$out
libdir=$out/lib
sharedlibdir=$out/lib
includedir=$out/include

Name: ${pname}
Description: Ristretto-Flavored PrivacyPass library
Version: ${version}

Requires:
Libs: -L$out/lib -lchallenge_bypass_ristretto
Cflags: -I$out/include
EOF
  '';
})
