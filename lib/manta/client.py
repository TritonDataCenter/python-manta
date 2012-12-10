# Copyright (c) 2012 Joyent, Inc.  All rights reserved.

"""The Manta client."""

import sys
import logging
import os
from os.path import exists, join
import json
from pprint import pprint, pformat
from urllib import urlencode, urlretrieve
import datetime

import httplib2
import appdirs

from manta.version import __version__
import manta.errors as errors



#---- globals

log = logging.getLogger("manta.client")
DEFAULT_HTTP_CACHE_DIR = appdirs.user_cache_dir(
    "python-manta", "Joyent", "http")
DEFAULT_USER_AGENT = "python-manta/%s (%s) Python/%s" % (
    __version__, sys.platform, sys.version.split(None, 1)[0])





#---- internal support stuff

def http_date(d=None):
    """Return HTTP Date format string for the given date.
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.3.1

    @param d {datetime.datetime} Optional. Defaults to `utcnow()`.
    """
    if not d:
        d = datetime.datetime.utcnow()
    return d.strftime("%a, %d %b %Y %H:%M:%S GMT")


def _indent(s, indent='    '):
    return indent + indent.join(s.splitlines(True))

class MantaHttp(httplib2.Http):
    def _request(self, conn, host, absolute_uri, request_uri, method, body, headers, redirections, cachekey):
        if log.isEnabledFor(logging.DEBUG):
            body_str = body or ''
            if body and len(body) > 1024:
                body_str = body[:1021] + '...'
            log.debug("req: %s %s\n%s", method, request_uri,
                '\n'.join([
                    _indent("host: " + host),
                    _indent("headers: " + pformat(headers)),
                    _indent("cachekey: " + pformat(cachekey)), #XXX
                    _indent("body: " + body_str)
                ]))
        res, content = httplib2.Http._request(self, conn, host, absolute_uri, request_uri, method, body, headers, redirections, cachekey)
        if log.isEnabledFor(logging.DEBUG):
            log.debug("res: %s %s\n%s\n%s", method, request_uri,
                _indent(pformat(res)),
                (len(content) < 1024 and _indent(content)
                 or _indent(content[:1021]+'...')))
        return (res, content)




#---- exports

class MantaClient(object):
    """
    A client for accessing the Manta REST API.
    http://apidocs.joyent.com/manta/manta/
    http://apidocs.joyent.com/manta/pythonsdk/

    @param url {str} The Manta URL
    @param user {str} The Manta username.
    @param signer {Signer instance} A python-manta Signer class instance
        that handles signing request to Manta using the http-signature
        auth scheme.
    @param user_agent {str} Optional. User-Agent header string.
    @param cache_dir {str} Optional. A dir to use for HTTP caching. It will
        be created as needed.
    @param disable_ssl_certificate_validation {bool} Default false.
    """
    def __init__(self, url, user, sign=None, signer=None,
            user_agent=None, cache_dir=None,
            disable_ssl_certificate_validation=False):
        assert user, 'user'
        # Prefer 'signer', but accept 'sign' a la node-manta.
        assert signer or sign, 'signer'
        self.url = url
        assert not url.endswith('/'), "don't want trailing '/' on url: %r" % url
        self.user = user
        self.signer = signer or sign
        self.cache_dir = cache_dir or DEFAULT_HTTP_CACHE_DIR
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self.disable_ssl_certificate_validation = disable_ssl_certificate_validation

    _http_cache = None
    def _get_http(self):
        if not self._http_cache:
            if not exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            self._http_cache = MantaHttp(self.cache_dir,
                disable_ssl_certificate_validation=self.disable_ssl_certificate_validation)
        return self._http_cache

    def _sign_request(self, headers):
        pass

    def _request(self, path, method="GET", body=None, headers=None):
        assert path.startswith('/'), "bogus path: %r" % path
        url = self.url + path
        http = self._get_http()

        ubody = body
        if body is not None and isinstance(body, dict):
            ubody = urlencode(body)
        if headers is None:
            headers = {}
        headers["User-Agent"] = self.user_agent

        # Signature auth.
        if "Date" not in headers:
            headers["Date"] = http_date()
        algorithm, fingerprint, signature = self.signer.sign(headers["Date"])
        headers["Authorization"] = \
            'Signature keyId="/%s/keys/%s",algorithm="%s" %s' % (
                self.user, fingerprint, algorithm, signature)

        res, content = http.request(url, method, ubody, headers)
        return res, content
        #res, content = _manta_req(url, method, body, headers)
        #if res["status"] == "204":
        #    return res, content
        #else:
        #    if res["content-type"] != "application/json":
        #        raise MantaShellError("API error: response is not json: '%s'"
        #            % res["content-type"])
        #    return res, json.loads(content)

    def put_directory(self, mdir):
        """PutDirectory
        http://apidocs.joyent.com/manta/manta/#PutDirectory

        @param mdir {str} A manta path, e.g. '/trent/stor/mydir'.
        """
        log.debug('PutDirectory %r', mdir)
        headers = {
            "Content-Type": "application/json; type=directory"
        }
        res, content = self._request(mdir, "PUT", headers=headers)
        #XXX

    # Aliases.
    # XXX want these? Perhaps in a separate optional class?
    #mkdir = put_directory

    def _manta_mkdir(url, log_write=None, dry_run=False, insecure=False):
        if log_write:
            log_write("mkdir %s", url)
        if not dry_run:
            res, data = _manta_json_req(url, "PUT",
                headers={"Content-Type": g_dir_content_type},
                insecure=insecure)
            if res["status"] != "204":
                raise MantaShellError("mkdir API error: %s %s: %s" % (
                    res["status"], data["code"], data["message"]))
