# Copyright (c) 2012 Joyent, Inc.  All rights reserved.

"""The Manta client."""

import sys
import logging
import os
from os.path import exists, join
import json
from pprint import pprint, pformat
from urllib import urlencode
import hashlib
import datetime
import base64

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



#---- compat

# Python version compat
# Use `bytes` for byte strings and `unicode` for unicode strings (str in Py3).
if sys.version_info[0] <= 2:
    py3 = False
    try:
        bytes
    except NameError:
        bytes = str
    base_string_type = basestring
elif sys.version_info[0] >= 3:
    py3 = True
    unicode = str
    base_string_type = str
    unichr = chr



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

    def _request(self, path, method="GET", query=None, body=None, headers=None):
        """Make a Manta request

        ...
        @returns (res, content)
        """
        assert path.startswith('/'), "bogus path: %r" % path

        if query:
            path += '?' + urlencode(query)
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

        return http.request(url, method, ubody, headers)

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
        if res["status"] != "204":
            raise errors.MantaAPIError(res, content)

    def list_directory(self, mdir, limit=None, marker=None):
        """ListDirectory
        http://apidocs.joyent.com/manta/manta/#ListDirectory

        @param mdir {str} A manta path, e.g. '/trent/stor/mydir'.
        @param limit {int} Limits the number of records to come back (default
            and max is 1000).
        @param marker {str} Key name at which to start the next listing.
        @returns Directory entries (dirents). E.g.:
            [{u'mtime': u'2012-12-11T01:54:07Z', u'name': u'play', u'type': u'directory'},
             ...]
        """
        log.debug('ListDirectory %r', mdir)

        query = {}
        if limit:
            query["limit"] = limit
        if marker:
            query["marker"] = marker

        res, content = self._request(mdir, "GET", query=query)
        if res["status"] != "200":
            raise errors.MantaAPIError(res, content)
        lines = content.split('\r\n')
        dirents = []
        for line in lines:
            if not line.strip():
                continue
            try:
                dirents.append(json.loads(line))
            except ValueError:
                raise errors.MantaError('invalid directory entry: %r' % line)
        return dirents

    def head_directory(self, mdir):
        """HEAD method on ListDirectory
        http://apidocs.joyent.com/manta/manta/#ListDirectory

        This is not strictly a documented Manta API call. However it is
        provided to allow access to the useful 'result-set-size' header.

        @param mdir {str} A manta path, e.g. '/trent/stor/mydir'.
        @returns The response object, which acts as a dict with the headers.
        """
        log.debug('HEAD ListDirectory %r', mdir)
        res, content = self._request(mdir, "HEAD")
        if res["status"] != "200":
            raise errors.MantaAPIError(res, content)
        return res

    def delete_directory(self, mdir):
        """DeleteDirectory
        http://apidocs.joyent.com/manta/manta/#DeleteDirectory

        @param mdir {str} A manta path, e.g. '/trent/stor/mydir'.
        """
        log.debug('DeleteDirectory %r', mdir)
        res, content = self._request(mdir, "DELETE")
        if res["status"] != "204":
            raise errors.MantaAPIError(res, content)

    def put_object(self, mpath, content=None, path=None, file=None,
                   content_length=None,
                   content_type="application/octet-stream",
                   durability_level=None):
        """PutObject
        http://apidocs.joyent.com/manta/manta/#PutObject

        Examples:
            client.put_object('/trent/stor/foo', 'foo\nbar\nbaz')
            client.put_object('/trent/stor/foo', path='path/to/foo.txt')
            client.put_object('/trent/stor/foo', file=open('path/to/foo.txt'),
                              size=11)

        One of `content`, `path` or `file` is required.

        @param mpath {str} Required. A manta path, e.g. '/trent/stor/myobj'.
        @param content {bytes}
        @param path {str}
        @param file {file-like object}
        @param content_type {string} Optional, but suggested. Default is
            'application/octet-stream'.
        @param durability_level {int} Optional. Default is 2. This tells
            Manta the number of copies to keep.
        """
        log.debug('PutObject %r', mpath)
        headers = {
            "Content-Type": content_type,
        }
        if durability_level:
            headers["x-durability-level"] = durability_level

        methods = [m for m in [content, path, file] if m is not None]
        if len(methods) != 1:
            raise errors.MantaError("exactly one of 'content', 'path' or "
                "'file' must be provided")
        if content:
            pass
        elif path:
            f = open(path)
            try:
                content = f.read()
            finally:
                f.close()
        else:
            content = f.read()
        if not isinstance(content, bytes):
            raise errors.MantaError("'content' must be bytes, not unicode")

        headers["Content-Length"] = str(len(content))
        md5 = hashlib.md5(content)
        headers["Content-MD5"] = base64.b64encode(md5.digest())
        res, content = self._request(mpath, "PUT", body=content,
                                     headers=headers)
        if res["status"] != "204":
            raise errors.MantaAPIError(res, content)

    def get_object(self, mpath, accept="*/*"):
        """GetObject
        http://apidocs.joyent.com/manta/manta/#GetObject

        @param mpath {str} Required. A manta path, e.g. '/trent/stor/myobj'.
        @param accept {str} Optional. Default is '*/*'. The Accept header
            for content negotiation.
        """
        log.debug('GetObject %r', mpath)
        headers = {
            "Accept": accept
        }

        res, content = self._request(mpath, "GET", headers=headers)
        if res["status"] != "200":
            raise errors.MantaAPIError(res, content)
        if len(content) != int(res["content-length"]):
            raise errors.MantaError("content-length mismatch: expected %d, "
                "got %s" % (res["content-length"], content))
        if res["content-md5"]:
            md5 = hashlib.md5(content)
            content_md5 = base64.b64encode(md5.digest())
            if content_md5 != res["content-md5"]:
                raise errors.MantaError("content-md5 mismatch: expected %d, "
                    "got %s" % (res["content-md5"], content_md5))
        return content

    def delete_object(self, mpath):
        """DeleteObject
        http://apidocs.joyent.com/manta/manta/#DeleteObject

        @param mpath {str} Required. A manta path, e.g. '/trent/stor/myobj'.
        """
        log.debug('GetObject %r', mpath)
        res, content = self._request(mpath, "DELETE")
        if res["status"] != "204":
            raise errors.MantaAPIError(res, content)
        return res

    #def put_link



