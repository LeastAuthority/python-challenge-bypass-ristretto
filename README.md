Python bindings for Brave's [privacy pass](https://github.com/brave-intl/challenge-bypass-ristretto) library
using the provided [ffi](https://github.com/brave-intl/challenge-bypass-ristretto-ffi) APIs.

WARNING: These bindings are in very early stages and is not usable yet.

# How to build

The rust ffi library is a git submodule, so
```
git clone --recursive https://github.com/LeastAuthority/privacypass
```
should clone everything needed to build

```
python setup.py build sdist bdist_wheel
pip install --editable .
```

# License

Currently the same license as the Brave's library, Mozilla Public License v2.

# Copyright

Least Authority TFA GmbH

