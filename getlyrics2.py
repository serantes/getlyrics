#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import Queue
import threading

import bson, bson.json_util, pymongo

import hashlib, json, os, re, subprocess, sys, time

import ConfigParser
from optparse import OptionParser

from mpd import (MPDClient, CommandError)
from socket import error as SocketError

from engines import *

SCRIPT_NAME = os.path.splitext(os.path.basename(sys.argv[0]))[0]

scriptsPath = os.path.dirname(sys.argv[0]) + '/'

# Configuration parameters.
params = {
    'mpdHost': 'localhost',
    'mongoDBHost': 'localhost',
    'cacheDirectory': os.path.expanduser('~/.lyrics'),
    'lrcDirectory': '',
    'lyricsWorkshopDirectory': '', 
    'autoEditWhenNoLyrics': False
}

cfgFile = 'getlyrics.conf'
config = ConfigParser.SafeConfigParser()
config.read(['/etc/' + cfgFile, os.path.expanduser('~/.config/getlyrics/' + cfgFile)])

if config.has_option('General', 'autoEditWhenNoLyrics'):
    params['autoEditWhenNoLyrics'] = config.get('General', 'AutoEditWhenNoLyrics', False)

if config.has_option('General', 'mpdHost'):
    params['mpdHost'] = config.get('General', 'mpdHost')

if config.has_option('General', 'mongoDBHost'):
    params['mongoDBHost'] = config.get('General', 'mongoDBHost')

if config.has_option('Cache', 'directory'):
    params['cacheDirectory'] = os.path.expanduser(config.get('Cache', 'directory'))

if config.has_option('Engines', 'lrcDirectory'):
    params['lrcDirectory'] = os.path.expanduser(config.get('Engines', 'lrcDirectory'))

if config.has_option('Engines', 'lyricsWorkshopDirectory'):
    params['lyricsWorkshopDirectory'] = os.path.expanduser(config.get('Engines', 'lyricsWorkshopDirectory'))

# Command line parameters.
parser = OptionParser()
parser.add_option("", "--autoedit", action = "store_true", dest = "autoEditWhenNoLyrics", default = False, help = "open edition dialog when no lyrics was found")
parser.add_option("", "--engines", dest = "forcedEngines", help = "comma separated engines to use", metavar="TEXT")
parser.add_option("", "--id", dest = "docId", default = "", help = "document id", metavar="TEXT")
parser.add_option("", "--import", action = "store_true", dest = "importToMongoDB", default = False, help = "import all data to MongoDB")
parser.add_option("", "--kana", action = "store_true", dest = "kanaMode", default = False, help = "kana conversion")
parser.add_option("", "--list", dest = "list", help = "available list: engines", metavar="TEXT")
parser.add_option("", "--mongoDBHost", dest = "mongoDBHost", help = "host[:port], defaults to \"localhost\"", metavar="TEXT")
parser.add_option("", "--raw", action = "store_true", dest = "rawOutput", default = False, help = "displays data in raw format")
parser.add_option("", "--romaji", action = "store_true", dest = "romajiMode", default = False, help = u"rōmaji conversion")
parser.add_option("", "--romaja", action = "store_true", dest = "romajaMode", default = False, help = "romaja conversion")
parser.add_option("", "--search", action = "store_true", dest = "searchInCache", default = False, help = "searchs in cache, needs --title or --artist parameters")
parser.add_option("", "--translate", dest = "translateLang", help = "translation language: en, es, ja, ko, etc.", metavar="TEXT")
parser.add_option("-l", "--album", dest = "album", help = "album title", metavar="TEXT")
parser.add_option("-b", "--albumartist", dest = "albumArtist", help = "album artist name", metavar="TEXT")
parser.add_option("-a", "--artist", dest = "artist", help = "artist name", metavar="TEXT")
parser.add_option("-c", "--cachedir", dest = "cache", help = "cache directory", metavar="DIR")
parser.add_option("-p", "--createemptycache", action = "store_true", dest = "createEmptyCache", default = False, help = "creates a cache file without lyrics")
parser.add_option("-d", "--delete", action = "store_true", dest = "deleteLyrics", default = False, help = "delete lyrics from cache")
parser.add_option("-e", "--edit", action = "store_true", dest = "editLyrics", default = False, help = "edit cached lyrics with default editor")
parser.add_option("-s", "--host", dest = "host", help = "[pwd@]host[:port], defaults to \"localhost\"", metavar="TEXT")
parser.add_option("-i", "--instrumental", action = "store_true", dest = "instrumental", default = False, help = "creates a cache file with the word \"Instrumental\" instead of the lyrics")
parser.add_option("-y", "--lyricscached", action = "store_true", dest = "lyricsCached", default = False, help = "check if lyrics was cached")
parser.add_option("-o", "--overwrite", action = "store_true", dest = "overwrite", default = False, help = "overwrite lyrics in cache")
parser.add_option("-q", "--quiet", action = "store_false", dest = "verbose", default = True, help = "don't print aditional data to stdout")
parser.add_option("-r", "--removecache", action = "store_true", dest = "removeCache", default = False, help = "delete all cached data")
parser.add_option("-t", "--title", dest = "title", help = "song title", metavar="TEXT")
parser.add_option("-k", "--track", dest = "tracknumber", help = "track number", metavar="NUMBER")

