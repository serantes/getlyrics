getlyrics
=========

A python script to fetch lyrics from several sources. Currently supported engines are:
- lrc             -- lrcShow-X cache, 
- lyricsworkshop  -- Lyrics Workshop Amarok 2 plugin cache.
- ttplayer        -- http://ttplayer.qianqian.com/
- lyricwiki       -- http://lyrics.wikia.com/
- chartlyrics     -- http://www.chartlyrics.com/


This is the help:

Usage: getlyrics.py [options]

Options:
  -h, --help            show this help message and exit
  --engines=TEXT        comma separated engines to use
  --kana                kana conversion
  --list=TEXT           list TEXT: engines
  --romaji              rōmaji conversion
  --romaja              romaja conversion
  --search              searchs in cache, needs --title or --artist parameters
  --translate=TEXT      translation language: en, es, ja, ko, etc.
  -l TEXT, --album=TEXT
                        album title
  -b TEXT, --albumartist=TEXT
                        album artist name
  -a TEXT, --artist=TEXT
                        artist name
  -c DIR, --cachedir=DIR
                        cache directory
  -p, --createemptycache
                        creates a cache file without lyrics
  -d, --delete          delete lyrics from cache
  -e, --edit            edit cached lyrics with default editor
  -s TEXT, --host=TEXT  [pwd@]host[:port], defaults "localhost"
  -i, --instrumental    creates a cache file with the word "Instrumental" instead of the lyrics
  -y, --lyricscached    check if lyrics was cached
  -o, --overwrite       overwrite lyrics in cache
  -q, --quiet           don't print aditional data to stdout
  -r, --removecache     delete cached song
  -t TEXT, --title=TEXT
                        song title
  -k NUMBER, --track=NUMBER
                        track number
