# Copyright 2012 Joyent, Inc.  All rights reserved.

"""python-manta errors"""

__all__ = ["MantaError", "MantaAPIError"]

import logging


#---- globals

log = logging.getLogger('manta.errors')



#---- exports

class MantaError(Exception):
    pass

class MantaAPIError(MantaError):
    #TODO: special error code handling
    pass
