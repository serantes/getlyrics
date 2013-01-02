#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       ttplayer.py
#
#       Copyright 2012 Ignacio Serantes <kde@aynoa.net>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

try:
    import HTMLParser, random, re, sys, urllib
    from xml.dom import minidom
    from ttpClient import ttpClient
    pluginEnabled = True

except:
    pluginEnabled = False


def download(base, args = None):
    """
        Downloads data from a web server.
    """
    if args != None:
        sArgs = {}
        for key in args:
            sArgs[key] = args[key].encode("utf-8")
        args = urllib.urlencode(sArgs)

    else:
        args = ''

    try:
        result = urllib.urlopen(base + args).read()

    except:
        result = ""

    return result


def cleanLRC(lyrics = ""):
    """
        Cleans all lrc related stuff.
    """
    try:
        lyricsLines = lyrics.split("\n")
        lyricsDict = dict()
        h = HTMLParser.HTMLParser()

        for line in lyricsLines:
            line = unicode(line.strip(), sys.getfilesystemencoding())
            line = h.unescape(line)
            try:
                if ((line[0] == "[") and (line[3] == ":") and (line[6] == ".") and (line[9] == "]")):
                    elements = line.rsplit("]")
                    lyric = ""
                    key = None
                    for element in reversed(elements):
                        if (element == ""):
                            continue

                        # Time format: [mm:ss.mm]
                        if (element[0] == "["):
                            if ((element[3] == ":") and (element[6] == ".")):
                                key = element + "]"

                            else:
                                lyric = element + lyric

                        else:
                            components = element.split("[")
                            if (len(components) == 2):
                                # Time format: [mm:ss.mm]
                                if ((components[1][2] == ":") and (components[1][5] == ".")):
                                    key = "[" + components[1] + "]"
                                    lyricsDict[key] = lyric
                                    lyric = components[0]
                                    continue

                                else:
                                    lyric = components[0] + "[" + components[1] + "]" + lyric

                            else:
                                lyric = element

                        if key != None:
                            lyricsDict[key] = lyric

            except:
                pass

        keys = lyricsDict.keys()
        keys.sort()
        lyrics = "\n".join([lyricsDict[key] for key in keys]).strip()

    except:
        pass

    return lyrics


def getLyricUrl(lyricsList, artist, title):
    """
        Gets the url for the search lyric.
    """
    result = None

    dom = minidom.parseString(lyricsList)
    lrcList = dom.getElementsByTagName('lrc')

    for node in lrcList:
        lrcArtist = node.getAttribute('artist').strip().lower()
        lrcTitle = node.getAttribute('title').strip().lower()

        # Strip parenthesis.
        p = re.compile("\(.*\)")
        stripLrcArtist = p.sub('', lrcArtist).strip()
        stripArtist = p.sub('', artist).strip()
        stripLrcTitle = p.sub('', lrcTitle).strip()
        stripTitle = p.sub('', title).strip()

        if ((lrcTitle == title) or (stripLrcTitle == stripTitle)):
            if ((lrcArtist == artist) or (stripLrcArtist == stripArtist)):
                #URL_BASE = "http://ttlrcct.qianqian.com/dll/lyricsvr.dll?dl?"
                URL_BASE = "http://ttlrccnc.qianqian.com/dll/lyricsvr.dll?dl?"
                #URL_BASE = "http://lrcct2.ttplayer.com/dll/lyricsvr.dll?dl?"
                URL_PARAMS = "Id=%d&Code=%d&uid=01&mac=%012x"
                lrcId = int(node.getAttribute('id'))
                result = URL_PARAMS % (lrcId, ttpClient.CodeFunc(lrcId, (node.getAttribute('artist') + node.getAttribute('title')).encode('UTF8')), random.randint(0,0xFFFFFFFFFFFF))
                result = URL_BASE + result

    return result


def ttPlayer_getLyrics(artist, title):
    """
        Search for matches and return the lyrics if there is one match.
    """
    CHARACTER_REPLACEMENTS = [["/", "-"], [" & ", " and "], ["'", ""], ["`", ""], [" ", ""]]

    artist = artist.lower()
    title = title.lower()

    # Strip parenthesis.
    p = re.compile("\(.*\)")
    artistStrip = p.sub('', artist).strip()
    titleStrip = p.sub('', title).strip()

    # Replace some special characters.
    cleanArtist = artistStrip
    cleanTitle = titleStrip
    for item in CHARACTER_REPLACEMENTS:
        cleanArtist = cleanArtist.replace(item[0], item[1])
        cleanTitle = cleanTitle.replace(item[0], item[1])

    #URL_BASE = "http://ttlrcct.qianqian.com/dll/lyricsvr.dll?sh?"
    URL_BASE = "http://ttlrccnc.qianqian.com/dll/lyricsvr.dll?sh?"
    #URL_BASE = "http://lrcct2.ttplayer.com/dll/lyricsvr.dll?sh?"
    URL_PARAMS = "Artist=%s&Title=%s&Flags=0"
    url = URL_BASE + URL_PARAMS % (ttpClient.EncodeArtTit(cleanArtist), ttpClient.EncodeArtTit(cleanTitle))

    try:
        url = getLyricUrl(download(url), artist, title)

    except:
        url = None

    lyrics = ""
    if (url != None):
        try:
            lyrics = cleanLRC(download(url))

        except:
            pass

    lyrics = lyrics.strip()
    if (lyrics == ""):
        lyrics = None

    return lyrics


def getLyrics(artist, title, verbose = False):
    """
        Get lyrics by artist and title in ttPlayer.
    """
    if not pluginEnabled:
        if verbose:
            print "Plugin is disabled because not all libraries are available: HTMLParser, random, re, sys urllib and/or xml."

        return None

    lyrics = ttPlayer_getLyrics(artist, title)

    return lyrics


if __name__ == '__main__':

    lyrics = getLyrics(u"倖田來未 (Koda Kumi)", u"IN THE AIR", True)
    print(lyrics)
