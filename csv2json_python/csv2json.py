#!/usr/bin/env python3
"""
Outputs a searchable full-text index of the CSV, for use by a javascript search engine. The format is:
{
    data: {
        "title": [ one title for each book, in sequence ],
        "author": [ one author for each book, in sequence ],
        "ID": [ one id for each book, in sequence ],
        ... for each of: collection,id,md5,language,extension,author,title,series
    },
}
"""
import base64, codecs, collections, copy, csv, itertools, gzip, json, os, sys
WHITELIST = ["collection", "id", "md5", "ipfs_cid", "language", "extension", "filesize", "author", "title", "series", "year", "torrent_group", "torrent_file_num"]
FILTER_FIELDS = ["collection", "language", "extension"]
SEARCH_FIELDS = ["author", "title", "series"]
FIELD_DISPLAY = {
    "extension": "Format"
}
DISPLAY = {**{ x: x.title() for x in WHITELIST }, **{ "extension": "Format" }}
OPTIONS = {
    "filterFields": FILTER_FIELDS,
    "searchFields": SEARCH_FIELDS,
    "displayFields": WHITELIST,
    "filterFieldsVisible": { x:y for x,y in DISPLAY.items() if x in FILTER_FIELDS },
    "searchFieldsVisible": { x:y for x,y in DISPLAY.items() if x in SEARCH_FIELDS },
    "displayFieldsVisible": { x:x for x in WHITELIST },
    "filters": {},
    "filtersVisible": {
        "collection": {
            "lg": "Nonfiction",
            "ff": "Fiction",
        }
    },
}

if __name__ == "__main__":
    # Output order is: [FF (as read), LG (as read)]
    # The search result order is just the output order, which is a problem (shows only fiction if there are many results)
    with gzip.open("output/ff_fiction.csv.gz", "rt", encoding="utf-8") as ff:
        #rows = list(itertools.islice(csv.reader(ff), 1000)) # Small smaple data for quick load times and easy testing
        rows = list(csv.reader(ff))
        rows[1:].sort() # Sort by (collection, id)
        ff_data = {col[0].lower(): col[1:] for col in zip(*rows) if col[0].lower() in WHITELIST}
        ff_length = len(ff_data["id"])
        ff_data["filesize"] = [int(x) for x in ff_data["filesize"]]
        ff_data["collection"] = ["ff"]*ff_length
        assert all(len(ff_data[k]) == ff_length for k in WHITELIST if k in ff_data)
    with gzip.open("output/lgc_updated.csv.gz", "rt", encoding="utf-8") as lg:
        #rows = list(itertools.islice(csv.reader(lg), 1000)) # Small smaple data for quick load times and easy testing
        rows = list(csv.reader(lg))
        rows[1:].sort() # Sort by (collection, id)
        lg_data = {col[0].lower(): col[1:] for col in zip(*rows) if col[0].lower() in WHITELIST}
        lg_length = len(lg_data["id"])
        lg_data["filesize"] = [int(x) for x in lg_data["filesize"]]
        lg_data["collection"] = ["lg"]*lg_length
    assert(set(ff_data.keys()) == set(lg_data.keys()))
    data = {k: ff_data[k] + lg_data[k] for k in ff_data.keys()}
    data_length = ff_length + lg_length
    assert all(len(data[k]) == data_length for k in WHITELIST if k in data)

    # Add reverse lookup by (collection, md5) -> id for join with other tables
    data["md5"] = [x.lower() for x in data["md5"]]
    md5_lookup = collections.defaultdict(list)
    for i in range(data_length):
        md5_lookup[(data["collection"][i], data["md5"][i])].append(i)
    #print(collections.Counter(len(x) for x in md5_lookup.values()))

    # Add ipfs_cid column
    cids = {}
    if False and os.path.exists("output/lg_hashes.csv.gz"):
        with gzip.open("output/lg_hashes.csv.gz", "rt", encoding="utf-8") as lg_hashes:
            for row in csv.DictReader(lg_hashes):
                md5 = row["md5"].lower()
                for i in md5_lookup[("lg", md5)]:
                    cids[i] = row["ipfs_cid"]
    if os.path.exists("source_data/ipfs_science_hashes_2526.txt"):
        with open("source_data/ipfs_science_hashes_2526.txt", "r", encoding="utf-8") as lg_cid:
            for line in lg_cid:
                cid, md5 = line.split()
                assert md5 == md5.lower()
                for i in md5_lookup[("lg", md5)]:
                    assert i not in cids or cids[i] == cid
                    cids[i] = cid
    if os.path.exists("source_data/ipfs_fiction_hashes_no_extensions.txt"):
        with open("source_data/ipfs_fiction_hashes_no_extensions.txt", "r", encoding="utf-8") as ff_cid:
            for line in ff_cid:
                cid, md5 = line.split()
                assert md5 == md5.lower()
                for i in md5_lookup[("ff", md5)]:
                    assert i not in cids or cids[i] == cid
                    cids[i] = cid
    data["ipfs_cid"] = [cids.get(i, "") for i in range(data_length)]
    #print(collections.Counter(collections.Counter(data["ipfs_cid"]).values()))
    del cids

    # Add data.torrent_group, data.torrent_file_num, and corpus.infohash
    data["torrent_group"] = [""]*data_length
    data["torrent_file_num"] = [""]*data_length
    infohash = {}
    if os.path.exists("output/torrent.csv.gz"):
        with gzip.open("output/torrent.csv.gz", "rt", encoding="utf-8") as torrent_csv:
            for row in csv.DictReader(torrent_csv):
                ids = md5_lookup[(row["collection"], row["md5"])]
                for i in ids:
                    group, file_num = int(row["group"]), int(row["file_num"])
                    assert group % 1000 == 0
                    group = group / 1000
                    full_group = data["collection"][i][0] + str(group)
                    infohash[full_group] = row["infohash"]
                    data["torrent_group"][i] = group
                    data["torrent_file_num"][i] = file_num

    # Done building data
    assert all(k in data and len(data[k]) == data_length for k in WHITELIST)
    options = copy.deepcopy(OPTIONS)
    for f in FILTER_FIELDS:
        most_common = [x for x,count in collections.Counter(data[f]).most_common(8) if x.strip() != ""]
        options["filters"][f] = sorted(most_common)

    if False:
        t_orig, t_dedup, t_compressed = 0, 0, 0
        for f, d in data.items():
            orig, dedup = sum(2+len(x) for x in d), sum(2+len(x) for x in set(d))
            count = len(d)
            compressed = min((dedup + 4*count), orig)
            t_orig += orig
            t_dedup += dedup
            t_compressed += compressed
            print(f, orig//1000000, dedup//1000000, compressed//1000000, round(orig/compressed, 2), file=sys.stderr)
        print("total", t_orig//1000000, t_dedup//1000000, t_compressed//1000000, t_orig/t_compressed, file=sys.stderr)

    # Works in Chrome and Firefox. Putting in literal javascript object hangs Chrome tab.
    # Load time     Chrome      Firefox
    # FF            37s         6s
    # LG            120s        16s
    keys = [x for x in WHITELIST if x in data.keys()]
    with open("output/site/js/corpus.js", "w") as f:
        print("const corpus={{\"options\":{},\"data\":{{}}, \"infohash\":{}}};".format(json.dumps(options), json.dumps(infohash)), file=f)

    for i, key in enumerate(keys):
        d = data[key]
        json_data = json.dumps(d, separators=(",",":"))
        with open("output/site/js/corpus_{}.js".format(key), "w") as f:
            print("corpus.data['{key}'] = {str_data};".format(key=key, str_data=json.dumps(json_data)), file=f)
