# Copyright 2012 Joyent, Inc.  All rights reserved.

"""A Python client/CLI/shell/SDK for Joyent Manta."""

__version__ = "1.0.0"

from .client import MantaClient
from .auth import PrivateKeySigner
