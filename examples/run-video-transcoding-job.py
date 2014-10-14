#!/usr/bin/env python

"""A Python Manta SDK version of
<https://apidocs.joyent.com/manta/example-video-transcode.html> from the Node.js
Manta SDK docs.  Usage:

    python run-video-transcoding-job.py
    python run-video-transcoding-job.py -v   # verbose output
"""

import logging
import os
from pprint import pprint, pformat
import sys
import time
from fnmatch import fnmatch
from posixpath import join as mjoin

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

print "* * *"
print "* Warning: This example runs a (long) video transcoding Manta job"
print "* which can cost a little bit. See"
print "*    https://apidocs.joyent.com/manta/example-video-transcode.html"
print "* for details"
print "* * *"

raw_input("Hit <Enter> to continue, ^C to abort.")
print

client = get_client(verbose=('-v' in sys.argv))

inputs = []
for dirpath, dirents, objents in client.walk('/manta/public/examples/kart'):
    for obj in objents:
        if fnmatch(obj["name"], "*.mov"):
            inputs.append(mjoin(dirpath, obj["name"]))
print "Inputs: %r" % inputs

job_phases = [
    {
        'type': 'map',
        'exec': 'ffmpeg -nostdin -i $MANTA_INPUT_FILE -an out.webm '
            '&& mpipe -p -H "content-type: video/webm" '
            '-f out.webm '
            '"/%s/public/manta-examples/kart/$(basename $MANTA_INPUT_OBJECT .mov).webm"'
                % os.environ['MANTA_USER']
    }
]
job_id = client.create_job(job_phases, name='video transcoding example')
print "Created job '%s'" % job_id
client.add_job_inputs(job_id, inputs)
client.end_job_input(job_id)
print "Added %d input%s to job '%s'" % (
    len(inputs), len(inputs) != 1 and 's' or '', job_id)

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

