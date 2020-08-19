from setuptools import setup, find_packages

_VERSION = '0.6.0'

setup(
    name='PyZE',
    version=_VERSION,
    description='Unofficial client and API for Renault ZE',
    author='James Muscat',
    author_email='jamesremuscat@gmail.com',
    url='https://github.com/jamesremuscat/pyze',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    long_description="Unofficial client and API for Renault ZE.",
    install_requires=[
        'dateparser',
        'pyjwt',
        'python-dateutil',
        'requests',
        'simplejson',
        'tabulate',
        'tzlocal'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pytest-cov'
    ],
    entry_points={
        'console_scripts': [
            'pyze = pyze.cli.__main__:main'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
