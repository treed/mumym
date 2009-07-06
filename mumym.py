#!/usr/bin/python
# mumym - Lojbanic word game
# Copyright (c) 2002-04 by Theodore Reed (rizen)
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

try:
	from psyco.classes import *
except ImportError:
	pass

#
# Changelog:
#
# 0.9.1:
#
#     + Added log system. (treed)
#     + Added AI framework and a simple AI named .alis. (treed)
#     + Corrected grammar in, added to and made the startup messages wrap
#           to 80 chars. (treed)
#     + Converted API to twisted, instead of irclib. Hoping this will
#           make this a bit more robust. (treed)
#     + Translated daemon as depsamru'e and condensed a few lines for the
#           daemonizer. (treed)
#     + Added the ability to run as a daemon. (treed)
#     + Added basic getopt support. (treed)
#     + Translate startup message to lojban. (treed)
#     + Finished that "na drani" line. (treed)
#     + Moved configuration stuff to external file. (treed)
#     + Replaced usage of xreadlines. (treed)
#     + Replaced true/false with built in True/False constants. (treed) 
#     + Added 'sidju' command to make bot repeat startup text. (rlpowell)
#     + Added 'sisti' command to stop bot. (rlpowell)
#     + Added COPYING and copyright statements. (treed)
#     + Added the ability to use psyco. (treed)
#

import string, random, time, re, ConfigParser, getopt, sys, os, logging
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

version = "0.9.1"

declaration = """.i la mumym. pe li """ + version + """ se ponse la sIodor.rid. ti'u li 2002 bi'o 
2004 .i my cu bapzifre samselpla .i lenu galfi my. kei se curmi fi la gypyly. 
pe la gnus. .i ko viska la'o gy. COPYING .gy tezu'e lenu zmadu cilre
--"""

usagestring = """.i lu cy. mumym.py [tadjygalfi] .cy cu plitadji
.i di'e tadjygalfi

.i lu ty. -s .ty .a lu ty. --smaji .ty cu gasnu lenu la mumym cu smaji kei
.i lu ty. -d .ty .a lu ty. --depsamruhe .ty cu gasnu lenu la mumym cu 
	depsamru'e kei
.i lu ty. -p/fu/bar/baz .ty .a lu ty. --pidfile=/fu/bar/baz .ty cu gasnu lenu
	la mumym punji le pruce namcu la'o gy. /fu/bar/baz .gy""" 


try:
	opts, args = getopt.getopt(sys.argv[1:], 'shdp:', ['smaji', 'help','depsamruhe','pidfile='])
except getopt.GetoptError:
	print declaration
	print usagestring
	sys.exit(2)

quiet = False
daemon = False
pidfile = None

for o, a in opts:
	if o in ('-s', '--smaji'):
		quiet = True
	if o in ('-h', '--help'):
		print declaration
		print usagestring
		sys.exit()
	if o in ('-d', "--depsamruhe"):
		daemon = True
	if o in ('-p', "--pidfile"):
		pidfile = a

if not quiet and not daemon:
	print declaration

consonants = "bcdfgjklmnprstvxz"
vowels  = "aeiouy"
numbers = {0 : "no", 1 : "pa", 2 : "re", 3 : "ci", 4 : "vo", 5 : "mu"}

parser = ConfigParser.ConfigParser()
parser.read(['./mumym.conf','/etc/ircbots/mumym.conf'])

chan = parser.get('main', 'channel')
nick = parser.get('main', 'nickname')
gihuste_loc = parser.get('main', 'gihuste')
logfile = parser.get('main','logfile')

servers = []

for section in parser.sections():
	if "server" in section:
		servers.append([parser.get(section, 'server'), parser.getint(section, 'port')])

class MultiLogger:
	"A utility class for having the same data go to multiple loggers with differing levels."

	def __init__(self):
		self.loggers = []
	
	def addLogger(self, logger, level):
		self.loggers.append((logger, level))
	
	def log(self, lvl, message):
		for logger, level in self.loggers:
			if level <= lvl:
				logger.log(lvl, message)

logger = MultiLogger()

debugging = False
def debug(msg):
	if debugging == True:
		logger.log(logging.DEBUG, msg)
info     = lambda msg: logger.log(logging.INFO,  msg)
warning  = lambda msg: logger.log(logging.WARNING, msg)
error    = lambda msg: logger.log(logging.ERROR, msg)
critical = lambda msg: logger.log(logging.CRITICAL, msg)

filelogger = logging.getLogger('file')
filelogger.addHandler(logging.FileHandler(logfile))
filelogger.setLevel(logging.DEBUG)
logger.addLogger(filelogger, logging.DEBUG)