(options, args) = parser.parse_args()

host = options.host
if (host == None):
    host = params['mpdHost']

mongoDBHost = options.mongoDBHost
if (mongoDBHost == None):
    mongoDBHost = params['mongoDBHost']

title = options.title
track = options.tracknumber
artist = options.artist
album = options.album
albumArtist = options.albumArtist

INTERNAL_ROMAJA = True
OUTDATED_JSON_FILES = False

if not options.autoEditWhenNoLyrics:
    options.autoEditWhenNoLyrics = params['autoEditWhenNoLyrics']

if (options.cache == None):
    cacheDir = params['cacheDirectory']

else:
    cacheDir = options.cache

connection = pymongo.MongoClient("mongodb://" + mongoDBHost)
mongoDB = connection.music
mongoDB_Lyrics = mongoDB.lyrics


def displayKDEInfo(infoMsg = "", infoType = "Information"):
    subprocess.call(["kdialog", "--title", SCRIPT_NAME + " - " +  infoType, "--passivepopup", infoMsg])


def mongoImport(cacheDir):
    count = 0
    for file in os.listdir(cacheDir):
        if file.endswith(".json"):
            docId = None
            try:
                fp = open(os.path.join(cacheDir, file))
                try:
                    doc = json.load(fp)
                    print("Importing %s by %s... " % (doc["title"], doc["artist"])),
                    docId = mongoStoreLyrics(doc)
                    print("done")
                    count += 1

                finally:
                    fp.close()

                if (docId != None):
                    os.rename(file, file + '.imported')

            except:
                print("Unexpected error:", sys.exc_info()[0])
                displayKDEInfo(sys.exc_info()[1].message, "Error")

    print("%s json files has been imported to MongoDB." % (count))



def mongoSearch(docId = "", artist = "", title = "", albumArtist = ""):
    if options.verbose:
        print('Search for lyrics in MongoDB')

    doc = None

    try:

        query = {}
        if (docId == ""):
            if (title != None):
                query['title'] = title

            if (albumArtist != None):
                query['artist'] =  albumArtist
                doc = mongoDB_Lyrics.find_one(query)

            if (doc == None):
                query['artist'] = artist
                doc = mongoDB_Lyrics.find_one(query)

        else:
            query['_id'] = bson.ObjectId(docId)
            doc = mongoDB_Lyrics.find_one(query)


    except:
        print("Unexpected error:", sys.exc_info()[0])
        displayKDEInfo(sys.exc_info()[1].message, "Error")

    return doc


def mongoRemoveLyrics(docId = "", artist = "", title = "", albumArtist = "", removeAllData = True):

    result = False
    if (docId == ""):
        doc = mongoSearch("", artist, title, albumArtist)
        try:
            docId = doc["_id"]

        except:
            docId = ""

    else:
        docId = bson.ObjectId(docId)

    if (docId != ""):

        try:
            if removeAllData:
                mongoDB_Lyrics.remove({"_id": bson.ObjectId(docId)})

            else:
                # Must remove all lyrics information respecting the rest of the data.
                keysToDelete = []
                for key in doc:
                    if ((key == "lyrics") or (key in ("kana", "romaji", "romaja")) or (key[:5] == "lang_")):
                        keysToDelete.append(key)

                for key in keysToDelete:
                    doc.pop(key, None)

                cacheLyric(docId, artist, title, "", "", "")


            result = True

        except:
            print("Unexpected error:", sys.exc_info()[0])
            displayKDEInfo(sys.exc_info()[1].message, "Error")

    return result


