#!/usr/bin/env sh

curl --tlsv1.2 -sSf https://sh.rustup.rs > /tmp/rustup-init
sh /tmp/rustup-init -y --default-host x86_64-unknown-linux-gnu --default-toolchain stable
rm /tmp/rustup-init

export PATH="$PATH":/github/home/.cargo/bin
