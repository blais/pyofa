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

import sys, os.path, logging, urllib
from mutagen import File

__version__ = '1.0a1'

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
        except Exception:
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
    return fingerprint, duration

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
        art='unknown',
        ttl='02-Track_02',
        alb='unknown',
        tnm='unknown',  # track no.
        gnr='unknown',
        yrr='unknown',
        brt='unknown',
        fmt='', ##MPEG-1 Layer 3',
        dur=str(duration),

        # Return the metadata.
        rmd='1',
        # What are those?
##         rmt='0',
##         lkt='1',
        )

##         dur=str(file.metadata.length or duration),
##         brt=str(file.metadata.get("~#bitrate", 0)),
##         fmt=file.metadata["~format"],
##         art=file.metadata["artist"],
##         ttl=file.metadata["title"],
##         alb=file.metadata["album"],
##         tnm=file.metadata["tracknumber"],
##         gnr=file.metadata["genre"],
##         yrr=file.metadata["date"][:4])

    data = urllib.urlencode(postargs)

##     data = 'gnr=&art=&rmt=0&cid=0736ac2cd889ef77f26f6b5e3fb8a09c&alb=&fmt=MPEG-1%20Layer%203&brt=220.805&cvr=MusicBrainz%20Picard-0.9.0alpha14&fpt=ATVDP5EhqRYXLAQgthFRD%2BobRRTiFc8W0AjUF1YSSQgaEHkNdwOcClQSbwrGBi8DzgL%2BAcIBqgIOAawBYQFKAWoBlAFnAUwBXAFTAYEBggEny9%2FDTuBu%2F3Yu0yRH%2FqsNERI3GtsjrCB%2FBUsCGhnTDJkXOw28Ao8FLgzcCgsCLAIOAgoA9ACyAV4BCADtAO0BNAGmAWsBNgFJASEBegFGAQEA4PRb%2FqwNCUgW3E%2F56gz9IugalOGEwzkBNAAfDHUAktEV84P%2FM%2F3H8bz0%2BgB7%2F7H%2B%2Ff98%2F37%2Flf%2BhAB%2F%2F4v9v%2F1r%2FoAA5ACH%2F%2BP%2Bc%2FxL%2FLPt0HOMKxPUtHbssKdfP6GfeUBooGlP6F%2BWhvefycADB%2FMvvKfsn6Y%2Fa8fBn%2FBP9HP33%2FuH9s%2Fz8%2Fqj%2FI%2F7o%2Fur%2FOP8l%2F3v%2Fa%2F94%2Fxj%2B%2Bf9JKrHgiOtYDIEOmBWn%2FDD%2BbjiT3YP3uBYkBVTv4bhV6vEFYhAf%2FuXpte7u7HcBiwDdAE8AQ%2F7a%2Fpr%2F2v%2FG%2F2b%2FAv9q%2F5L%2F2AAiACv%2Fb%2F84%2F6ej%2FC%2BTIuIUmRDs%2BVcI0%2FgLF9Hstu7xCbcC1Acm1v%2FwigrACcT%2F2v4oAa39bv0cACgAmgA6ACL%2FcgAqABEAMAAFABkAYgA8AJYAjgCYAJ0AJQSLCKoF0Qr7%2B2TFZ8u%2FImUee%2FM%2F%2BEMVKvJO05skrgYNNykDk%2F3l6lv%2FGgmV%2F2cAAgAOACb%2FX%2F99%2F77%2Fov%2FDAB%2F%2F%2FP%2Bx%2F8z%2F3%2F%2Bc%2F4QADgA5QDQ8OQ%3D%3D&ttl=02-Track_02&tnm=2&lkt=1&dur=275000&yrr='

    f = urllib.urlopen(url, data)
    print f.read()