def mongoRestoreLyrics(docId = "", artist = "", title = "", albumArtist = "", lyricsKind = ""):

    doc = mongoSearch(docId, artist, title, albumArtist)

    if (doc == None):
        #      docId, lyrics, artist, title, source
        return None, None, artist, title, ""

    if (lyricsKind == ""):
        lyricsKind = 'lyrics'

    artist = title = source = lyrics = ""
    if ("artist" in doc):
        artist = doc["artist"].strip()

    if ("title" in doc):
        title = doc["title"].strip()

    if ("source" in doc):
        source = doc["source"].strip()

    if (lyricsKind in ("kana", "romaji", "romaja")):
        if (lyricsKind in doc):
            lyrics = doc[lyricsKind].strip()

        elif (lyrics == ""):
            if ("lyrics" in doc):
                lyrics = doc["lyrics"].strip()
                try:
                    if (lyricsKind == "kana"):
                        lyrics = subprocess.check_output([scriptsPath + "ka2ka", "--kana", "-p", lyrics]).strip()
                        if (lyrics != ""):
                            lyrics += "\n--\nAutomatic conversion using \"%s\"" % "ka2ka"

                    elif (lyricsKind == "romaji"):
                        lyrics = subprocess.check_output([scriptsPath + "ka2ka", "--romaji", "-p", lyrics]).strip()
                        if (lyrics != ""):
                            lyrics += "\n--\nAutomatic conversion using \"%s\"" % "ka2ka"

                    elif (lyricsKind == "romaja"):
                        if INTERNAL_ROMAJA:
                            lyrics = fromHangulToRomaja(lyrics).strip()
                            if (lyrics != ""):
                                lyrics += "\n--\nAutomatic conversion using internal method"

                        else:
                            lyrics = subprocess.check_output([scriptsPath + "ha2ro.pl", lyrics]).strip()
                            if (lyrics != ""):
                                lyrics += "\n--\nAutomatic conversion using \"%s\"" % "ha2ro.pl"

                except:
                    pass

                if lyrics != "":
                    doc[lyricsKind] = lyrics

    elif (lyricsKind[:5] == "lang_"):
        if (lyricsKind in doc):
            lyrics = doc[lyricsKind].strip()

        else:
            if ("lyrics" in doc):
                lyrics = doc["lyrics"].strip()
                try:
                    lyrics = subprocess.check_output([scriptsPath + "gtc", "-d", options.translateLang, lyrics]).strip()
                    if (lyrics != ""):
                        lyrics += "\n--\nAutomatic translation using \"%s\"" % "Google Translate"

                except:
                    pass

            else:
                lyrics = ""

    else:
        if (lyricsKind in doc):
            lyrics = doc[lyricsKind].strip()

    docId = doc["_id"]

    return docId, lyrics, artist, title, source


def mongoStoreLyrics(doc = None):

    docId = None

    if (doc != None):
        try:
            if ("_id" in doc):
                mongoDB_Lyrics.save(doc)

            else:
                mongoDB_Lyrics.insert(doc)

            docId = doc["_id"]

        except:
            print("Unexpected error:", sys.exc_info()[0])
            displayKDEInfo(sys.exc_info()[1].message, "Error")

    return docId


def mongoRawPrint(docId):
    doc = mongoSearch(docId)

    print(bson.json_util.dumps(doc, sort_keys=True, indent=4))


#
# Convierte un texto de Hangul a Romaja.
#
# http://czyborra.com/unicode/characters.html !!! fundamental !!!
# http://sori.org/hangul/romanizations.html#Roman_Intro
#
def fromHangulToRomaja(data):
    if (data == ''):
        return ""

    # Seems like there are different interpretations :P.

    # Javascript code list.
    #choseongList = 'g;gg;n;d;dd;l;m;b;bb;s;ss;;j;jj;c;k;t;p;h'.split(';')
    #jungseongList = 'a;ae;ya;yae;eo;e;yeo;ye;o;wa;wae;oe;yo;u;weo;we;wi;yu;eu;yi;i'.split(';')
    #jongseongList = ';g;gg;gs;n;nj;nh;d;l;lg;lm;lb;ls;lt;lp;lh;m;b;bs;s;ss;ng;j;c;k;t;p;h'.split(';')

    # Perl-Lingua code list.
    choseongList = 'g;kk;n;d;tt;r;m;b;pp;s;ss;;j;jj;ch;k;t;p;h'.split(';')
    jungseongList = 'a;ae;ya;yae;eo;e;yeo;ye;o;wa;wae;oe;yo;u;wo;we;wi;yu;eu;yi;i'.split(';')
    jongseongList = ';g;kk;ks;n;nj;nh;d;r;lg;lm;lb;ls;lt;lp;lh;m;b;ps;s;ss;ng;j;c;k;t;p;h'.split(';')

    # Python code list.
    #choseongList = 'g;gg;n;d;dd;r;m;b;bb;s;ss;;j;jj;c;k;t;p;h'.split(';')
    #jungseongList = 'a;ae;ya;yae;eo;e;yeo;ye;o;wa;wae;oe;yo;u;weo;we;wi;yu;eu;yi;i'.split(';')
    #jongseongList = ';g;gg;gs;n;nj;nh;d;l;lg;lm;lb;ls;lt;lp;lh;m;b;bs;s;ss;ng;j;c;k;t;p;h'.split(';')

    firstChar = 44032
    lastChar = firstChar + 11172

    result = ''
    charCode = 0
    choseongIndex = 0
    jungseongIndex = 0
    i = 0
    while True:
        if (i >= len(data)):
            break

        charCode = ord(data[i])
        if ((charCode < firstChar) or (charCode > lastChar)):
            result += data[i]
            i += 1
            continue

        n = firstChar;
        choseongIndex = 0
        while True:
            n += len(jungseongList) * len(jongseongList)
            if (n > charCode):
                break

            choseongIndex += 1

        n -= len(jungseongList) * len(jongseongList)

        jungseongIndex = 0
        while True:
            n += len(jongseongList)
            if (n > charCode):
                break

            jungseongIndex += 1

        n -= len(jongseongList)
        jongseong = charCode - n
        result += choseongList[choseongIndex] + jungseongList[jungseongIndex] + jongseongList[jongseong]

        i += 1

    return result


