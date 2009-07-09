#!/usr/bin/env python

from distutils.core import setup

setup(name="mumym",
      version="0.9.2-devel",
      description="Lojbanic word game for IRC",
      author="Theodore Reed",
      author_email="treed@surreality.us",
      url="http://surreality.us/wiki/show/Mumym",
      scripts=['mumym.py'],
      data_files=[('/etc/ircbots/',['mumym.conf']),
      			('/etc/init.d/',['misc/mumym'])]
     )
