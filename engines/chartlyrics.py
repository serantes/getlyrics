#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       chartlyrics.py
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
    import re, urllib
    from xml.dom import minidom
    pluginEnabled = True

except:
    pluginEnabled = False


def download(base, args = None):
    """
        Downloads data from a web server
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


def removeTags(html):
    # intros
    html = html.replace("<br>", "\n").replace("<br />", "\n")

    # remove html tags.
    p = re.compile(r'<.*?>')
    html = p.sub('', html)

    return html


def cleanName(name):
    # Removing al text between () when there is a previous space.
    p = re.compile(r' \(.*?\)')
    cleanedName = p.sub('', name).strip()
    if (cleanedName != ""):
        name = cleanedName

    return name.strip()


def chartLyrics_getLyrics(artist, title, extendedSearch = True):
    args = {"artist": artist,
            "song": title
            }

    data = download("http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect?", args)

    lyrics = ""
    if data != "":
        # This is the returned data.
        #<GetLyricResult>
        #   <TrackId></TrackId>
        #   <LyricChecksum></LyricChecksum
        #   <LyricId></LyricId>
        #   <lyricSong></LyricSong>
        #   <LyricArtist></LyricArtist>
        #   <LyricUrl></LyricUrl>
        #   <LyricCoverArtUrl></LyriccOVerArtUrl>
        #   <LyricRank></LyricRank>
        #   <LyricCorrectUrl></LyricCorrectUrl>
        #   <Lyric></Lyric>
        #</GetLyricResult>

        dom = minidom.parseString(data)

        for item in dom.getElementsByTagName("Lyric"):
            lyrics += removeTags(item.toxml()) + "\n"

    lyrics = lyrics.strip()
    if (lyrics == ""):
        lyrics = None

    return lyrics


def getLyrics(artist, title, verbose = False):
    """
        Get lyrics by artist and title
        set cacheDir to a valid (existing) directory to enable caching.
    """
    if not pluginEnabled:
        if verbose:
            print "Plugin is disabled because not all libraries are available: re, urllib and/or xml."

        return None

    lyrics = chartLyrics_getLyrics(cleanName(artist), cleanName(title), False)

    if (lyrics == None):
        source = None

    return lyrics


if __name__ == '__main__':

    lyrics = getLyrics(u"Peter Gabriel", u"Sledgehammer", True)
    print(lyrics)
