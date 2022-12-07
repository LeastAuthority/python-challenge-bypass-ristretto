{ lib
, pkgsForHost
, fenix
, naersk
, src
}:
let
  # The derivation for the package with the header file, shared library, and
  # pkg-config files.
  libchallenge_bypass_ristretto_ffi = crate.overrideAttrs (old: {
    inherit postInstall;
  });

  # The basic Rust crate for libchallenge-bypass-ristretto-ffi.  This is not
  # enough by itself because the purpose of this -ffi package is to expose a C
  # API and ABI.  Crates typically don't do that so after Cargo is done we
  # have to massage the package a bit to get the right pieces in the right
  # place.  All of the compilation (maybe cross-compilation) happens here
  # though.
  crate = buildPackage ({
    inherit src;
  } // (lib.optionalAttrs isCrossCompiling {
    # If we are cross-compiling then tell the Rust toolchain about this fact.
    # It would be more symmetric (and therefore better) if we could always
    # cross-compile (even from a system to itself) but there are some quirks
    # that prevent us from doing so (as of NixOS 22.11 / Rust 1.64).

    # We need it to produce output suitable for the host system.  If we don't
    # tell it this, it will produce output for the build system - which is
    # fine in the native compilation case (it's what "native compilation"
    # means, even).
    #
    # On quirk of cross-compilation is that we don't always know how to
    # compute this string for the (build == host) case.
    CARGO_BUILD_TARGET = rustSystemTarget;

    # It must also use the correct linker for the host system.  Another quirk
    # of cross-compilation is that we don't always know how to tell Rust how
    # to link correctly when (build == host).
    "CARGO_TARGET_${toEnvVar rustSystemTarget}_LINKER" = ld;
  }));

  # The system to tell cargo/rustc to build for.  Rust calls this the
  # "target".  autotools and nixpkgs call it the "host".
  rustSystemTarget = toRustTarget pkgsForHost.stdenv.hostPlatform.config;

  # Map from system quads as known to nixpkgs to system names as understood by
  # the Rust toolchain.
  toRustTarget = s: ({
    "aarch64-unknown-linux-android"    = "aarch64-linux-android";
    "armv7a-unknown-linux-androideabi" = "armv7-linux-androideabi";
    "x86_64-unknown-linux-gnu"         = "x86_64-unknown-linux-gnu";
  }).${s};

  # Notice whether we are cross-compiling or not.  There are some asymmetries
  # between native compilation and cross-compilation which need special
  # handling and this lets us know whether to apply that handling or not.
  isCrossCompiling = pkgsForHost.buildPlatform != pkgsForHost.hostPlatform;

  # Convert a string that represents a Cargo system "target" into a form where
  # it can be interpolated into an environment variable for Cargo that tells
  # Cargo which linker to use.  For example::
  #
  #  toEnvVar "aarch64-linux-android" = "AARCH64_LINUX_ANDROID"
  #
  toEnvVar = s: lib.replaceChars ["-"] ["_"] (lib.toUpper s);

  # Assemble a Rust build toolchain that can build for the "target" system.
  toolchain = with fenix; combine [
    minimal.cargo
    minimal.rustc
    targets.${rustSystemTarget}.latest.rust-std
  ];

  # Get a customized (to use our configuration of the toolchain) Rust crate
  # building function from Naersk.
  buildPackage = (naersk.override {
    cargo = toolchain;
    rustc = toolchain;
  }).buildPackage;

  # Shuffle the header file and shared library files around into appropriate
  # places in the final package.  Also, generate a pkg-config file describing
  # it.
  postInstall = ''
    # Provide the ffi header file things can be compiled against the library.
    mkdir -p $out/include $out/lib
    cp src/lib.h $out/include/

    cp target/${
      lib.optionalString isCrossCompiling (rustSystemTarget + "/")
    }release/lib${libname}.so $out/lib

    # Provide a pkgconfig file so build systems can find the header and library.
    mkdir -p $out/lib/pkgconfig
    cat > $out/lib/pkgconfig/lib${libname}.pc <<EOF
prefix=$out
exec_prefix=$out
libdir=$out/lib
sharedlibdir=$out/lib
includedir=$out/include

Name: lib${libname}
Description: Ristretto-Flavored PrivacyPass library
Version: ${version}

Requires:
Libs: -L$out/lib -l${libname}
Cflags: -I$out/include
EOF
'';

  version = crate.version;
  pname = with builtins;
    substring 0 (stringLength crate.name - stringLength version - 1) crate.name;
  libname = "${lib.replaceChars ["-"] ["_"] pname}";

  ld = "${pkgsForHost.stdenv.cc}/bin/${pkgsForHost.stdenv.hostPlatform.config}-ld";
in
libchallenge_bypass_ristretto_ffi
