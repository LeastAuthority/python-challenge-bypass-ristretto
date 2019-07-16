{ fetchFromGitHub, rustPlatform }:
rustPlatform.buildRustPackage rec {
  name = "ristretto-${version}";
  version = "1.0.0-pre.1";
  src = fetchFromGitHub {
    owner = "brave-intl";
    repo = "challenge-bypass-ristretto-ffi";
    rev = "${version}";
    sha256 = "06lxs4rxy4i9l4wjm1wqi4dnqscpzgp7v24ayp524gwgf3yc1sd9";
  };
  cargoSha256 = "1qbfp24d21wg13sgzccwn3ndvrzbydg0janxp7mzkjm4a83v0qij";
}
