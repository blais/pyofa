"""
Functions to cache the fingerprints and puids.
"""

import os, shelve
from os.path import *

import musicdns


class MusicDNSCache(object):

    def __init__(self, cachefn=None):
        if cachefn is None:
            cachefn = join(os.environ['HOME'], '.musicdns_cache')
        self.cachefn = cachefn
        self.dbm = shelve.open(self.cachefn, 'c')
    
    def getpuid(self, fn, musicdns_key):
        fn = abspath(fn)

        # Lookup puid from the fingerprint.
        try:
            duration, fingerprint, puid = self.dbm[fn]
        except KeyError:
            fingerprint = None
            puid = None

        if fingerprint is None or duration is None:

            # Get the fingerprint and duration.
            try:
                fingerprint, duration = self.dbm[fn]
            except KeyError:
                fingerprint, duration = musicdns.create_fingerprint(fn)
                self.dbm[fn] = duration, fingerprint, puid
                self.dbm.sync()

        if puid is None:
            assert duration is not None
            puid = musicdns.lookup_fingerprint(fingerprint, duration, musicdns_key)
            self.dbm[fn] = duration, fingerprint, puid
            self.dbm.sync()

        return puid, duration

