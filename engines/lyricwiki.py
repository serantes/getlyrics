#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       lyricwiki.py
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
    import json, re, urllib
    from BeautifulSoup import BeautifulSoup, Comment
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


def normalizeJson(data):
    #return data[7:].replace("'", "\"")
    return data[7:].replace("\"", "\\\"").replace("'", "\"")


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


def lyricWiki_downloadArtistSongs(artist):

    args = {"artist": artist,
            "fmt": "xml"
            }

    data = download("http://lyrics.wikia.com/api.php?", args)
    dom = minidom.parseString(data)
    #<getArtistResponse>
    #   <artist></artist>
    #   <albums>
    #       <album></album>
    #       <year></year>
    #       <songs>
    #           <item></item>
    #       </songs>title.encode("utf-8")
    #   </albums>
    #</getArtistResponse>

    songs = '\nNot found, suggested songs:\n'
    for song in dom.getElementsByTagName('item'):
        songs += removeTags(song.toxml()) + "\n"

    return songs


def lyricWiki_getLyrics(artist, title, extendedSearch = True):

    args = {"artist": artist,
            "song": title,
            "fmt": "json"
            }

    url = json.loads(normalizeJson(download("http://lyrics.wikia.com/api.php?", args)))["url"]
    html = download(url)

    soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    data = soup.find("div", {"class":"lyricbox"})
    if data != None:
        comments = data.findAll(text = lambda text:isinstance(text, Comment))
        [comment.extract() for comment in comments]
        [tag.extract() for tag in data.findAll('div')]
        data = removeTags(unicode(data)).strip()

    else:
        if extendedSearch:
            data = lyricWiki_downloadArtistSongs(artist).strip()
        else:
            data = None

    return data


def getLyrics(artist, title, verbose = False):
    """
        Get lyrics by artist and title
        set cacheDir to a valid (existing) directory to enable caching.
    """
    if not pluginEnabled:
        if verbose:
            print "Plugin is disabled because not all libraries are available: BeautifulSoup, json, re and/or urllib."

        return None

    #lyrics = lyricWiki_getLyrics(artist, title, extendedSearch)
    lyrics = lyricWiki_getLyrics(cleanName(artist), cleanName(title), False)

    return lyrics


if __name__ == '__main__':

    lyrics = getLyrics(u"Peter Gabriel", u"Sledgehammer", True)
    print(lyrics)
