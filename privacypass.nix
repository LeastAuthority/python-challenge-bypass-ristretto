{ ristretto, git, python, pythonPackages, setuptools_scm, milksnake, cffi }:
pythonPackages.buildPythonPackage rec {
  version = "0.0.0";
  pname = "privacypass";
  name = "${pname}-${version}";
  src = ./.;

  postUnpack = ''
  substituteInPlace $sourceRoot/setup.py \
      --replace "['cargo', 'build', '--release']" "['sh', '-c', ':']" \
      --replace "./challenge-bypass-ristretto-ffi" "/" \
      --replace "target/release" "${ristretto}/lib" \
      --replace "./src" "${src}/challenge-bypass-ristretto-ffi/src"
  '';

  nativeBuildInputs = [
    git
  ];

  propagatedNativeBuildInputs = [
    ristretto
  ];

  propagatedBuildInputs = [
    cffi
  ];

  buildInputs = [
    setuptools_scm
    milksnake
  ];

}
