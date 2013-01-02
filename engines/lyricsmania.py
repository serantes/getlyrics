#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       lyricsmania.py
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
    import lxml.html, re, urllib
    pluginEnabled = True

except:
    pluginEnabled = False


def cleanName(name):
    # Removing al text between parenthesis when there is a previous space.
    p = re.compile(r' \(.*?\)')
    cleanedName = p.sub('', name).strip()
    if (cleanedName != ""):
        name = cleanedName

    return name.strip()


def _getLyrics(artist, title):
    """
        Main get lyrics function
    """

    URL_BASE = "http://www.lyricsmania.com/"
    lyrics = None

    artist = cleanName(artist)
    title = cleanName(title)

    search = u"%(artist)s %(title)s" % {"artist": artist, "title": title}
    url = URL_BASE + "searchnew.php?%s" % urllib.urlencode({'k': search.encode("utf-8"), 'x':'0', 'y': '0'})
    page = lxml.html.parse(urllib.urlopen(url))
    try:
        links = page.getroot().cssselect('#albums>h1>a')

        for item in links:
            item = item.text.split(" - ")
            foundArtist = item[0]
            foundTitle = item[1]

            if (foundArtist == artist) and (foundTitle == title):
                url = "%s_lyrics_%s.html" % (foundTitle.lower().replace(" ", "_"), foundArtist.lower().replace(" ", "_"))

                content = urllib.urlopen(URL_BASE + url)
                page = lxml.html.parse(content)
                div = page.getroot().get_element_by_id('songlyrics_h')
                lyrics = ''.join([text for text in div.itertext()]).strip()

    except:
        pass

    return lyrics


def getLyrics(artist, title, verbose = False):
    """
        Get lyrics by artist and title
    """
    if not pluginEnabled:
        if verbose:
            print "Plugin is disabled because not all libraries are available: lxml.html, re, and/or urllib."

        return None

    lyrics = _getLyrics(artist, title)

    if (lyrics == None):
        source = None

    return lyrics


if __name__ == '__main__':

    lyrics = getLyrics(u"Peter Gabriel", u"Sledgehammer", True)
    #lyrics = getLyrics(u"倖田來未 (Koda Kumi)", u"IN THE AIR", True)
    print(lyrics)
