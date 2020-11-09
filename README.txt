Generates metadata indexes for the library genesis project. To run:

1. Download required metadata (see below)
2. Run 'sh make.sh'. This will take around an hour the first time.
3. Everything is now available! Check the 'output' folder
  - Library genesis databases as CSV
    /output/ff_*.csv.gz
    /output/lgc_*.csv.gz
    /output/lg_*.csv.gz
  - Simplified CSV databases, suitable for human use
    /output/ff_simple.csv.gz
    /output/lg_simple.csv.gz
  - HTML search site. (allows search, gives download links) Entirely self-contained except the actual books. Very slow to load currently. 140s Chrome, 18s Firefox. However, fast search (100ms)
    /output/site
4. (Optional) If you have a local copy of libgen.txt (~500GB):
  - Edit python_server/server.py to point to correct locations of libgen.txt, and output/site
  - Run 'python python_server/server.py'
  - Access http://localhost:5000/ in your browser. Now you can search for books, and also read them.
5. (Optional) Delete source_data/torrent.csv.gz and output/torrent.csv.gz. Run 'make.sh' again--this will re-generate the magnet links in about a day.
6. If wanted, download all of libgen using torrents/IPFS, and modify search_libgen.js to add a link to your local version. Now the search site will point to your local version, and you can distribute the whole thing together.

Required data in source_data (download this first).

- All LG torrents. Put in source_data/torrents/lg.
  http://libgen.rs/repository_torrent/
- All FF torrents. Put in source_data/torrents/ff.
  http://libgen.rs/fiction/repository_torrent/
- Latest LG database.
  http://gen.lib.rus.ec/dbdumps/
- (optional) Latest full LG database. Improves CSV output.
  http://gen.lib.rus.ec/dbdumps/.
- Latest FF database.
  http://gen.lib.rus.ec/dbdumps/
- Latest IPFS LG hash loopup table
  /ipns/databases.libgen.eth/ipfs_science_hashes_2526.txt
  https://cloudflare-ipfs.com/ipns/databases.libgen.eth/ipfs_science_hashes_2526.txt
- Latest IPFS FF hash lookup table.
  /ipns/databases.libgen.eth/ipfs_fiction_hashes_no_extensions.txt
  https://cloudflare-ipfs.com/ipns/databases.libgen.eth/ipfs_fiction_hashes_no_extensions.txt
