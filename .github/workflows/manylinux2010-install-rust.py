import subprocess
print(subprocess.check_output(["/bin/bash", "-c", """
curl --tlsv1.2 -sSf https://sh.rustup.rs > /tmp/rustup-init
sh /tmp/rustup-init -y --default-host x86_64-unknown-linux-gnu --default-toolchain stable
rm /tmp/rustup-init

# The change to run this script patched into setup.py changes the project
# version by making the working copy dirty.  Clean the working copy.
git reset --hard
"""]))

import os
os.environ["PATH"] += ":/github/home/.cargo/bin"
