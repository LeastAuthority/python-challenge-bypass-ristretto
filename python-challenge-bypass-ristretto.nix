# A basic packaging of this very project: Python bindings to the Rust
# Ristretto implementation.
{ ristretto, git, python, pythonPackages, setuptools_scm, milksnake, cffi, attrs, testtools, hypothesis }:
let
  ristretto-lib = if ristretto ? lib then ristretto.lib else ristretto;
in
pythonPackages.buildPythonPackage rec {
  version = "0.0.0";
  pname = "python-challenge-bypass-ristretto";
  name = "${pname}-${version}";
  src = ./.;

  # We hack up setup.py a bit.  We're going to supply a pre-built Ristretto
  # FFI library.  We don't want Python distutils to build it for us.  This
  # gives us more control and is easier than trying to mash Python and Rust
  # build environments into one.
  postUnpack = ''
  substituteInPlace $sourceRoot/setup.py \
      --replace "['cargo', 'build', '--release']" "['sh', '-c', ':']" \
      --replace "./challenge-bypass-ristretto-ffi" "/" \
      --replace "target/release" "${ristretto-lib}/lib" \
      --replace "./src" "${ristretto.src}/src"
  '';

  nativeBuildInputs = [
    # necessary for setuptools_scm to compute the version being built
    git
  ];

  propagatedNativeBuildInputs = [
    # here's the pre-built library mentioned above
    ristretto-lib
  ];

  propagatedBuildInputs = [
    # the bindings are cffi-based
    cffi
    attrs
  ];

  buildInputs = [
    # required to provide metadata for the build
    setuptools_scm
    # required to build the cffi extension module
    milksnake
  ];

  checkInputs = [
    testtools
    hypothesis
  ];
}
