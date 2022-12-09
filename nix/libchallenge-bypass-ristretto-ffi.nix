# A function to create a derivation for the libchallenge_bypass_ristretto_ffi
# library wrapping the challenge-bypass-ristretto-ffi Rust crate.
{
  # An instance of nixpkgs
  pkgs

# The nix-community/fenix packages suitable for use on the build system.
, fenix

# The nix-community/naersk packages suitable for use on the build system.
, naersk

# The challenge-bypass-ristretto-ffi source to build and package.
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

    # Convince the linker to put a SONAME in the dynamic object.
    CARGO_BUILD_RUSTFLAGS =
      "-C link-arg=${setSONAME "lib${libname}.so"}";

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
    # One quirk of cross-compilation is that we don't always know how to
    # compute this string for the (build == host) case.
    CARGO_BUILD_TARGET = rustSystemTarget;

    # It must also use the correct linker for the host system.  Another quirk
    # of cross-compilation is that we don't always know how to tell Rust how
    # to link correctly when (build == host).
    #
    # In principle we could also add this to .cargo/config.toml in the source like:
    #
    #    [target.aarch64-linux-android]
    #    linker = "aarch64-unknown-linux-android-clang"
    #
    # as long as we know in advance all of the targets and what the correct
    # linker to use for them is, which perhaps we do.  However, doing so means
    # patching the source or convincing upstream to take the config.  Perhaps
    # they would - I haven't tried.  Also, I don't understand how the relative
    # path in the above example (which really works!) gets resolved in this
    # build.  In contrast, `ld` here is (and must be, apparently) absolute.
    #
    # Which approach is better, I do not know.
    "CARGO_TARGET_${toEnvVar rustSystemTarget}_LINKER" = ld;
  }));

  # The system to tell cargo/rustc to build for.  Rust calls this the
  # "target".  autotools and nixpkgs call it the "host".
  rustSystemTarget = toRustTarget pkgs.stdenv.hostPlatform.config;

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
  isCrossCompiling = pkgs.buildPlatform != pkgs.hostPlatform;

  # Compute a Cargo "link-arg" value which will cause the linker to set the
  # given name as a SONAME in the resulting object.
  #
  # string -> string
  setSONAME = name: {
    # If we could consitently use a "compiler" (gcc, clang) as a "linker" --
    # instead of sometimes using a "linker" (ld, ld.lld) as a "linker" -- then
    # we probably wouldn't need any branching to figure this out.  But we
    # sometimes use ld and sometimes gcc.
    #
    "lld" = "--soname=${name}";
    "bfd" = "-Wl,-soname,${name}";
  }.${pkgs.stdenv.hostPlatform.linker};

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

  # Read some metadata out of the derivation for the crate (courtesy of
  # naersk, thanks).  We get the package version and name and then
  # post-process the name a bit for a couple different purposes.
  version = crate.version;

  # Suppose that version is semantic and pull off the major so we can put it
  # in the SONAME of the shared object.
  majorVersion = builtins.head (lib.splitString "." version);

  # Since name is like "libfoo-version", we can compute the conventional
  # "pname" by slicing the "-version" suffix off.
  pname = with builtins;
    substring 0 (stringLength crate.name - stringLength version - 1) crate.name;

  # Then we can preserve the name we gave it in the past (kind of carelessly)
  # with underscores instead of dashes.
  libname = "${lib.replaceChars ["-"] ["_"] pname}";

  # The linker that is correct to use for the host system.  This is only used
  # for cross-compilation at the moment, since I don't know the correct value
  # to specify for a native build and Cargo also doesn't seem to need our help
  # in that case.
  ld = "${pkgs.stdenv.cc}/bin/${pkgs.stdenv.cc.targetPrefix}ld";

  # Alias lib for convenience above..
  lib = pkgs.lib;
in
libchallenge_bypass_ristretto_ffi
