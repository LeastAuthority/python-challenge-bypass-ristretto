from setuptools import setup
def build_native(spec):
    # build rust library
    build = spec.add_external_build(
        cmd=['cargo', 'build', '--release'],
        path='./challenge-bypass-ristretto-ffi'
    )
    spec.add_cffi_module(
        # The Python module name
        module_path='challenge_bypass_ristretto._native',
        # The C library being bound
        dylib=lambda: build.find_dylib('challenge_bypass_ristretto_ffi', in_path='target/release'),
        header_filename=lambda: build.find_header('lib.h', in_path='./src'),
        rtld_flags=['NOW', 'NODELETE']
    )

def readme():
    with open('README.md') as f:
        return f.read()

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
    use_scm_version=True,
    url='https://github.com/',
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