if not daemon:
	stdoutlogger = logging.getLogger('stdout')
	stdoutlogger.addHandler(logging.StreamHandler(sys.stdout))
	stdoutlogger.setLevel(logging.DEBUG)
	if not quiet:
		logger.addLogger(stdoutlogger, logging.WARNING)
	else:
		logger.addLogger(stdoutlogger, logging.ERROR)

info("Mumym " + version + " starting up.")

def isgismu(line): return (line[4] != " ")

def isPossible(gismu):
    for l in range(len(gismu)):
	if gismu.rfind(gismu[l]) != l:
	    return False
    return True
	    
def getgismu(line): 
    debug(":" + line[1:6] + ":")
    return line[1:6]	

gihuste = map(getgismu, filter(isgismu, open(gihuste_loc).readlines()))
possible_gismu = filter(isPossible, gihuste)


# TODO
# Make man page.
# Use logger stuff from ebg.
# Fix regexp usage. It's icky.

class AI:
	"Base class for AIs."
	def __init__(self, mumym):
		global possible_gismu
		self.possible_gismu = possible_gismu
		self.mumym = mumym
		
	def onGuess(self, guess, score):
		"Called when someone makes a guess, including the current AI."
		pass

	def makeGuess(self):
		"Called when it's the AI's turn, you should make a guess with self.mumym.guess()."
		pass


class SimpleAI(AI): # la alis.
	"A simple AI that will only guess random words that haven't already been guessed."
	def onGuess(self, guess, score):
		# This needs to be done in a try block, in case some bonehead guesses a word
		#  that's already been guessed.
		try: 
			self.possible_gismu.remove(guess)
		except:
			pass

	def makeGuess(self):
		guess = random.choice(self.possible_gismu)
		self.mumym.msg(self.mumym.chan, "la .alis smadi le du'u zo " + guess + " valsi")
		self.mumym.guess("alis", guess)

