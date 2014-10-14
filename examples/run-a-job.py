#!/usr/bin/env python

"""A small example showing how to run a Manta job using the python-manta
client.
"""

import logging
import os
from pprint import pprint, pformat
import sys
import time

# Import the local manta module.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import manta


def get_client(verbose=False):
    MANTA_USER = os.environ['MANTA_USER']
    MANTA_URL = os.environ['MANTA_URL']
    MANTA_TLS_INSECURE = bool(os.environ.get('MANTA_TLS_INSECURE', False))
    MANTA_NO_AUTH = os.environ.get('MANTA_NO_AUTH', 'false') == 'true'
    if MANTA_NO_AUTH:
        signer = None
    else:
        MANTA_KEY_ID = os.environ['MANTA_KEY_ID']
        signer = manta.CLISigner(key_id=MANTA_KEY_ID)
    client = manta.MantaClient(url=MANTA_URL,
        account=MANTA_USER,
        signer=signer,
        verbose=verbose,
        disable_ssl_certificate_validation=MANTA_TLS_INSECURE)
    return client

def _indent(s, indent='    '):
    return indent + indent.join(s.splitlines(True))


#---- mainline

logging.basicConfig()

client = get_client(verbose=('-v' in sys.argv))

print "# First let's add a file to manta on which we'll operate."
mpath = '/%s/public/fruit.txt' % os.environ['MANTA_USER']
content = '''pear
crabapple
macintosh apple
banana
grape
braeburn apple
peach
'''
client.put_object(mpath, content=content, content_type='text/plain')
print 'Added "%s"\n' % mpath


print "# Now let's create a job that will grep that input for 'apple'."
# Create the job at get a job_id.
job_phases = [
    {
        'exec': 'grep apple',
        'type': 'map'
    }
]
job_id = client.create_job(job_phases, name='grep for apple')
print "Created job '%s'" % job_id

# Add inputs (manta paths to process) to the job.
client.add_job_inputs(job_id, [mpath])
client.end_job_input(job_id)
print "Added 1 input to job '%s'" % job_id

# Wait (polling) for the job to complete.
print "Waiting for job to complete"
n = 0
while True:
    time.sleep(5)
    job = client.get_job(job_id)
    if job["state"] == "done":
        sys.stdout.write('\n')
        break
    sys.stdout.write('.')
    n += 1
    if n % 60 == 0:
        sys.stdout.write('\n')
    sys.stdout.flush()

print "Job '%s' completed" % job_id

print
print "# Dump some job data."
print "Job:\n%s" % _indent(pformat(job))
print "Job inputs:\n%s" % _indent(pformat(client.get_job_input(job_id)))
print "Job outputs:\n%s" % _indent(pformat(client.get_job_output(job_id)))
print "Job errors:\n%s" % _indent(pformat(client.get_job_errors(job_id)))

