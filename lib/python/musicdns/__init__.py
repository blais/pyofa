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

import sys, os.path, logging, urllib, re

try:
    from xml.etree import ElementTree
    from xml.etree.ElementTree import iterparse
    from xml.etree.ElementPath import Path
except ImportError:
    from elementtree import ElementTree
    from elementtree.ElementTree import iterparse
    from elementtree.ElementPath import Path

from mutagen import File


__version__ = '1.0' # 2007-09-12

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
    Returns a pair of (fingerprint, duration-in-millis).
    If the file cannot be decoded, a IOError is raised."""

    # Make sure the filename is encoded properly to be consumed by the decoders.
    filename = encode_filename(filename)

    # Try to decode the audio file.
    result = None
    for decoder in _decoders:
        logging.debug("Decoding using %r...", decoder.__name__)
        try:
            result = decoder.decode(filename)
        except Exception, e:
            continue
    if not result:
        raise IOError("Could not decode file '%s' with any of the available decoders: %s." %
                      (filename, ','.join(x.__name__.split('.')[-1] for x in _decoders)))

    # Create the fingerprint.
    #
    # Note: the computed duration is typically incorrect. Use mutagen instead to
    # get the duration. If we could fix this in ffmpeg, we would not need the
    # dependency on mutagen.
    buffer, samples, sample_rate, stereo, _duration = result
    duration = File(filename).info.length * 1000

    fingerprint = ofa.create_print(buffer, samples, sample_rate, stereo)
    return fingerprint, int(duration)

def encode_filename(filename):
    """Encode unicode strings to filesystem encoding."""
    if isinstance(filename, unicode):
        if os.path.supports_unicode_filenames:
            return filename
        else:
            return filename.encode(_io_encoding, 'replace')
    else:
        return filename


musicdns_host = 'ofa.musicdns.org'
musicdns_port = 80

def lookup_fingerprint(fingerprint, duration, musicdns_key, **opt):
    """Given the fingerprint of an audio file, lookup the PUID from the MusicDNS
    service, synchronously."""

    req = '/ofa/1/track'
    url = 'http://%s:%d%s' % (musicdns_host, musicdns_port, req)
    postargs = dict(

        # Identification.
        cid=musicdns_key,
        cvr="pyofa/%s" % __version__,
        
        # The given fingerprint.
        fpt=fingerprint,

        # These are required by the license agreement, to help fill out the
        # MusicDNS database.
        art=opt.pop('art', ''),
        ttl='02-Track_02',
        alb=opt.pop('alb', ''),
        tnm=opt.pop('tnm', ''),  # track no.
        gnr=opt.pop('gnr', ''),
        yrr=opt.pop('yrr', ''),
        brt=opt.pop('brt', ''),
        fmt='', ##MPEG-1 Layer 3',
        dur=str(duration),

        # Return the metadata?
        rmd='0',

        # FIXME: What are those? Found from Picard, not in protocol docs.
        ## rmt='0',
        ## lkt='1',
        )

    data = urllib.urlencode(postargs)
    f = urllib.urlopen(url, data)

    # Parse the response.
    tree = ElementTree.parse(f)
    sanitize_tree(tree)
    el = tree.find('//puid')

    if el is not None:
        puid = el.attrib['id']
    else:
        puid = None

    return puid

    
def sanitize_tree(tree):
    """Remove all XML namespaces from the element tree. This is an inconvenience
    due to the effbot's obsessiveness in maintaining the XML namespaces
    throughout the tags. We prefer BeautifulSoup, which does away with this
    nonsense, but since etree comes with Python, we'll settle for this kludge
    instead in the name of avoiding dependencies.
    """
    for el in tree.getiterator():
        el.tag = re.sub('{.*}', '', el.tag)


