from setuptools import setup, find_packages

_VERSION = '0.0.1'

setup(
    name='PyZE',
    version=_VERSION,
    description='Unofficial client and API for Renault ZE',
    author='James Muscat',
    author_email='jamesremuscat@gmail.com',
    url='https://github.com/jamesremuscat/pyze',
    packages=find_packages('src', exclude=["*.tests"]) + [''],
    package_dir={'pyze': 'src/pyze'},
    long_description="Unofficial client and API for Renault ZE.",
    install_requires=[
        "requests"
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest'
    ],
    entry_points={
        'console_scripts': [
        ],
    }
)
