#!/usr/bin/env python3
import codecs, csv, gzip
"""Generate simple.csv.gz for FF and LG from .csv.gz dumps of raw libgen table"""

# LG: ID(7),MD5(32),Language(2889),Extension(104),Author(1000),Title(1044),Archive,Filename
# Sort: Language,Author,Title,Extension
rows = []
with gzip.open("output/lg_updated.csv.gz", "rt", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        rows.append((
            row["Language"][:45],
            row["Author"][:200],
            row["Title"][:1000],
            row["Extension"][:6],
            row["Series"][:200],
            row["ID"],
            row["MD5"].lower(),
        ))
rows.sort()
with gzip.open("output/lg_simple.csv.gz", "wt", encoding="utf-8") as f:
    writer = csv.writer(f, dialect="excel")
    writer.writerow(["Collection", "ID", "MD5", "Language", "Extension", "Author", "Title", "Series", "Archive", "ArchiveMember"])
    for row in rows:
        language, author, title, extension, series, id_, md5 = row
        group = (int(id_) // 1000) * 1000
        archive = "text/lg/{}.tar.xz".format(group)
        archive_member = "{}/{}.{}.txt".format(group, md5, extension)
        writer.writerow(["lg", id_, md5, language, extension, author, title, series, archive, archive_member])

# FF: ID(7),MD5(32),Language(45),Extension(6),Author(264),Title(1095),Series(167),Archive,ArchiveMember
# Sort: Language,Author,Title,Extension
rows = []
with gzip.open("output/ff_fiction.csv.gz", "rt", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        rows.append((
            row["Language"][:45],
            row["Author"][:200],
            row["Title"][:1000],
            row["Extension"][:6],
            row["Series"][:200],
            row["ID"],
            row["MD5"].lower(),
        ))
rows.sort()
with gzip.open("output/ff_simple.csv.gz", "wt", encoding="utf-8") as f:
    writer = csv.writer(f, dialect="excel")
    writer.writerow(["Collection", "ID", "MD5", "Language", "Extension", "Author", "Title", "Series", "Archive", "ArchiveMember"])
    for row in rows:
        language, author, title, extension, series, id_, md5 = row
        group = (int(id_) // 1000) * 1000
        archive = "text/ff/{}.tar.xz".format(group)
        archive_member = "{}/{}.txt".format(group, md5)
        writer.writerow(["ff", id_, md5, language, extension, author, title, series, archive, archive_member])
