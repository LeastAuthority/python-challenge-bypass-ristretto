# A basic packaging of the Ristretto FFI library (around the Ristretto Crate
# but that's all handled by Cargo for us).
{ fetchFromGitHub, rustPlatform }:
rustPlatform.buildRustPackage rec {
  name = "ristretto-${version}";
  version = "1.0.0-pre.1";
  src = fetchFromGitHub {
    owner = "brave-intl";
    repo = "challenge-bypass-ristretto-ffi";
    # master@HEAD as of this writing.
    rev = "f88d942ddfaf61a4a6703355a77c4ef71bc95c35";
    sha256 = "1gf7ki3q6d15bq71z8s3pc5l2rsp1zk5bqviqlwq7czg674g7zw2";
  };
  cargoSha256 = "1qbfp24d21wg13sgzccwn3ndvrzbydg0janxp7mzkjm4a83v0qij";
}
