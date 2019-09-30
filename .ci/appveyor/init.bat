Rem Get a Rust build toolchain.
choco install rustup.install --version 1.19.0

Rem Build challenge-bypass-ristretto-ffi.
cd challenge-bypass-ristretto-ffi
cargo build --release

Rem Install it so we can link the Python extension against it.
make install