def mpdInfo(host = "localhost", keys = ("albumartist", "album", "artist")):
    result = dict()

    client = MPDClient()

    host = host.split(":")
    try:
        port = host[1]

    except:
        port = "6600"

    host = host[0].split("@")

    try:
        password = host[0]
        host = host[1]

    except:
        password = ""
        host = host[0]

    conId = {'host': host, 'port': port}

    try:
        client.connect(**conId)

    except SocketError:
        result["error"] = "Connection to mpd failed."
        return False, result

    if password:
        try:
            client.password(password)

        except CommandError:
            result["error"] = "Authentification failed."
            return False, result

    for key in client.currentsong():
        value = client.currentsong()[key]
        if (type(value).__name__ == "list"):
            value = ", ".join(value)

        key = "%s" % key
        if key in keys:
            result[key] = value

    client.disconnect()

    return True, result


def getSongPath(cacheDir, artist, title):
    digest = hashlib.sha1(artist.lower().encode(sys.getfilesystemencoding()) + title.lower().encode(sys.getfilesystemencoding())).hexdigest()
    return os.path.join(cacheDir, digest) + ".json"


def findSongPath(cacheDir, artist, title, albumArtist):
    path = getSongPath(cacheDir, artist, title)
    if not os.path.exists(path):
        path = getSongPath(cacheDir, albumArtist, title)
        if not os.path.exists(path):
            path = None

    return path


def cacheLyric(docId = None, artist = "", title = "", source = "", lyrics = "", lyricsKind = ""):
    if (source == None):
        source = ""

    if (lyrics == None):
        lyrics = ""

    if True:
        if (docId == None):
            docId = mongoStoreLyrics({"artist": artist, lyricsKind: lyrics, "time": time.time(), "title": title, "source": source})

        else:
            docId = mongoStoreLyrics({"_id": docId, "artist": artist, lyricsKind: lyrics, "time": time.time(), "title": title, "source": source})

    else:
        docId = getSongPath(cacheDir, artist, title)
        if not os.path.exists(os.path.dirname(docId)):
            # Creamos el path.
            os.makedirs(os.path.dirname(docId))

        if ((lyricsKind == "") or (lyricsKind == None)):
            lyricsKind = "lyrics"

        try:
            if os.path.exists(docId):
                fp = open(docId, "r")
                try:
                    js = json.load(fp)
                    fp.close()
                    fp = open(docId, "w")
                    js[lyricsKind] = lyrics
                    json.dump(js, fp, indent = 4)

                finally:
                    fp.close()

            else:
                fp = open(docId, "w")
                try:
                    json.dump({"time": time.time(), "artist": artist, "title": title,
                                "source": source, lyricsKind: lyrics}, fp, indent = 4)
                finally:
                    fp.close()

        except:
            pass

    return docId


def cleanName(name):
    # Removing al text between () when there is a previous space.
    p = re.compile(r' \(.*?\)')
    cleanedName = p.sub('', name).strip()
    if (cleanedName != ""):
        name = cleanedName

    return name.strip()


def readCachedLyrics(cacheUrl, artist = "", title = "", albumArtist = "", lyricsKind = None):
    lyrics = source = None
    if os.path.isfile(cacheUrl):
        path = cacheUrl

    else:
        path = findSongPath(cacheDir, artist, title, albumArtist)

    if (path != None):
        try:
            fp = open(path)
            try:
                js = json.load(fp)
                artist = title = source = lyrics = ""

                if "artist" in js:
                    artist = js["artist"].strip()

                if "title" in js:
                    title = js["title"].strip()

                if "source" in js:
                    source = js["source"].strip()

                if lyricsKind in ("kana", "romaji", "romaja"):
                    lyrics = ""
                    if lyricsKind in js:
                        lyrics = js[lyricsKind].strip()

                    if (lyrics == ""):
                        if "lyrics" in js:
                            lyrics = js["lyrics"].strip()
                            try:
                                if lyricsKind == "kana":
                                    lyrics = subprocess.check_output([scriptsPath + "ka2ka", "--kana", "-p", lyrics]).strip()
                                    if (lyrics != ""):
                                        lyrics += "\n--\nAutomatic conversion using \"%s\"" % "ka2ka"

                                elif lyricsKind == "romaji":
                                    lyrics = subprocess.check_output([scriptsPath + "ka2ka", "--romaji", "-p", lyrics]).strip()
                                    if (lyrics != ""):
                                        lyrics += "\n--\nAutomatic conversion using \"%s\"" % "ka2ka"

                                elif lyricsKind == "romaja":
                                    if INTERNAL_ROMAJA:
                                        lyrics = fromHangulToRomaja(lyrics).strip()
                                        if (lyrics != ""):
                                            lyrics += "\n--\nAutomatic conversion using internal method"


                                    else:
                                        lyrics = subprocess.check_output([scriptsPath + "ha2ro.pl", lyrics]).strip()
                                        if (lyrics != ""):
                                            lyrics += "\n--\nAutomatic conversion using \"%s\"" % "ha2ro.pl"

                            except:
                                pass

                elif lyricsKind[:5] == "lang_":
                    if lyricsKind in js:
                        lyrics = js[lyricsKind].strip()

                    else:
                        if "lyrics" in js:
                            lyrics = js["lyrics"].strip()
                            try:
                                lyrics = subprocess.check_output([scriptsPath + "gtc", "-d", options.translateLang, lyrics]).strip()
                                if (lyrics != ""):
                                    lyrics += "\n--\nAutomatic translation using \"%s\"" % "Google Translate"

                            except:
                                pass

                        else:
                            lyrics = ""

                else:
                    if lyricsKind in js:
                        lyrics = js[lyricsKind].strip()

            finally:
                fp.close()

        except:
            pass

    return lyrics, artist, title, source, path



