{ fetchFromGitHub, rustPlatform }:
rustPlatform.buildRustPackage rec {
  name = "ristretto-${version}";
  version = "1.0.0-pre.0";
  src = fetchFromGitHub {
    owner = "brave-intl";
    repo = "challenge-bypass-ristretto-ffi";
    # Pick the most recent version I can actually get to build.
    # https://github.com/brave-intl/challenge-bypass-ristretto-ffi/issues/48
    rev = "a4b1ac1262920e41833425908e59d7ebadb31e19";
    sha256 = "0bwph820gnha6hhhgb9zb8qxlp1958b9rikwm4480mnij7mmb778";
  };
  cargoSha256 = "1qbfp24d21wg13sgzccwn3ndvrzbydg0janxp7mzkjm4a83v0qij";
}