"""
picard:

gnr=
art=
rmt=0
cid=0736ac2cd889ef77f26f6b5e3fb8a09c
alb=
fmt=MPEG-1%20Layer%203
brt=220.805
cvr=MusicBrainz%20Picard-0.9.0alpha14
fpt=ATVDP5EhqRYXLAQgthFRD%2BobRRTiFc8W0AjUF1YSSQgaEHkNdwOcClQSbwrGBi8DzgL%2BAcIBqgIOAawBYQFKAWoBlAFnAUwBXAFTAYEBggEny9%2FDTuBu%2F3Yu0yRH%2FqsNERI3GtsjrCB%2FBUsCGhnTDJkXOw28Ao8FLgzcCgsCLAIOAgoA9ACyAV4BCADtAO0BNAGmAWsBNgFJASEBegFGAQEA4PRb%2FqwNCUgW3E%2F56gz9IugalOGEwzkBNAAfDHUAktEV84P%2FM%2F3H8bz0%2BgB7%2F7H%2B%2Ff98%2F37%2Flf%2BhAB%2F%2F4v9v%2F1r%2FoAA5ACH%2F%2BP%2Bc%2FxL%2FLPt0HOMKxPUtHbssKdfP6GfeUBooGlP6F%2BWhvefycADB%2FMvvKfsn6Y%2Fa8fBn%2FBP9HP33%2FuH9s%2Fz8%2Fqj%2FI%2F7o%2Fur%2FOP8l%2F3v%2Fa%2F94%2Fxj%2B%2Bf9JKrHgiOtYDIEOmBWn%2FDD%2BbjiT3YP3uBYkBVTv4bhV6vEFYhAf%2FuXpte7u7HcBiwDdAE8AQ%2F7a%2Fpr%2F2v%2FG%2F2b%2FAv9q%2F5L%2F2AAiACv%2Fb%2F84%2F6ej%2FC%2BTIuIUmRDs%2BVcI0%2FgLF9Hstu7xCbcC1Acm1v%2FwigrACcT%2F2v4oAa39bv0cACgAmgA6ACL%2FcgAqABEAMAAFABkAYgA8AJYAjgCYAJ0AJQSLCKoF0Qr7%2B2TFZ8u%2FImUee%2FM%2F%2BEMVKvJO05skrgYNNykDk%2F3l6lv%2FGgmV%2F2cAAgAOACb%2FX%2F99%2F77%2Fov%2FDAB%2F%2F%2FP%2Bx%2F8z%2F3%2F%2Bc%2F4QADgA5QDQ8OQ%3D%3D
ttl=02-Track_02
tnm=2
lkt=1
dur=275000
yrr=

pyofa:


http://ofa.musicdns.org:80/ofa/1/track?gnr=unknown
art=unknown
cid=92519b52ab185804de486fff9be67048
alb=unknown
fmt=mp3
brt=unknown
cvr=pyofa%2F1.0a1
fpt=ATVDP5EhqRYXLAQgthFRD%2BobRRTiFc8W0AjUF1YSSQgaEHkNdwOcClQSbwrGBi8DzgL%2BAcIBqgIOAawBYQFKAWoBlAFnAUwBXAFTAYEBggEny9%2FDTuBu%2F3Yu0yRH%2FqsNERI3GtsjrCB%2FBUsCGhnTDJkXOw28Ao8FLgzcCgsCLAIOAgoA9ACyAV4BCADtAO0BNAGmAWsBNgFJASEBegFGAQEA4PRb%2FqwNCUgW3E%2F56gz9IugalOGEwzkBNAAfDHUAktEV84P%2FM%2F3H8bz0%2BgB7%2F7H%2B%2Ff98%2F37%2Flf%2BhAB%2F%2F4v9v%2F1r%2FoAA5ACH%2F%2BP%2Bc%2FxL%2FLPt0HOMKxPUtHbssKdfP6GfeUBooGlP6F%2BWhvefycADB%2FMvvKfsn6Y%2Fa8fBn%2FBP9HP33%2FuH9s%2Fz8%2Fqj%2FI%2F7o%2Fur%2FOP8l%2F3v%2Fa%2F94%2Fxj%2B%2Bf9JKrHgiOtYDIEOmBWn%2FDD%2BbjiT3YP3uBYkBVTv4bhV6vEFYhAf%2FuXpte7u7HcBiwDdAE8AQ%2F7a%2Fpr%2F2v%2FG%2F2b%2FAv9q%2F5L%2F2AAiACv%2Fb%2F84%2F6ej%2FC%2BTIuIUmRDs%2BVcI0%2FgLF9Hstu7xCbcC1Acm1v%2FwigrACcT%2F2v4oAa39bv0cACgAmgA6ACL%2FcgAqABEAMAAFABkAYgA8AJYAjgCYAJ0AJQSLCKoF0Qr7%2B2TFZ8u%2FImUee%2FM%2F%2BEMVKvJO05skrgYNNykDk%2F3l6lv%2FGgmV%2F2cAAgAOACb%2FX%2F99%2F77%2Fov%2FDAB%2F%2F%2FP%2Bx%2F8z%2F3%2F%2Bc%2F4QADgA5QDQ8OQ%3D%3D
rmd=1
ttl=unknown
tnm=0
dur=0
yrr=unknown


"""
