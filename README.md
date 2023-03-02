# python-challenge-bypass-ristretto

Python bindings for Brave's [privacy pass](https://github.com/brave-intl/challenge-bypass-ristretto) library
using the provided [ffi](https://github.com/brave-intl/challenge-bypass-ristretto-ffi) APIs.

# Usage

The API largely mirrors that of the underlying Rust library with a few classes thrown in.
For example:

```
>>> from challenge_bypass_ristretto import  RandomToken
>>> print(RandomToken.create().blind().encode_base64())
QxE220HfZvvOJSNdDx3hgYNfQntxeT+mkRr55LNMNyYdXdFOfkrHRoQz+MXlqfyoiWPWc7dG3k4sa5ZWDv+9WtPkZf1uZVhTwBW4YKgyPXK3jj4Ig7kKDjcGMGtoCdgJ
```

# How to install

Binary wheels for Linux (manylinux2010), macOS, and Windows are distributed on PyPI.

```
pip install python-challenge-bypass-ristretto
```

# How to build

The Rust FFI library is a git submodule, so to clone all sources needed for a build:

```
git clone --recursive https://github.com/LeastAuthority/python-challenge-bypass-ristretto
```

Then, with the Rust and Python toolchains installed:

```
python setup.py build sdist bdist_wheel
pip install --editable .
```

There is also Nix-based package which manages most of this complexity for you and only requires a checkout:

```
nix build
```

# License

Currently the same license as the Brave's library, Mozilla Public License v2.

# Copyright

Least Authority TFA GmbH