def searchLyrics(q, command, engine):
    try:
        lyrics = eval(command)

    except:
        lyrics = None

    q.put([lyrics, engine])



def manageEngines(options, metadata):

    album = albumArtist = artist = title = track = ""
    if ("album" in metadata):
        album = metadata["album"]

    if ("albumArtist" in metadata):
        albumArtist = metadata["albumArtist"]

    if ("artist" in metadata):
        artist = metadata["artist"]

    if ("title" in metadata):
        title = metadata["title"]

    if ("track" in metadata):
        track = metadata["track"]

    toSearch = []
    if (options.forcedEngines == None):
        enginesToUse = []

    else:
        enginesToUse = options.forcedEngines.strip().replace(" ", "").split(",")

    for engine in ENGINES:
        if ((enginesToUse != []) and not (engine[0] in enginesToUse)):
            continue

        if engine[2]:
            # Web engine.
            if (engine[1] == 1):
                command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", %s)" % (artist, title, options.verbose)
                toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, artist)]]
                if (albumArtist != artist):
                    command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", %s)" % (albumArtist, title, options.verbose)
                    toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, albumArtist)]]

            elif (engine[2] == 2):
                command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", u\"%s\", %s)" % (artist, album, track, title, options.verbose)
                toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, artist)]]
                if (albumArtist != artist):
                    command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", u\"%s\", %s)" % (albumArtist, album, track, title, options.verbose)
                    toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, albumArtist)]]

        else:
            # Filesystem engine.
            if (engine[1] == 1):
                command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", %s)" % (params[engine[0] + 'Directory'], artist, title, options.verbose)
                toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, artist)]]
                if (albumArtist != artist):
                    command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", %s)" % (params[engine[0] + 'Directory'], albumArtist, title, options.verbose)
                    toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, albumArtist)]]

            elif (engine[2] == 2):
                command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", u\"%s\", u\"%s\", %s)" % (params[engine[0] + 'Directory'], artist, album, track, title, options.verbose)
                toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, artist)]]
                if (albumArtist != artist):
                    command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", u\"%s\", u\"%s\", %s)" % (params[engine[0] + 'Directory'], albumArtist, album, track, title, options.verbose)
                    toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, albumArtist)]]

    q = Queue.Queue()
    for item in toSearch:
        if options.verbose:
            print("Searching in \"%s\": %s" % (item[1], item[2]))

        t = threading.Thread(target=searchLyrics, args=(q, item[0], item[1]))
        t.daemon = True
        t.start()

    count = 0
    lyrics = source = None
    while ((lyrics == None) and (count < len(toSearch))):
        count += 1
        result = q.get()
        lyrics = result[0]
        source = result[1]

    return {"lyrics": lyrics, "source": source}


def preprocessSearchData(docId, title, artist, albumArtist, album, track):
    askMPD = ((docId == "") and ((title == None) or (artist == None) or (albumArtist == None) or (album == None) or (track == None)))

    if (askMPD and (host != "")):
        result, data = mpdInfo(host, ("title", "track", "artist", "album", "albumartist"))
        if result:
            if ((title == None) and ("title" in data)):
                title = data["title"]

            if ((track == None) and ("track" in data)):
                track = data["track"]

            if ((artist == None) and ("artist" in data)):
                artist = data["artist"]

            if ((album == None) and ("album" in data)):
                album = data["album"]

            if ((albumArtist == None) and ("albumartist" in data)):
                albumArtist = data["albumartist"]

        else:
            if options.verbose:
                print(data["error"])
                sys.exit(0)

    # todos  los datos a vacio.
    if (title == None):
        title = ""

    if (track == None):
        track = ""

    if (artist == None):
        artist = ""

    if (album == None):
        album = ""

    if (albumArtist == None):
        albumArtist = ""

    # Conversión a unicode.
    title = unicode(title.strip(), 'utf-8')
    artist = unicode(artist.strip(), 'utf-8')
    album = unicode(album.strip(), 'utf-8')
    albumArtist = unicode(albumArtist.strip(), 'utf-8')
    track = unicode(track.strip(), 'utf-8')

    # Si no hay artist usar el albumArtist
    if (artist == ""):
        artist = albumArtist

    # Si no hay albumArtis usar artist
    if (albumArtist == ""):
        albumArtist = artist

    # Varificamos que tengamos suficientes metadatos.
    if ((options.docId == "") and ((artist == "") or (title == ""))):
        if options.verbose:
            print('No metadata available.')

        sys.exit(0)

    return title, artist, albumArtist, album, track



