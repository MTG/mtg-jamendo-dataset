import os
import errno
import time
import datetime
import json


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def stats(done, total, starttime):
    nowtime = time.time()
    position = done*1.0 / total
    duration = round(nowtime - starttime)
    durdelta = datetime.timedelta(seconds=duration)
    remaining = round((duration / position) - duration)
    remdelta = datetime.timedelta(seconds=remaining)

    return str(durdelta), str(remdelta)


def guess_csv_delimiter(data):
    """ Simple method to guess the delimiter of a CSV file (, or \t).
        The csv.Sniffer class expects that all rows have the same
        number of fields which is not the case in our data.
        Instead, just count the number of times each delimiter occurs
        and return the one with the highest count"""

    TAB = "\t"
    COMMA = ","

    tabcount = data.count(TAB)
    commacount = data.count(COMMA)
    if tabcount > commacount:
        return TAB
    else:
        return COMMA


def read_json(json_file):
    with open(json_file) as fp:
        return json.load(fp)
