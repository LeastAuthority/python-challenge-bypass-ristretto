from setuptools import setup
def build_native(spec):
    # build rust library
    build = spec.add_external_build(
        cmd=['cargo', 'build', '--release'],
        path='./challenge-bypass-ristretto-ffi'
    )
    spec.add_cffi_module(
        module_path='privacypass._native',
        dylib=lambda: build.find_dylib('challenge_bypass_ristretto', in_path='target/release'),
        header_filename=lambda: build.find_header('lib.h', in_path='./src'),
        rtld_flags=['NOW', 'NODELETE']
    )

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='privacypass',
    packages=['privacypass'],
    zip_safe=False,
    platforms='any',
    setup_requires=['milksnake', 'setuptools_scm'],
    install_requires=['milksnake'],
    use_scm_version=True,
    url='https://github.com/',
    milksnake_tasks=[
        build_native
    ],
    author='Ramakrishnan Muthukrishnan',
    author_email='ram@leastauthority.com',
    license = 'Mozilla Public License v2',
    description='Privacypass library.',
    long_description=readme(),
    long_description_content_type='text/markdown'
)
