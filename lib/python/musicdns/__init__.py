# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

__all__ = ('create_fingerprint',)


_plugins = ["avcodec", "directshow", "quicktime", "gstreamer"]
_decoders = []

def initialize():
    for name in _plugins:
        try:
            decoder = getattr(__import__('musicdns.%s' % name), name)
            _decoders.append(decoder)
        except ImportError:
            pass
    if not _decoders:
        logging.warning(
            "No decoders found! Fingerprinting will be disabled.")

try:
    import ofa
    initialize()
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

