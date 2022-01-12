let
  sources = import nix/sources.nix;
in
{ pkgs ? import sources.nixpkgs { }
, stdenv ? pkgs.stdenv
, lib ? pkgs.lib
, darwin ? pkgs.darwin
, src ? sources.challenge-bypass-ristretto-ffi
}:
let
  withSecurity = attrs: {
    buildInputs = lib.optional stdenv.isDarwin darwin.apple_sdk.frameworks.Security;
  };
  defaultCrateOverrides = pkgs.defaultCrateOverrides // {
    curve25519-dalek = withSecurity;
    challenge-bypass-ristretto-ffi = withSecurity;
  };

  # Create a buildRustCrate that knows about our crate overrides to provide
  # the Security framework on macOS.  The crates that require it come from the
  # crate2nix-generated packaging (generated-challenge-bypass-ristretto.nix)
  # so nixpkgs doesn't know about the extra build dependencies and the crate
  # metadata doesn't know anything about native dependencies either.
  #
  # We pass defaultCrateOverrides in like this instead of passing it to
  # generated-challenge-bypass-ristretto.nix below (which does accept it)
  # because the latter causes the generated code to want to use
  # buildRustCrate.override itself but we're going to destroy that ability a
  # few lines below.
  buildRustCrateWithOverrides = pkgs.buildRustCrate.override {
    inherit defaultCrateOverrides;
  };

  # Further customize buildRustCrate by having it decline to strip any of the
  # binaries.  Stripping Rust rlibs on macOS corrupts them sometimes
  # (<https://github.com/rust-lang/rust/issues/42857>).  We could make this a
  # macOS-only thing but binary size isn't really the primary concern at this
  # point in time.
  #
  # buildRustCrate doesn't specifically recognize dontStrip but extra
  # attributes just end up on the derivation where the "strip.sh" setup-hook
  # respects it.
  #
  # Here is where we destroy the buildRustCrate.override by turning it into a
  # function (it was a set before, of course... maybe a "functor"?).
  buildRustCrate = args: buildRustCrateWithOverrides (args // { dontStrip = true; });

  challenge-bypass-ristretto' = pkgs.callPackage ./generated-challenge-bypass-ristretto.nix {
    # Get all of the crates built with our preferences accounted for by
    # supplying our customized buildRustCrate.
    inherit buildRustCrate;
  };

  # Note: challenge-bypass-ristretto and tests are mutually recursive because
  # tests needs the lib output but needs to be defined inside the derivation
  # itself.
  challenge-bypass-ristretto = challenge-bypass-ristretto'.rootCrate.build.overrideAttrs (old: rec {
    pname = "libchallenge_bypass_ristretto_ffi";
    # Version constrained by
    # https://hackage.haskell.org/package/base-4.12.0.0/docs/Data-Version.html
    # until you upgrade to Cabal 3.0.0.
    version = "1.0.0-pre3";

    # crate2nix generates expressions that want to use the local source files.
    # Git submodules make everything more complicated though so I'd rather just
    # always say we built from the canonical revision from Github.  Override the
    # src defined in the generated expression to say that.
    inherit src;

    postInstall = ''
    # Provide the ffi header file things can be compiled against the library.
    mkdir -p $lib/include
    cp src/lib.h $lib/include/

    # Provide a pkgconfig file so build systems can find the header and library.
    mkdir -p $lib/lib/pkgconfig
    cat > $lib/lib/pkgconfig/${pname}.pc <<EOF
prefix=$lib
exec_prefix=$lib
libdir=$lib
sharedlibdir=$lib
includedir=$lib/include

Name: ${pname}
Description: Ristretto-Flavored PrivacyPass library
Version: ${version}

Requires:
Libs: -L$lib -lchallenge_bypass_ristretto_ffi
Cflags: -I$lib/include
EOF
    '';
    passthru = {
      inherit tests;
    };
  });

  tests =
    let
      inherit (challenge-bypass-ristretto) pname;
    in
      {
        simple = pkgs.runCommand "${pname}-tests" {
          nativeBuildInputs = [
            # Putting pkg-config here causes the hooks that set
            # PKG_CONFIG_PATH to be set.
            pkgs.pkg-config
            challenge-bypass-ristretto.lib
          ];
        } ''
# Verify that we are supplying the dynamic libraries in a discoverable way.
if ! pkg-config --exists ${pname}; then
  echo "Failed to discover ${pname} with pkg-config"
  exit 1
fi
if ! pkg-config --validate ${pname}; then
  echo "Failed to validate ${pname}.pc with pkg-config"
  exit 1
fi
echo "passed" > "$out"
'';
  };

in
challenge-bypass-ristretto
