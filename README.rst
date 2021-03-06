.. -*- coding: utf-8 -*-

==================================================
   pyofa: Python Wrapper for MusicDNS  (libofa)
==================================================

.. contents::
..
    1  Description
    2  Dependencies
      2.1  MusicDNS Key
    3  Documentation
    4  Download
    5  Build and Installation
      5.1  Installing on Ubuntu
    6  Copyright and License
    7  Author

Description
===========

pyofa is a simple Python wrapper around the MusicDNS technology
provided by MusicIP for generating PUIDs (audio fingerprints) from
audio files (e.g. MP3, M4A, etc.).


Dependencies
============

- `Python 2.5 <http://python.org>`_ or higher
- MusicIP's `libofa <http://www.musicip.com/dns>`_
- python-mutagen
- libavcodec (FFMPEG)

On Ubuntu, this means installing the following packages (9.04, updated
on [2009-05-13])::

  pkg-config
  python-mutagen
  libavcodec-dev
  libavformat-dev
  liba52-dev
  libmp3lame-dev
  libx264-dev
  libxvidcore-dev


MusicDNS Key
------------

You will need your own MusicDNS key to use this package. You simply
provide it to the `getpuid()` function. You register for a key here:

  http://www.musicip.com/dns/key.jsp


Documentation
=============

- See `example script <bin/musicdns-getpuid>`_
- `CHANGES <CHANGES>`_
- `TODO <TODO>`_


Download
========

A Mercurial repository can be found at:

  http://github.com/blais/pyofa



Build and Installation
======================

To build the dynlibs::

  python setup.py config

In order for this to work, it should say "yes" for both ofa and
avcodec. Then, to build and install::

  python setup.py build_ext --inplace
  python setup.py install

or to build an RPM (with AVCodec/FFMPEG and OFA enabled)::

  python setup.py bdist_rpm


Installing on Ubuntu
--------------------
Ubuntu, here are the list of packages you need to install::

  # apt-get install python-mutagen libavcodec-dev libavformat-dev libofa0-dev


Copyright and License
=====================

This code is distributed under the `GNU General Public License <COPYING>`_;


Author
======

Martin Blais <blais@furius.ca>
(using the code of Lukáš Lalinský)

.. note::

   Lukáš is the author of the great majority of the code, I just
   repackaged and simplified it outside of Picard because I wanted to
   write scripts using MusicDNS without a GUI application.
