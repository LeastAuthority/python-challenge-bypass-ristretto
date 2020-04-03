{ pkgs, stdenv, darwin }:
let
  withSecurity = attrs: {
    buildInputs = stdenv.lib.optional stdenv.isDarwin darwin.apple_sdk.frameworks.Security;
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

  challenge-bypass-ristretto = pkgs.callPackage ./generated-challenge-bypass-ristretto.nix {
    # Get all of the crates built with our preferences accounted for by
    # supplying our customized buildRustCrate.
    inherit buildRustCrate;
  };
in
challenge-bypass-ristretto.rootCrate.build.overrideAttrs (old: rec {
  pname = "libchallenge_bypass_ristretto_ffi";
  # Version constrained by
  # https://hackage.haskell.org/package/base-4.12.0.0/docs/Data-Version.html
  # until you upgrade to Cabal 3.0.0.
  version = "1.0.0-pre1";

  # crate2nix generates expressions that want to use the local source files.
  # Git submodules make everything more complicated though so I'd rather just
  # always say we built from the canonical revision from Github.  Override the
  # src defined in the generated expression to say that.
  src = pkgs.fetchFromGitHub {
    owner = "brave-intl";
    repo = "challenge-bypass-ristretto-ffi";
    rev = "f88d942ddfaf61a4a6703355a77c4ef71bc95c35";
    sha256 = "1gf7ki3q6d15bq71z8s3pc5l2rsp1zk5bqviqlwq7czg674g7zw2";
  };

  postInstall = ''
  # Newer nixpkgs give Rust crates a "lib" output where we need to put
  # everything.  Older nixpkgs have lib set to something else (the path to the
  # .so, it seems) and only have the "out" output and things need to go there.
  if [ ! -d $lib ]; then
    lib=$out/lib
  fi

  # Expose the header file and pkg-config so other bindings can be built
  # against this one. It might be better to have a separate dev output but I
  # don't know how to do that.
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
Libs: -L$lib -lchallenge_bypass_ristretto_ffi
Cflags: -I$lib/include
EOF
  '';
})
