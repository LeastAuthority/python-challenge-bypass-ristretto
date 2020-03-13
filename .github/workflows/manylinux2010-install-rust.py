import subprocess
print(subprocess.check_output(["/bin/bash", "-c", """
curl --tlsv1.2 -sSf https://sh.rustup.rs > /tmp/rustup-init
sh /tmp/rustup-init -y --default-host x86_64-unknown-linux-gnu --default-toolchain stable
rm /tmp/rustup-init
"""]))

import os
os.environ["PATH"] += ":/github/home/.cargo/bin"
