#!/usr/bin/env python

from distutils.core import setup

setup(name="mumym",
      version="0.9.1",
      description="Lojbanic word game for IRC",
      author="Theodore Reed",
      author_email="treed@surreality.us",
      url="http://savannah.nongnu.org/projects/ircbots/",
      scripts=['mumym.py'],
      data_files=[('/etc/ircbots/',['mumym.conf']),
      			('/etc/init.d/',['misc/mumym'])]
     )
