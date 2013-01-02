#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       lrc.py
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
    import HTMLParser, os, sys
    pluginEnabled = True

except:
    pluginEnabled = False

FILE_NAME_PATTER = u"%s - %s.lrc"

def getLyrics(directory, artist, title, verbose = False):
    """
        Get lyrics by artist and title from the lrc cache
    """
    if not pluginEnabled:
        if verbose:
            print "Plugin is disabled because not all libraries are available: HTMLParser, os and/or sys."

        return None

    if (directory == ""):
        return None

    lyrics = u""

    filename = FILE_NAME_PATTER % (artist, title)
    filename = filename.replace("?", "")
    filename = os.path.join(directory, filename)
    if os.path.isfile(filename):
        try:
            f = open(filename, 'r')
            try:
                lyricsDict = dict()
                h = HTMLParser.HTMLParser()

                for line in f:
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

            finally:
                f.close()

        except:
            pass

    if lyrics == "":
        lyrics = None

    return lyrics


if __name__ == '__main__':

    #lyrics = getLyrics("./tests/", u"倖田來未 (Koda Kumi)", u"Twinkle〜English Version〜", True)
    lyrics = getLyrics("./tests/", u"f(x)", u"제트별 (Jet)", True)
    print(lyrics)
