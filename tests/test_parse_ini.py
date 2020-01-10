import os
import pytest
from functools import reduce


def test_parse_ini():
    # copied & modified from https://github.com/armbues/ioc_parser/blob/master/iocp/Parser.py
    import configparser, re
    config = configparser.ConfigParser()
    fpath = reduce(os.path.join, ['.', 'src', 'st2g', 'rules', 'patterns.ini'])
    config.read(fpath)
    patterns, defang = {}, {}
    for ind_type in config.sections():
        try:
            ind_pattern = config.get(ind_type, 'pattern')
        except:
            continue
        if ind_pattern:
            # ind_regex = re.compile(ind_pattern)
            patterns[ind_type] = ind_pattern
        try:
            ind_defang = config.get(ind_type, 'defang')
        except:
            continue
        if ind_defang:
            defang[ind_type] = True
    # return patterns, defang
    from pprint import pprint
    pprint(patterns)
    pprint(defang)
