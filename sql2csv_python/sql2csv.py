#!/usr/bin/env python3
"""sql2csv.py: Converts one simple MySQL DB dump into equivalent CSV files, one per table.

Usage:
    cat fiction.sql | sql2csv.py - fiction:fiction.csv
    sql2csv.py fiction.sql fiction:fiction.csv
        Reads 'fiction.sql', and outputs the 'fiction' table to the file 'fiction.csv'
    sql2csv.py fiction.sql fiction:fiction.csv fiction_hashes.csv
        Reads 'fiction.sql', and outputs the 'fiction' table to the file 'fiction.csv', the 'fiction_hashes' table to 'fiction_hashes.csv'
    sql2csv.py fiction.sql %:%.csv
        Reads 'fiction.sql', and outputs each table to an output file according to the template given. If the two tables are 'fiction' and 'fiction_hashes', this outputs the 'fiction' table to the file 'fiction.csv', the 'fiction_hashes' table to 'fiction_hashes.csv'

Known limitation: The input SQL dump must be valid UTF8. The output will have any null bytes stripped, even though null bytes are valid UTF8.
"""

import ast, csv, gzip, os, re, sys
WILDCARD = "%"

def entry_regex(cols, capture):
    number = r"""\d+"""
    string = r"""'(?:[^']|\\')*'"""
    null = r"""NULL"""
    if capture:
        field = "({})".format("|".join([number, string, null]))
    else:
        field = "(?:{})".format("|".join([number, string, null]))
    return r'''\({}\)'''.format(",".join([field]*len(cols)))
def line_regex(table, cols):
    fields = entry_regex(cols, capture=False)
    col_names = r'''\({}\)'''.format(", ".join("`{}`".format(colname) for colname in cols))
    return "INSERT INTO `{}` {} VALUES ({}(?:,{})*);".format(table, col_names, fields, fields)

def process_db_definitions():
    line = yield
    definition = False
    while True:
        if line.startswith("CREATE TABLE"):
            table_name, cols, definition = line.split("`")[1], [], True
            line = yield
        elif definition and line.strip().startswith("`"):
            col = line.split("`")[1]
            cols.append(col)
            line = yield
        elif definition and not line.startswith(" "):
            line = yield (table_name, cols)
            table_name, cols, definition = None, None, False
        else:
            line = yield
def parse_sql_value(x):
    if x == "NULL":
        return None
    else:
        x = ast.literal_eval(x)
        if not isinstance(x, str):
            return x
        return x.replace('\x00','')

def process_table_rows(table_name, cols):
    rows = []
    line = yield []
    ENTRY_REGEX = re.compile(entry_regex(cols, capture=True))
    INSERT_LINE_REGEX = re.compile(line_regex(table_name, cols))
    while True:
        rows = []
        if line.startswith("INSERT INTO `{}`".format(table_name)):
            m = INSERT_LINE_REGEX.fullmatch(line.rstrip("\n"))
            assert m
            if m:
                try:
                    rows = [[parse_sql_value(x) for x in entry.groups()] for entry in ENTRY_REGEX.finditer(m.group(1))]
                except SyntaxError:
                    rows = []
        line = yield rows

if __name__ == "__main__":
    if not (len(sys.argv) >=3 and all(2 == len(arg.split(":")) for arg in sys.argv[2:])):
        print(__doc__)
        sys.exit(1)
    filepath = sys.argv[1]
    filename = os.path.basename(filepath)
    if filepath == "-":
        f = sys.stdin
    elif filename.endswith(".sql"):
        f = open(filepath, "r")
    elif filename.endswith(".sql.gz"):
        f = gzip.open(filepath, "rt", encoding="utf-8")
    else:
        raise Exception("Unexpected file format. Should be stdin or .sql")

    csv_mapping = {}
    template = None
    for arg in sys.argv[2:]:
        from_, to = arg.split(":")
        if from_ == WILDCARD:
            if template is not None:
                raise Exception("Two wildcard formats ({}) ({}) were given. Only one may be given.".format(template, to))
            elif template is None and len(csv_mapping) > 0:
                raise Exception("Wildcard ({}) and non-wildcard ({}) format both given. If a wildcard format is given, it should be the only format.".format(template, argv[2]))
            elif template is None and len(csv_mapping) == 0:
                template = to
        elif template is not None:
            raise Exception("Wildcard ({}) and non-wildcard ({}) format both given. If a wildcard format is given, it should be the only format.".format(template, arg))
        else:
            if from_ in csv_mapping:
                raise Exception("Same database cannot be used twice: {}".format(from_))
            elif to in csv_mapping.values():
                raise Exception("Same output file cannot be used twice: {}".format(to))
            else:
                csv_mapping[from_] = to

    processing = {}
    parse_db = process_db_definitions(); next(parse_db)
    for line in f:
        new_db = parse_db.send(line)
        if new_db is not None:
            table_name, cols = new_db
            if table_name not in csv_mapping and template is not None:
                csv_mapping[table_name] = template.replace(WILDCARD, table_name)
            if table_name in csv_mapping:
                print("Outputting table:", table_name, csv_mapping[table_name], cols, file=sys.stderr)
                if csv_mapping[table_name] == "-":
                    csv_file = sys.stdout
                elif csv_mapping[table_name].endswith(".gz"):
                    csv_file = gzip.open(csv_mapping[table_name], "wt", encoding="utf-8")
                else:
                    csv_file = open(csv_mapping[table_name], "w")
                csv_writer = csv.writer(csv_file, dialect="excel")
                csv_writer.writerow(cols) # Column header row with names
                processor = process_table_rows(table_name, cols)
                next(processor)
                processing[table_name] = processor, csv_writer
            else:
                print("Skipping table:", table_name, cols, file=sys.stderr)
        for processor, csv_writer in processing.values():
            rows = processor.send(line)
            csv_writer.writerows(rows)