#sys.exit(0)
if options.importToMongoDB:
    mongoImport(cacheDir)

    sys.exit(0)


#sys.exit(0)
if (options.list != None):
    witchList = options.list.lower()
    if (witchList == ""):
        witchList = "engines"

    if (witchList == "engines"):
        print("Available engines:")
        i = 0
        for engine in ENGINES:
            i += 1
            print("  %02d: %s" % (i, engine[0]))

        if (i == 1):
            print("\nThere is %d engine." % i)

        else:
            print("\nThere are %d engines." % i)

    else:
        print("ERROR: \"%s\" is an unknown list type." % witchList)

    sys.exit(0)


#sys.exit(0)
if options.searchInCache:
    query = {}

    regexInArtist = regexInTitle = False
    chars = set('.^$*+?{}[]\|()')
    try:
        regexInArtist = any((c in chars) for c in artist)

    except:
        pass

    try:
        regexInTitle = any((c in chars) for c in title)

    except:
        pass


    if (options.docId != ""):
        query["_id"] = bson.ObjectId(options.docId)

    else:
        if (title != None):
            if regexInTitle:
                query["title"] = {'$regex': unicode(title.strip(), 'utf-8')}

            else:
                query["title"] = unicode(title.strip(), 'utf-8')

        if (artist != None):
            if regexInArtist:
                query["artist"] = {'$regex': unicode(artist.strip(), 'utf-8')}

            else:
                query["artist"] = unicode(artist.strip(), 'utf-8')

    cursor = mongoDB_Lyrics.find(query).sort([('title', pymongo.ASCENDING), ('artist', pymongo.ASCENDING), ('album', pymongo.ASCENDING)])

    i = 0
    for doc in cursor:
        i += 1
        print("#%03d (%s): %-45s by \"%s\"" % (i, doc["_id"], doc["title"], doc["artist"]))

    if options.verbose:
        print("%s results found." % i)


    if OUTDATED_JSON_FILES:
        searchTerm = searchTermHuman = ""
        if (title != None):
            title = unicode(title.strip(), 'utf-8')
            searchTermHuman = "(title = \"%s\")" % title
            searchTerm += "\"title\": \".*%s.*\"" % title

        if (artist != None):
            artist = unicode(artist.strip(), 'utf-8')
            if searchTerm != "":
                searchTermHuman += " or "
                searchTerm +="|"

            searchTermHuman += "(artist = \"%s\")" % artist
            searchTerm += "\"artist\": \".*%s.*\"" % artist

        if (searchTerm != ""):
            if options.verbose:
                print("Searching for %s....\n" % searchTermHuman)

            command = "/usr/bin/grep -i -l \"%s\" %s" \
                            % (searchTerm.encode("unicode-escape").replace("\\", "\\\\\\").replace("\"", "\\\"").replace("|", "\\|"), \
                                cacheDir + "/*.json")
            #print(command)
            try:
                files = subprocess.check_output([command], shell=True).strip()
                files = files.split("\n")

                recordSet = []
                for element in files:
                    lyrics, artist, title, source, path = readCachedLyrics(element)
                    recordSet += [[title, artist, element]]

                resultSet = sorted(recordSet, key=lambda record: record[0])
                i = 0
                for item in resultSet:
                    i += 1
                    if options.verbose:
                        print("%02d: %-45s by \"%s\"\n    -s \"\" -t \"%s\" -a \"%s\"\n    \"%s\"\n" % (i, "\"" + item[0] + "\"", item[1], item[0], item[1], item[2]))

                    else:
                        print("%02d: %-45s by \"%s\"" % (i, "\"" + item[0] + "\"", item[1]))

                if options.verbose:
                    print("%s results found." % len(files))

            except:
                pass

    sys.exit(0)



# Si algo falla preprocessSearchData cierra el programa.
title, artist, albumArtist, album, track = preprocessSearchData(options.docId, title, artist, albumArtist, album, track)



if options.verbose:
    if (options.docId != ""):
        print("Track information: \"_id\"=" + options.docId)

    else:
        print("Track information: \"" + title.encode(sys.getfilesystemencoding()) + "\" by \"" + artist.encode(sys.getfilesystemencoding()) + "\", track #" + track.encode(sys.getfilesystemencoding()))



