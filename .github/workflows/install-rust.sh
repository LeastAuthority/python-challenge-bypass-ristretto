# Source this so I can fix your PATH and stuff.

curl --tlsv1.2 -sSf https://sh.rustup.rs > /tmp/rustup-init
sh /tmp/rustup-init -y --default-host x86_64-unknown-linux-gnu --default-toolchain stable
rm /tmp/rustup-init

. "$HOME"/.cargo/env
