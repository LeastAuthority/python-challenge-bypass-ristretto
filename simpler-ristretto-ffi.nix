{ buildRustCrate, buildRustCrateHelpers, crates }:
buildRustCrate {
  crateName = "libchallenge_bypass_ristretto_ffi";
  version = "1.0.0-pre3";
  description = "good stuff";
  authors = [ "some people"; ];
  sha256 = "1zqq1157c51f53ga4p9l4dd8ax6md27h1xjrjp2plkvml5iymks5";
  dependencies = buildRustCrateHelpers.mapFeatures [
    # crypto-mac = "0.10"
    # curve25519-dalek = { version = "3", default-features = false }
    # digest = "0.9"
    # hmac = "0.10"
    # rand = { version = "0.7", default-features = false }
    (
    # rand_core = "0.5.1"
    # rand_chacha = "0.2.2"
    # subtle = { version = "^2.2", default-features = false }
    # zeroize = "1.3"
  ];
}