class Mumym(irc.IRCClient):
	def __init__(self):
		global possible_gismu, gihuste
		self.possible_gismu = possible_gismu
		self.gihuste = gihuste 
		self.nickname = nick
		self.realname = "la mumym pe li" + version
		self.versionName = "la mumym"
		self.versionNum = "li " + version
		self.sourceURL = "http://savannah.nongnu.org/projects/ircbots/"
		
		self.chan = chan
		
		self.players            = []
		self.player_is_ai       = []
		self.ais                = {"alis": SimpleAI}
		self.playing_ais        = {}
		self.current_turn       = 0
		self.current_gismu      = ""
		self.currently_playing  = False
		self.currently_starting = False
		
		self.rnd = random.Random(time.time())
		
	def isgismu(self, line): return (line[4] != " ")
	    
	def isPossible(self, gismu):
	    for l in range(len(gismu)):
		if gismu.rfind(gismu[l]) != l:
		    return False
	    return True
	    
	def getgismu(self, line): 
	    return line[1:6]	
		
	def signedOn(self):
		info("Connected.")
		self.join(self.chan)
		self.msg(self.chan, "coi rodo mi'e la mumym. mi logji selkei .i tezu'e lenu kelci kei .e'u ko cusku lu doi mumym. ko cfari li'u")
		
	def privmsg(self, who, where, what):
		if (re.compile("doi \.?mumym\.? ko cfari").match(what) != None):
			self.start_game(string.split(who,'!')[0])
		elif (re.compile("doi \.?mumym\.? ko cfagau").match(what) != None):
			self.start_playing()
		elif (re.compile("doi \.?mumym\.? mi kelci djica").match(what) != None):
			self.add_player(string.split(who,'!')[0])
		elif (re.compile("doi \.?mumym\.? ko sisti").match(what) != None):
			self.stopgame(string.split(who,'!')[0])
		elif (re.compile("doi \.?mumym\.? ko sidju").match(what) != None):
			self.signedOn()
		elif (re.compile("doi \.?mumym\.? la ([.a-zA-Z]+) kelci").match(what) != None):
			self.add_ai(re.compile("doi \.?mumym\.? la ([.a-zA-Z]+) kelci").match(what).group(1))
		elif string.split(what)[0] == "zo":
		    try:
			self.guess(string.split(who, '!')[0], string.split(what)[1])
		    except IndexError:
			pass

	def guess(self, who, guess):
		if self.currently_playing == False:
		    return
		score = 0
		if who != self.players[self.current_turn]:
			self.msg(self.chan, "doi " + who + " do na ka'e nau smadi .i ko denpa.") 
		if guess not in self.gihuste:
		    self.msg(self.chan, "doi " + who + " le do valsi na drani leka tarmi .i ko drani gasnu")
		    return
		if who != self.players[self.current_turn]:
		    return
		if guess == self.current_gismu:
		    self.endgame(who)
		    return
		for c in range(len(guess)):
		    if guess.rfind(guess[c]) == c:
			if guess[c] in self.current_gismu:
			    score += 1
		
		jboscore = " li " + numbers[score]
		
		self.msg(self.chan, "di'e se smadi fi mi .i kancu zo " + guess + jboscore)
		
		self.advance_turn()
		
	def advance_turn(self):
		if self.current_turn == len(self.players)-1:
		    self.current_turn = 0
		else:
		    self.current_turn += 1
		
		if not self.player_is_ai[self.current_turn]:
			self.msg(self.chan, "doi " + self.players[self.current_turn] + " do smadi le du'u ma valsi")
		else:
			self.playing_ais[self.players[self.current_turn]].makeGuess()
	def stopgame(self, who):
		self.msg(self.chan, "vi'o doi " + who )
		self.players = []
		self.player_is_ai = []
		self.playing_ais = {}
		self.current_turn = 0
		self.current_gismu = ""
		self.currently_playing = False
		self.currently_starting = False

	def endgame(self, who):
		self.msg(self.chan, "di'e se smadi fi mi .i kancu zo " + self.current_gismu + " li mu .i doi " + who + " do jinga .ui")
		self.msg(self.chan, "lenu kelci kei cu selfanmo")
		self.players = []
		self.current_turn = 0
		self.current_gismu = ""
		self.currently_playing = False
		self.currently_starting = False

	def start_game(self, who):
		if self.currently_playing == True:
		    self.msg(self.chan, ".i je'e " + who + " ku'i ca kelci .i ko denpa")
		    return
		if self.currently_starting == True:
		    self.msg(self.chan, ".i je'e " +
		    who + " ku'i ca cfari .i ko denpa gi'a cusku lu doi mumym. mi bredi li'u")
		    return
		self.currently_starting = True
		self.msg(self.chan, ".i ca cfari .i tezu'e lenu do kelci kei .e'u ko cusku lu doi mumym. mi kelci djica li'u .i ca lenu rodo bredi kei ko cusku lu doi mumym. ko cfagau li'u .i lu doi mumym. ko sisti li'u cu rinka le nu mi sisti le fanmo")
	
	def add_ai(self, who):
		if self.currently_starting == False:
			return
		if who not in self.ais:
			self.msg(self.chan, ".i la " + who + " na zasti")
			return
		if who in self.players:
			self.msg(self.chan, ".i la " + who + " puzi kelci")
			return
		self.players.append(who)
		self.player_is_ai.append(True)
		self.playing_ais[who] = self.ais[who](self)
		self.msg(self.chan, ".i la " + who + " kelci")

	def add_player(self, who):
		if self.currently_starting == False:
		    return
		if who not in self.players:
		    self.players.append(who)
		    self.player_is_ai.append(False)
		    self.msg(self.chan, ".i doi " + who + " do kelci")
		    
	def start_playing(self):
		if self.currently_starting == False:
		    return
		if len(self.players) == 0:
		    self.msg(self.chan, ".i no kelci cu bredi .i tezu'e lenu do kelci kei .e'u ko cusku lu doi mumym. mi kelci djica li'u")
		    return
		self.currently_starting = False
		self.current_gismu = self.rnd.choice(self.possible_gismu)
		self.currently_playing = True
		self.msg(self.chan, "ca kelci")
		if self.player_is_ai[self.current_turn]:
			self.playing_ais[self.players[self.current_turn]].makeGuess()
		else:
			self.msg(self.chan, "doi " + self.players[self.current_turn] + " do smadi le du'u ma valsi")

if daemon:
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent
    os.setsid()
    os.umask(077)
    for i in range(3):
        try:
            os.close(i)
        except OSError, e:
            if e.errno != errno.EBADF:
                raise
	
if pidfile != None:
	open(pidfile,'w').write(str(os.getpid()))

try:
	import pwd
	if os.getuid() == 0: # Running as root is bad. Try running as 'mumym'.
		uid = pwd.getpwnam('mumym')[2]
		os.chown(logfile, uid, uid)
		os.setuid(uid)
except: # Something went wrong. Either the pwd module isn't available, or there is no mumym user...
	pass
	

class MumymFactory(protocol.ClientFactory):
    
	protocol = Mumym

	def clientConnectionLost(self, connector, reason):
        	connector.connect()

	def clientConnectionFailed(self, connector, reason):
        	reactor.stop()


if __name__ == '__main__':
	f = MumymFactory()
	
	server, port = random.choice(servers)
	reactor.connectTCP(server, port, f)

	reactor.run()
