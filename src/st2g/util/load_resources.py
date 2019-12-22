import os
import pkg_resources
import configparser
from functools import reduce

def load_ini():
    config = configparser.ConfigParser()
    fpath = reduce(os.path.join, ['rules', 'patterns.ini'])
    with pkg_resources.resource_stream("st2g", fpath) as fin:
        binary_config = fin.read()
    config.read_string(binary_config.decode("UTF-8"))
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
            ind_defang = config.get(ind_type, 'defang')  # defang is for dot replacement? need check later
        except:
            continue
        if ind_defang:
            defang[ind_type] = True
    # convert to spacy pattern format
    ret = []
    # add additional entities
    ret.append({'label': "Pronoun", 'pattern': [{"POS": "PRON", "IS_ALPHA": True}]})
    for k, v in patterns.items():
        cur = {'label': k, 'pattern': [{"TEXT": {"REGEX": v}}]}
        ret.append(cur)
    return ret

def load_operations():
    fpath = reduce(os.path.join, ['rules', 'operations.cfg'])
    with pkg_resources.resource_stream("st2g", fpath) as fin:
        operations = fin.readlines()
    return [_.decode("UTF-8").strip() for _ in operations if len(_.strip())]
