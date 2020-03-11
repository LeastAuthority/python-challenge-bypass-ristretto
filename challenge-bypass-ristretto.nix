{ pkgs, stdenv, darwin }:
let
  withSecurity = attrs: {
    buildInputs = stdenv.lib.optional stdenv.isDarwin darwin.apple_sdk.frameworks.Security;
  };
  disableStripping = attrs: attrs // { dontStrip = true; };
  defaultCrateOverrides = pkgs.defaultCrateOverrides // {
    curve25519-dalek = withSecurity;
    challenge-bypass-ristretto-ffi = withSecurity;
  };
  buildRustCrate = (args: pkgs.buildRustCrate (args // {
    dontStrip = true;
  }));
  challenge-bypass-ristretto = pkgs.callPackage ./generated-challenge-bypass-ristretto.nix {
    inherit defaultCrateOverrides;
    inherit buildRustCrate;
  };
in
challenge-bypass-ristretto.rootCrate.build.overrideAttrs (old: rec {
  pname = "libchallenge_bypass_ristretto";
  version = "1.0.0-pre.1";
  postInstall = ''
  # Newer nixpkgs give Rust crates a "lib" output where we need to put
  # everything.  Older nixpkgs have lib set to something else (the path to the
  # .so, it seems) and only have the "out" output and things need to go there.
  if [ ! -d $lib ]; then
    lib=$out/lib
  fi

  mkdir $lib/include
  cp src/lib.h $lib/include/

  mkdir $lib/pkgconfig
  cat > $lib/pkgconfig/${pname}.pc <<EOF
prefix=$lib
exec_prefix=$lib
libdir=$lib
sharedlibdir=$lib
includedir=$lib/include

Name: ${pname}
Description: Ristretto-Flavored PrivacyPass library
Version: ${version}

Requires:
Libs: -L$lib -lchallenge_bypass_ristretto
Cflags: -I$lib/include
EOF
  '';
})
