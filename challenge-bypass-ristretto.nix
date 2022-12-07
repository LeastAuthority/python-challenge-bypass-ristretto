{ pkgs
, system
, crossSystem
, rustSystemTarget
, fenix
, naersk
, src
}:
let
  toEnvVar = s: pkgs.lib.replaceChars ["-"] ["_"] (pkgs.lib.toUpper s);

  libchallenge_bypass_ristretto_ffi = crate.overrideAttrs (old: {
    inherit postInstall;
  });

  crate = buildPackage {
    inherit src;

    # Tell cargo/rustc what system to build for.
    CARGO_BUILD_TARGET = rustSystemTarget;

    # And tell it what program to use to link for that system.
    "CARGO_TARGET_${toEnvVar rustSystemTarget}_LINKER" = ld;
  };

  pname = "libchallenge_bypass_ristretto_ffi";
  version = "1.0.0-pre3";

  toolchain = with fenix.packages.${system}; combine [
    minimal.cargo
    minimal.rustc
    targets.${rustSystemTarget}.latest.rust-std
  ];

  buildPackage = (naersk.lib.${system}.override {
    cargo = toolchain;
    rustc = toolchain;
  }).buildPackage;

  postInstall = ''
    # Provide the ffi header file things can be compiled against the library.
    mkdir -p $out/include $out/lib
    cp src/lib.h $out/include/

    cp target/${rustSystemTarget}/release/${pname}.so $out/lib

    # Provide a pkgconfig file so build systems can find the header and library.
    mkdir -p $out/lib/pkgconfig
    cat > $out/lib/pkgconfig/${pname}.pc <<EOF
prefix=$out
exec_prefix=$out
libdir=$out/lib
sharedlibdir=$out/lib
includedir=$out/include

Name: ${pname}
Description: Ristretto-Flavored PrivacyPass library
Version: ${version}

Requires:
Libs: -L$out/lib -lchallenge_bypass_ristretto_ffi
Cflags: -I$out/include
EOF
'';

  clangSystemQuad = ({
    "aarch64-linux-android" = "aarch64-unknown-linux-android";
    "armv7-linux-androideabi" = "foo";
  }).${rustSystemTarget};

  ld = "${pkgs.pkgsCross.${crossSystem}.stdenv.cc}/bin/${clangSystemQuad}-ld";
in
libchallenge_bypass_ristretto_ffi
