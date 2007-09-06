#! /usr/bin/env python
# 
# Search for a track by title (and optionally by artist name).
#
# Usage:
#   python findtrack.py 'track name' ['artist name']
#
# $Id$
#
import sys
import logging
from musicbrainz2.webservice import Query, TrackFilter, WebServiceError

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
    

if len(sys.argv) < 1:
    print "Usage: findtrack.py 'puid'"
    sys.exit(1)

q = Query()
try:
    f = TrackFilter(puid=sys.argv[1])
    results = q.getTracks(f)
except WebServiceError, e:
    print 'Error:', e
    sys.exit(1)


for result in results:
    track = result.track
    print "Score     :", result.score
    print "Id        :", track.id
    print "Title     :", track.title
    print "Artist    :", track.artist.name
    print

# EOF




#!/usr/bin/env python
"""
Find a track's artist and title.
"""

def find_artist_and_title(puid):
    q = Query()
    try:
        f = TrackFilter(puid=sys.argv[1])
        results = q.getTracks(f)
    except WebServiceError, e:
        print 'Error:', e
        sys.exit(1)
    

def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    for fn in args:
        



if __name__ == '__main__':
    main()
