from setuptools import setup

_DYLIB_NAME = 'challenge_bypass_ristretto_ffi'

def build_native(spec):
    # build rust library
    cargo_build = ['cargo', 'build', '--release']
    build = spec.add_external_build(
        cmd=['sh', '-c', 'echo "Running cargo build..."; {}'.format(" ".join(cargo_build))],
        path='./challenge-bypass-ristretto-ffi'
    )
    spec.add_cffi_module(
        # The Python module name
        module_path='challenge_bypass_ristretto._native',
        # The C library being bound
        dylib=lambda: build.find_dylib(_DYLIB_NAME, in_path='target/release'),
        header_filename=lambda: build.find_header('lib.h', in_path='./src'),
        rtld_flags=['NOW', 'NODELETE']
    )

def readme():
    with open('README.md') as f:
        return f.read()

def _myversion():
    return dict(
        # Unfortunately PyPI rejects package versions with a local part.
        # Define a local scheme that never has a local part.
        local_scheme=lambda version: "",
    )

setup(
    name='python-challenge-bypass-ristretto',
    packages=['challenge_bypass_ristretto', 'challenge_bypass_ristretto.tests'],
    zip_safe=False,
    platforms='any',
    setup_requires=['milksnake', 'setuptools_scm'],
    install_requires=['cffi', 'attrs'],
    extras_require={
        "tests": [
            "testtools",
            "hypothesis",
        ],
    },
    use_scm_version=_myversion,
    url='https://github.com/LeastAuthority/python-challenge-bypass-ristretto',
    milksnake_tasks=[
        build_native
    ],
    author='Ramakrishnan Muthukrishnan',
    author_email='ram@leastauthority.com',
    license = 'Mozilla Public License v2',
    description='Bindings for Brave\'s Ristretto-flavored Privacy Pass library.',
    long_description=readme(),
    long_description_content_type='text/markdown'
)
