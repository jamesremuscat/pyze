from setuptools import setup, find_packages

_VERSION = '0.1.0'

setup(
    name='PyZE',
    version=_VERSION,
    description='Unofficial client and API for Renault ZE',
    author='James Muscat',
    author_email='jamesremuscat@gmail.com',
    url='https://github.com/jamesremuscat/pyze',
    packages=['pyze'],
    package_dir={'': 'src'},
    long_description="Unofficial client and API for Renault ZE.",
    install_requires=[
        'dateparser',
        'pyjwt',
        'python-dateutil',
        'requests',
        'simplejson',
        'tabulate'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest'
    ],
    entry_points={
        'console_scripts': [
            'pyze = pyze.cli.__main__:main'
        ],
    }
)
