#!/usr/bin/env python

"""python-manta Python package setup script"""

import os
import sys
import distutils
from distutils.core import setup

assert sys.version_info > (2, 3), \
    "python-manta does not support this Python version: %s" % sys.version

_top_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_top_dir, "lib"))
try:
    import manta
finally:
    del sys.path[0]

classifiers = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.4
Programming Language :: Python :: 2.5
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Operating System :: OS Independent
Topic :: Software Development :: Libraries :: Python Modules
"""

packages = [d[0][len('lib/'):].replace('/', '.')
    for d in os.walk('lib/manta') if "__pycache__" not in d[0]]

script = (sys.platform == "win32" and "bin\\mantash" or "bin/mantash")
#XXX version = manta.__version__ + '-' + 'gcafebab'
version = manta.__version__
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
    packages=packages + ["httplib2", "paramiko"],
    package_dir={"": "lib"},
    package_data={
        '': ['*.so', '*.txt'],
    },
    scripts=[script],
    description="A Python SDK for Manta (Joyent's Object Store and Cloud Compute system)",
    classifiers=filter(None, classifiers.split("\n")),
    long_description="""A Python SDK for Manta (Joyent's Object Store and Cloud Compute system).

This provides a Python 'manta' package and a 'mantash' (Manta Shell) CLI
and shell.
""",
)
