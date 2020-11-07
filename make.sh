#!/bin/sh
check_prog() {
    which "$1" >/dev/null 2>/dev/null
}

assert_prog() {
    check_prog "$1" || {
        echo "$2" >&2
        exit 1
    }
}

extract_sql() {
    # Usage: RAR_FILE ARCHIVE_MEMBER
    # Extracts one (normally, the only) file from the rar, and makes sure it is valid UTF8. Outputs to stdout
    assert_prog unrar "Please install unrar to extract $1"
    echo "Extracting $2..." >&2
    unrar p -inul "$1" "$2"
}

validate_utf8() {
    if check_prog uconv; then
        uconv --to-code utf8 --from-code utf8 --callback skip
    else
        assert_prog iconv "Please install iconv or uconv to extract $2 from $1"
        iconv -f utf8 -c -o /dev/stdout # will die on libgen.rar due to memory
    fi
}

##########
# make.sh
##########
#
# See README.txt for required metadata files in source_data
# Note that this does not currently notice updated source data--delete the output to re-generate anything
#
# Generates
#   1) CSV databases containing the same information as the official libgen MySQL database dumps
#   2) a simplified CSV index, containing only the most useful fields, for each of the two major datasets (ff and lg)
#   3) a static HTML and javascript site, which can be used to search for books, and provides links to download each (book content not included in search site).
#      note that currently, this site is slow to load (15s firefox, 60s chrome) but relatively fast to search. it is probably too large to be served from the web, but is good for LAN, IPFS, or local search

# full csv databases: ff_fiction.csv.gz ff_fiction_description.csv.gz  ff_fiction_hashes.csv.gz
fiction_rar=`find source_data -iname 'fiction*.rar' | sort -r | head -n1`
[ -s output/ff_fiction.csv.gz ] || {
    [ -z "$fiction_rar" ] && {
        echo "Download source_data/fiction.rar and run again"
        exit 1
    }
    assert_prog python3 "Python3 is required for make.sh"
    mkdir -p output
    set -x
    extract_sql "${fiction_rar}" fiction.sql | validate_utf8 | python3 sql2csv_python/sql2csv.py - %:output/ff_%.csv.gz
}
# full csv databases: lgc_topics.csv.gz  lgc_updated.csv.gz
libgen_compact_rar=`find source_data -iname 'libgen_compact*.rar' | sort -r | head -n1`
[ -s output/lgc_updated.csv.gz ] || {
    [ -z "$libgen_compact_rar" ] && {
        echo "Download source_data/libgen_compact.rar and run again"
        exit 1
    }
    assert_prog python3 "Python3 is required for make.sh"
    mkdir -p output
    extract_sql "${libgen_compact_rar}" libgen_compact.sql | validate_utf8 | python3 sql2csv_python/sql2csv.py - %:output/lgc_%.csv.gz
}
# (optional) full csv databases: lg_description.csv.gz lg_description_edited.csv.gz lg_hashes.csv.gz lg_topics.csv.gz lg_updated.csv.gz lg_updated_edited.csv.gz
libgen_rar=`find source_data -iname 'libgen*.rar' -and -not -iname 'libgen_compact*' | sort -r | head -n1`
[ -e "${libgen_rar}" -a \! -s output/lg_updated.csv.gz ] && {
    assert_prog python3 "Python3 is required for make.sh"
    mkdir -p output
    extract_sql "${libgen_rar}" libgen.sql | validate_utf8 | python3 sql2csv_python/sql2csv.py - %:output/lg_%.csv.gz
}

# Generate torrent index
[ -s output/torrent.csv.gz ] || {
    if [ -s source_file/torrent.csv.gz ]; then
        cp source_file/torrent.csv.gz output/torrent.csv.gz
    else
        assert_prog python3 "Python3 is required for make.sh"
        # TODO: add and check requirements.txt
        python3 csv2json_python/torrent2csv.py # 10h runtime, so we package this as a source file even though it can be generated from metadata
    fi
}

# simplified csv indexes: ff_simple.csv.gz lg_simple.csv.gz
[ -s output/ff_simple.csv.gz ] || {
    assert_prog python3 "Python3 is required for make.sh"
    python3 libgenindex_python/simple.py
}

# generate the search site
#[ -s output/html/index.html ] || {
    cp -r static -T output/site
#}
[ -s output/site/js/corpus.js ] || {
    python3 csv2json_python/csv2json.py
}

