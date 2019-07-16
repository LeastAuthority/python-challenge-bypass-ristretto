{ ristretto, git, python, pythonPackages, setuptools_scm, milksnake }:
pythonPackages.buildPythonPackage rec {
  version = "0.0.0";
  pname = "privacypass";
  name = "${pname}-${version}";
  src = ./.;

  nativeBuildInputs = [
    git
    ristretto
  ];

  buildInputs = [
    setuptools_scm
    milksnake
  ];
}