if (options.removeCache or options.overwrite):
    if mongoRemoveLyrics(options.docId, artist, title, albumArtist):
        print("Document was removed in MongoDB.")

    if OUTDATED_JSON_FILES:
        path = findSongPath(cacheDir, artist, title, albumArtist)
        if (path != None):
            os.remove(path)
            if not options.overwrite and options.verbose:
                print("File \"" + path + "\" has been deleted.")

        else:
            if not options.overwrite and options.verbose:
                print("Lyrics was not cached.")

    if options.removeCache:
        sys.exit(0)



if options.lyricsCached:
    doc = mongoSearch(options.docId, artist, title, albumArtist)
    if (doc != None):
        if options.verbose:
            print("Lyrics was cached in document with \"_id\": %s\n" % (doc["_id"]))

    else:
        if options.verbose:
            print("Lyrics was not in cache.")

    if OUTDATED_JSON_FILES:
        path = findSongPath(cacheDir, artist, title, albumArtist)
        if (path != None):
            if options.verbose:
                print("Lyrics was cached as:\n  file: %s\n   url: %s" % (os.path.basename(path), path))

        else:
            if options.verbose:
                print("Lyrics was not in file cache.")


elif options.instrumental:
    source = ""
    lyrics = "Instrumental"

    docId = cacheLyric(None, artist, title, source, lyrics)
    if options.verbose:
        print("--\nLyrics was cached in document with \"_id\": %s" % docId)


elif (options.deleteLyrics or options.editLyrics or options.kanaMode or options.romajiMode or options.romajaMode or (options.translateLang != None)):
    lyrics = ""
    lyricsKind = "lyrics"
    if options.kanaMode:
        lyricsKind = "kana"

    elif options.romajiMode:
        lyricsKind = "romaji"

    elif options.romajaMode:
        lyricsKind = "romaja"

    elif options.translateLang != None:
        if (options.translateLang == ""):
            options.translateLang = "en"

        lyricsKind = "lang_" + options.translateLang

    if options.deleteLyrics:
        if mongoRemoveLyrics(options.docId, artist, title, albumArtist, False):
            print("Lyrics was removed.")

        if OUTDATED_JSON_FILES:
            path = findSongPath(cacheDir, artist, title, albumArtist)
            if os.path.exists(path):
                fp = open(path, "r")
                try:
                    js = json.load(fp)
                    if lyricsKind in js:
                        fp.close()
                        fp = open(path, "w")
                        del js[lyricsKind]
                        json.dump(js, fp, indent = 4)
                        if options.verbose:
                            print("%s lyrics has been deleted from the lyrics cache." % lyricsKind)

                finally:
                    fp.close()

    else:
        #lyrics, artist, title, source, path = readCachedLyrics(cacheDir, artist, title, albumArtist, lyricsKind)
        docId, lyrics, artist, title, source = mongoRestoreLyrics(options.docId, artist, title, albumArtist, lyricsKind)
        if options.editLyrics:
            if ((lyrics == None) or (lyrics == "")):
                lyrics = ""
                if ((docId == None) or (docId == "")):
                    docId = cacheLyric(None, artist, title, source, lyrics, lyricsKind)

            #subprocess.call(["kioclient", "exec", path])
            dialogLabel = "Lyrics for \"%s\" by \"%s\"" % (title, artist)
            if (lyricsKind in ("kana", "romaji", "romaja")):
                dialogLabel += " [%s version]" % lyricsKind

            elif (lyricsKind[0:5] == "lang_"):
                dialogLabel += " [translated to \"%s\"]" % lyricsKind[5:]

            try:
                #lyrics = subprocess.check_output(["kdialog", "--title", "getLyrics", "--textinputbox", dialogLabel, lyrics]).strip()
                lyrics = subprocess.check_output([scriptsPath + "editor.py", lyrics, dialogLabel])
                if (lyrics != ""):
                    docId = cacheLyric(docId, artist, title, source, lyrics.strip(), lyricsKind)
                    if options.verbose:
                        print("Lyrics edited and updated.")

            except:
                print("Unexpected error:", sys.exc_info()[0])
                displayKDEInfo(sys.exc_info()[1].message, "Error")

        else:
            if (lyrics != None):
                if (lyrics != ""):
                    docId = cacheLyric(None, artist, title, source, lyrics, lyricsKind)

                if options.rawOutput:
                    mongoRawPrint(docId)

                else:
                    print(lyrics.encode(sys.getfilesystemencoding()))

            else:
                if options.verbose:
                    print("Lyrics was not in cache.")


