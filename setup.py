from setuptools import find_packages, setup

PACKAGE_NAME = 'olaaf-transient'
VERSION = '0.35.1'
AUTHOR = 'Open Law Library'
AUTHOR_EMAIL = 'info@openlawlib.org'
DESCRIPTION = 'Implementation of transient authentication'
KEYWORDS = 'transient authentication'
URL = 'https://github.com/openlawlibrary/OLAAF-Transient/tree/master'

with open('README.md', encoding='utf-8') as file_object:
  long_description = file_object.read()

packages = find_packages()

ci_require = [
    "pylint==2.3.1",
    "bandit==1.6.0",
    "coverage==4.5.3",
    "pytest-cov==2.7.1",
]

dev_require = [
    "autopep8==1.4.4",
    "pylint==2.3.1",
    "bandit==1.6.0",
]

tests_require = [
    "pytest-django==4.*",
    "pytest==6.*",
]

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    keywords=KEYWORDS,
    packages=packages,
    include_package_data=True,
    data_files=[
        ('lib/site-packages/olaaf_transient', [
            './LICENSE.txt',
            './README.md'
        ])
    ],
    zip_safe=False,
    install_requires=[
        "Django == 3.2.*",
        "GitPython >= 2.1.11",
        "selenium ~= 3.0",
        "lxml >= 4.3",
        "taf == 0.33.0",
    ],
    extras_require={
        'ci': ci_require,
        'test': tests_require,
        'dev': dev_require
    },
    tests_require=tests_require,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'Topic :: Software Development',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)
