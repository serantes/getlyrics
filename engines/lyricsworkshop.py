#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       lyricsworkshop.py
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
    import os, subprocess
    pluginEnabled = True

except:
    pluginEnabled = False

FILE_NAME_PATTER = u"%s_%s_%s_%s.html"

def getLyrics(directory, artist, album, tracknumber, title, verbose = False):
    """
        Get lyrics by artist and title from the lyrics workshop cache
    """
    if not pluginEnabled:
        if verbose:
            print "Plugin is disabled because not all libraries are available: os and/or subprocess."

        return None

    if (directory == ""):
        return None

    lyrics = u""

    try:
        tracknumber = '%02d' % int(tracknumber.split("/")[0])

    except:
        tracknumber = 0

    filename = FILE_NAME_PATTER % (artist, album, tracknumber, title)
    filename = filename.replace(" ", "_")
    if verbose:
        print "Searching in html cache for:", filename

    filename = os.path.join(directory, filename)
    if os.path.isfile(filename):
        addLines = True
        try:
            lyricsLines = subprocess.check_output(['html2text', filename, "UTF-8"]).split("\n")
            lyrics = u""
            for line in lyricsLines:
                line = line.strip()
                if (line[:5] == "**** ") and (line[-5:] == " ****"):
                    continue

                elif (line[:30] == "=============================="):
                    addLines = False
                    continue

                else:
                    if addLines:
                        lyrics += unicode(line, 'utf-8') + "\n"

        except:
            pass

    if lyrics == "":
        lyrics = None

    else:
        lyrics = lyrics.strip()

    return lyrics


if __name__ == '__main__':

    #lyrics = getLyrics("./tests/", u"倖田來未 (Koda Kumi)", u"Twinkle〜English Version〜", True)
    lyrics = getLyrics("./tests/", u"f(x)", u"제트별 (Jet)", True)
    print(lyrics)