else:
    lyrics = None
    path = None
    source = None
    lyricsInCache = False
    storage = ''
    lyricsKind = "lyrics"

    #if (not options.overwrite and cacheDir and os.path.exists(cacheDir)):
    if not options.overwrite:
        docId, lyrics, artist, title, source = mongoRestoreLyrics(options.docId, artist, title, albumArtist)
        if (lyrics == None):
            if OUTDATED_JSON_FILES:
                path = findSongPath(cacheDir, artist, title, albumArtist)
                if (path != None):
                    try:
                        fp = open(path)
                        try:
                            doc = json.load(fp)
                            lyrics = doc["lyrics"].strip()

                            docId = mongoStoreLyrics(doc)

                        finally:
                            fp.close()

                        if (docId != None):
                            os.rename(path, path + '.imported')

                        lyricsInCache = True

                    except:
                        pass

        else:
            lyricsInCache = True

    if (lyrics == None):
        # aquí llamar a la función.
        toSearch = []
        if (options.forcedEngines == None):
            enginesToUse = []

        else:
            enginesToUse = options.forcedEngines.strip().replace(" ", "").split(",")

        for engine in ENGINES:
            if ((enginesToUse != []) and not (engine[0] in enginesToUse)):
                continue

            if engine[2]:
                # Web engine.
                if (engine[1] == 1):
                    command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", %s)" % (artist, title, options.verbose)
                    toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, artist)]]
                    if (albumArtist != artist):
                        command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", %s)" % (albumArtist, title, options.verbose)
                        toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, albumArtist)]]

                elif (engine[2] == 2):
                    command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", u\"%s\", %s)" % (artist, album, track, title, options.verbose)
                    toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, artist)]]
                    if (albumArtist != artist):
                        command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", u\"%s\", %s)" % (albumArtist, album, track, title, options.verbose)
                        toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, albumArtist)]]

            else:
                # Filesystem engine.
                if (engine[1] == 1):
                    command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", %s)" % (params[engine[0] + 'Directory'], artist, title, options.verbose)
                    toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, artist)]]
                    if (albumArtist != artist):
                        command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", %s)" % (params[engine[0] + 'Directory'], albumArtist, title, options.verbose)
                        toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, albumArtist)]]

                elif (engine[2] == 2):
                    command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", u\"%s\", u\"%s\", %s)" % (params[engine[0] + 'Directory'], artist, album, track, title, options.verbose)
                    toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, artist)]]
                    if (albumArtist != artist):
                        command = u"" + engine[0] + ".getLyrics(u\"%s\", u\"%s\", u\"%s\", u\"%s\", u\"%s\", %s)" % (params[engine[0] + 'Directory'], albumArtist, album, track, title, options.verbose)
                        toSearch += [[command, engine[0], "\"%s\" by \"%s\"" % (title, albumArtist)]]

        q = Queue.Queue()
        for item in toSearch:
            if options.verbose:
                print("Searching in \"%s\": %s" % (item[1], item[2]))

            t = threading.Thread(target=searchLyrics, args=(q, item[0], item[1]))
            t.daemon = True
            t.start()

        count = 0
        lyrics = None
        while ((lyrics == None) and (count < len(toSearch))):
            count += 1
            result = q.get()
            lyrics = result[0]
            source = result[1]

    if ((lyrics != None) or options.verbose):
        if ((lyrics == None) or (lyrics == "")):
            if options.verbose:
                print("No lyrics found.")

            if options.autoEditWhenNoLyrics:
                lyricsKind = "lyrics"
                #lyrics, artist, title, source, path = readCachedLyrics(cacheDir, artist, title, albumArtist, lyricsKind)
                lyrics = ""
                docId = cacheLyric(docId, artist, title, source, lyrics, lyricsKind)
                lyricsInCache = True

                #subprocess.call(["kioclient", "exec", path])
                dialogLabel = "Lyrics for \"%s\" by \"%s\"" % (title, artist)
                if (lyricsKind in ("kana", "romaji", "romaja")):
                    dialogLabel += " [%s version]" % lyricsKind

                elif (lyricsKind[0:5] == "lang_"):
                    dialogLabel += " [translated to \"%s\"]" % lyricsKind[5:]

                try:
                    #lyrics = subprocess.check_output(["kdialog", "--title", "getLyrics", "--textinputbox", dialogLabel, lyrics]).strip()
                    lyrics = subprocess.check_output([scriptsPath + "editor.py", lyrics, dialogLabel])
                    if (lyrics != ""):
                        cacheLyric(docId, artist, title, source, lyrics.strip(), lyricsKind)
                        if options.verbose:
                            print("Lyrics edited and updated.")

                except:
                    pass

        else:
            if options.verbose:
                print("Lyrics found in %s." % source)

            if options.rawOutput:
                mongoRawPrint(options.docId)

            else:
                print(lyrics.encode(sys.getfilesystemencoding()))

    if not lyricsInCache and ((lyrics != None) or options.createEmptyCache):
        docId = cacheLyric(None, artist, title, source, lyrics, lyricsKind)
        if options.verbose:
            print("--\nLyrics was cached in \"%s\"." % docId)
