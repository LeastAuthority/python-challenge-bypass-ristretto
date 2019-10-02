# A basic packaging of the Ristretto FFI library (around the Ristretto Crate
# but that's all handled by Cargo for us).
{ stdenv, fetchFromGitHub, rustPlatform, Security ? null }:
rustPlatform.buildRustPackage rec {
  pname = "ristretto";
  name = "${pname}-${version}";
  # For pkg-config, this has to follow the "RPM version" specification,
  # whatever that is.  Cabal ends up parsing this so really the rules are up
  # to it.  Cabal 2.4 is strict.  Cabal 3.0 is looser.
  version = "0.9.999";
  src = fetchFromGitHub {
    owner = "brave-intl";
    repo = "challenge-bypass-ristretto-ffi";
    # master@HEAD as of this writing.
    rev = "f88d942ddfaf61a4a6703355a77c4ef71bc95c35";
    sha256 = "1gf7ki3q6d15bq71z8s3pc5l2rsp1zk5bqviqlwq7czg674g7zw2";
  };

  # XXX
  cargoSha256 =
    if stdenv.isDarwin
      then "1vfzdvpjj6s94p650zvai8gz89hj5ldrakci5l15n33map1iggch"
      else "1qbfp24d21wg13sgzccwn3ndvrzbydg0janxp7mzkjm4a83v0qij";

  buildInputs = stdenv.lib.optional stdenv.isDarwin Security;

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

Name: libchallenge_bypass_ristretto
Description: Ristretto-Flavored PrivacyPass library
Version: ${version}

Requires:
Libs: -L$out/lib -lchallenge_bypass_ristretto
Cflags: -I$out/include
EOF
  '';
}
