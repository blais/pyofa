#!/usr/bin/env python

import os.path, sys
from ConfigParser import RawConfigParser

if sys.version_info < (2, 5):
    print "*** You need Python 2.5 or higher to use this wrapper."


from distutils.command.build import build
from distutils.command.config import config
from distutils.command.install import install as install
from distutils.core import setup, Extension

defaults = {

    'build': {
        'with-directshow': 'False',
        'with-avcodec': 'True',
        'with-libofa': 'True',
    },

    # Note: you may have to customize some of the flags below for your
    # specific installation and support requirements.
    'avcodec': {
        'cflags': '-I/usr/include/ffmpeg',
        'libs': ('-pthread -lavformat -lavcodec -lz -la52 '
                 '-lfaac -lfaad -lgsm -lmp3lame -lx264 -lxvidcore '
                 '-ldc1394 -ldl -lX11 -lXext -lraw1394 -ltheora '
                 '-lvorbisenc -lavutil -lvorbis -lm -logg')
        },

    'libofa': {
        'cflags': '',
        'libs': '-lofa'
        },

    'directshow': {
        'cflags': '',
        'libs': ''
        },

}

cfg = RawConfigParser()
for section, values in defaults.items():
    cfg.add_section(section)
    for option, value in values.items():
        cfg.set(section, option, value)
cfg.read(['build.cfg'])


ext_modules = []

if cfg.getboolean('build', 'with-libofa'):
    ext_modules.append(
        Extension('musicdns.ofa', sources=['lib/python/musicdns/ofa.c'],
                  extra_compile_args=cfg.get('libofa', 'cflags').split(),
                  extra_link_args=cfg.get('libofa', 'libs').split()))

if cfg.getboolean('build', 'with-directshow'):
    ext_modules.append(
        Extension('musicdns.directshow',
                  sources=['lib/python/musicdns/directshow.cpp'],
                  extra_compile_args=cfg.get('directshow', 'cflags').split(),
                  extra_link_args=cfg.get('directshow', 'libs').split()))

if cfg.getboolean('build', 'with-avcodec'):
    ext_modules.append(
        Extension('musicdns.avcodec',
                  sources=['lib/python/musicdns/avcodec.c'],
                  extra_compile_args=cfg.get('avcodec', 'cflags').split(),
                  extra_link_args=cfg.get('avcodec', 'libs').split()))


class pyofa_config(config):

    def run(self):
        print 'checking for pkg-cfg...',
        have_pkgconfig = False
        if os.system('pkg-config --version >%s 2>%s' % (os.path.devnull, os.path.devnull)) == 0:
            print 'yes'
            have_pkgconfig = True
        else:
            print 'no'

        print 'checking for libofa...',
        if have_pkgconfig:
            self.pkgconfig_check_module('libofa', 'libofa')
        else:
            self.check_lib('libofa', 'ofa_create_print', ['ofa1/ofa.h'], [['ofa'], ['libofa']])

        print 'checking for libavcodec/libavformat...',
        if have_pkgconfig:
            self.pkgconfig_check_module('avcodec', 'libavcodec libavformat')
        else:
            self.check_lib('avcodec', 'av_open_input_file', ['avcodec.h', 'avformat.h'], [['avcodec', 'avformat'], ['avcodec-51', 'avformat-51']])

        print 'checking for directshow...',
        if sys.platform == 'win32':
            print 'yes'
            cfg.set('build', 'with-directshow', True)
            cfg.set('directshow', 'cflags', '')
            cfg.set('directshow', 'libs', 'strmiids.lib')
        else:
            print 'no'
            cfg.set('build', 'with-directshow', False)

        print 'saving build.cfg'
        cfg.write(file('build.cfg', 'wt'))


    def pkgconfig_exists(self, module):
        if os.system('pkg-config --exists %s' % module) == 0:
            return True

    def pkgconfig_cflags(self, module):
        pkgcfg = os.popen('pkg-config --cflags %s' % module)
        ret = pkgcfg.readline().strip()
        pkgcfg.close()
        return ret

    def pkgconfig_libs(self, module):
        pkgcfg = os.popen('pkg-config --libs %s' % module)
        ret = pkgcfg.readline().strip()
        pkgcfg.close()
        return ret

    def pkgconfig_check_module(self, name, module):
        print '(pkg-config)',
        if self.pkgconfig_exists(module):
            print 'yes'
            cfg.set('build', 'with-' + name, True)
            cfg.set(name, 'cflags', self.pkgconfig_cflags(module))
            cfg.set(name, 'libs', self.pkgconfig_libs(module))
        else:
            print 'no'
            cfg.set('build', 'with-' + name, False)

    def check_lib(self, name, function, includes, libraries):
        for libs in libraries:
            res = self.try_link(
                "%s\nint main() { void *tmp = (void *)%s; return 0; }" % (
                    "\n".join('#include <%s>' % i for i in includes),
                    function),
                libraries=libs, lang='c')
            if res:
                print 'yes'
                cfg.set('build', 'with-' + name, True)
                cfg.set(name, 'cflags', '')
                # FIXME: gcc format?
                cfg.set(name, 'libs', ' '.join(l + '.lib' for l in libs))
                return
        print 'no'
        cfg.set('build', 'with-' + name, False)



def read_version():
    sys.path.insert(0, 'lib/python')
    from musicdns import __version__
    return __version__


args = {
    'name': 'pyofa',
    'version': read_version(),
    'description': 'A Python wrapper for MusicDNS.',
    'url': 'http://furius.ca/pyofa',
    'author': "Martin Blais",
    'author_email': "blais@furius.ca",
    'package_dir': {'': 'lib/python'},
    'packages': ('musicdns',),
    'ext_modules': ext_modules,
    'cmdclass': {
        'config': pyofa_config,
    'scripts': ['bin/musicdns-getpuid', 'bin/musicdns-guess-album'],
    },
}

setup(**args)

