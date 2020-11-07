import csv, gzip, os
from torrentool.api import Torrent

ff_torrents = set(os.listdir("source_data/torrents/ff"))
assert [name.startswith("f_") and name.endswith(".torrent") for name in ff_torrents]
ff_groups = set(int(name[2:-8]) for name in ff_torrents)
assert set("f_{}.torrent".format(ff_group) for ff_group in ff_groups) == ff_torrents
ff_range = range(min(ff_groups), max(ff_groups)+1000, 1000)
assert set(ff_range) == ff_groups, "Some ff torrents missing"
assert set("f_{}.torrent".format(ff_group) for ff_group in ff_range) == ff_torrents

LG_OVERRIDE = { 0: "r_000.torrent" }
LG_MISSING = (81000, 82000)
lg_torrents = set(os.listdir("source_data/torrents/lg"))
assert [name.startswith("r_") and name.endswith(".torrent") for name in lg_torrents]
lg_groups = set(int(name[2:-8]) for name in lg_torrents)
assert set(LG_OVERRIDE.get(lg_group, "r_{}.torrent".format(lg_group)) for lg_group in lg_groups) == lg_torrents
lg_range = [x for x in range(min(lg_groups), max(lg_groups)+1000, 1000) if x not in LG_MISSING]
assert set(lg_range) == lg_groups, "Some lg torrents missing"
assert set(LG_OVERRIDE.get(lg_group, "r_{}.torrent".format(lg_group)) for lg_group in lg_groups) == lg_torrents

with gzip.open("output/torrent.csv.gz", "wt") as f:
    writer = csv.writer(f, dialect='excel')
    writer.writerow(["collection", "group", "torrent", "infohash", "file_num", "md5"])
    for ff_group in ff_range:
        torrent = "f_{}.torrent".format(ff_group)
        t = Torrent.from_file("source_data/torrents/ff/" + torrent)
        for i, f in enumerate(t.files):
            md5 = f.name.split("/")[-1].split(".")[0]
            writer.writerow(["ff", ff_group, torrent, t.info_hash, i, md5])
    for lg_group in lg_range:
        torrent = LG_OVERRIDE.get(lg_group, "r_{}.torrent".format(lg_group))
        t = Torrent.from_file("source_data/torrents/lg/" + torrent)
        for i, f in enumerate(t.files):
            md5 = f.name.split("/")[-1].split(".")[0]
            writer.writerow(["lg", lg_group, torrent, t.info_hash, i, md5])
