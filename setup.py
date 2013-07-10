#!/usr/bin/env python

"""python-manta Python package setup script"""

import os
import sys
#import distutils
#from distutils.core import setup
from setuptools import setup

assert sys.version_info > (2, 4), \
    "python-manta does not support this Python version: %s" % sys.version

_top_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_top_dir, "lib"))


classifiers = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.5
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Operating System :: OS Independent
Topic :: Software Development :: Libraries :: Python Modules
"""

packages = [d[0][len('lib/'):].replace('/', '.')
    for d in os.walk('lib/manta') if "__pycache__" not in d[0]]

script = (sys.platform == "win32" and "bin\\mantash" or "bin/mantash")
version = "1.5.1"
setup(
    name="manta",
    version=version,
    maintainer="Joyent",
    maintainer_email="support@joyent.com",
    author="Joyent",
    author_email="support@joyent.com",
    url="https://github.com/joyent/python-manta",
    license="MIT",
    platforms=["any"],
    packages=packages,
    package_dir={"": "lib"},
    package_data={
        '': ['*.txt'],
    },
    install_requires=[
        "pycrypto == 2.6.0",
        "paramiko >= 1.7.7.2",
        "httplib2==0.8",
    ],
    scripts=[script],
    
    description="A Python SDK for Manta",
    classifiers=filter(None, classifiers.split("\n")),
    long_description="""A Python SDK for Manta (Joyent's object stor and cloud compute system).

This provides a Python 'manta' package and a 'mantash' (Manta Shell) CLI
and shell.
""",
)
