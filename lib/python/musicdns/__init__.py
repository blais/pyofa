# -*- coding: utf-8 -*-
#
# pyofa, a wrapper around the MusicDNS libofa and service.
# Copyright (C) 2007 Martin Blais (modifications)
# Copyright (C) 2006 Lukáš Lalinský (original code)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import sys, os.path, logging

__all__ = ('initialize', 'finalize',
           'create_fingerprint', 'lookup_fingerprint')


_plugins = ["avcodec", "directshow", "quicktime", "gstreamer"]
_decoders = []

def import_decoders():
    for name in _plugins:
        try:
            decoder = getattr(__import__('musicdns.%s' % name), name)
            _decoders.append(decoder)

            # Note: the reason we're not calling 'init' here is that it may be
            # lengthy, and we want to give the change to multithreaded programs
            # to delegate this to a background thread in order to speed up
            # startup.
        except ImportError:
            pass
    if not _decoders:
        logging.warning(
            "No decoders found! Fingerprinting will be disabled.")

def initialize():
    "You must call this before your use the decoders."
    for decoder in _decoders:
        decoder.init()

def finalize():
    "You must call this after you're done using the decoders."
    for decoder in _decoders:
        decoder.done()

try:
    import ofa
    import_decoders()
except ImportError:
    logging.warning("Libofa not found! Fingerprinting will be disabled.")
    ofa = None


def create_fingerprint(filename):
    """Compute a fingerprint from an open audio file.
    This function may return none.
    If the file cannot be decoded, a IOError is raised."""

    # Make sure the filename is encoded properly to be consumed by the decoders.
    filename = encode_filename(filename)

    # Try to decode the audio file.
    result = None
    for decoder in _decoders:
        logging.debug("Decoding using %r...", decoder.__name__)
        try:
            trace(decoder, filename)
            result = decoder.decode(filename)
        except Exception:
            continue
    if not result:
        raise IOError("Could not decode file '%s' with any of the available decoders: %s." %
                      (filename, ','.join(x.__name__.split('.')[-1] for x in _decoders)))

    # Create the fingerprint.
    buffer, samples, sample_rate, stereo, duration = result
    fingerprint = ofa.create_print(buffer, samples, sample_rate, stereo)
    return fingerprint

def encode_filename(filename):
    """Encode unicode strings to filesystem encoding."""
    if isinstance(filename, unicode):
        if os.path.supports_unicode_filenames:
            return filename
        else:
            return filename.encode(_io_encoding, 'replace')
    else:
        return filename

def lookup_fingerprint(fingerprint, musicdns_key):
    """Given the fingerprint of an audio file, lookup the PUID from the MusicDNS
    service, synchronously."""
    
## FIXME: todo
##     if file.state != file.PENDING:
##         handler(file, None)
##         return
##     self.tagger.window.set_statusbar_message(N_("Looking up the fingerprint for file %s..."), file.filename)
##     self.tagger.xmlws.query_musicdns(partial(self._lookup_finished, handler, file),
##         rmt='0',
##         lkt='1',
##         cid=MUSICDNS_KEY,
##         cvr="MusicBrainz Picard-%s" % version_string,
##         fpt=fingerprint,
##         dur=str(file.metadata.length or length),
##         brt=str(file.metadata.get("~#bitrate", 0)),
##         fmt=file.metadata["~format"],
##         art=file.metadata["artist"],
##         ttl=file.metadata["title"],
##         alb=file.metadata["album"],
##         tnm=file.metadata["tracknumber"],
##         gnr=file.metadata["genre"],
##         yrr=file.metadata["date"][:4])



