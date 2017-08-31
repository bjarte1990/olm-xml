from io import open
from re import sub, findall, match
from pyodbc import connect


def init_connection(drv, mdb):

    conn_str = 'DRIVER={driver};DBQ={mdb_location}'
    return connect(conn_str.format(driver=drv, mdb_location=mdb))


def save_xml(xml, filename='B.xml'):
    f = open(filename, 'w+', encoding="utf-8")
    f.write(xml)
    f.close()


def sub_all(from_list, to_df, text):
    for r in from_list:
        if '.' in r:
            column = r.split('.')[1]
        else:
            column = r
        text = sub('\{' + r + '\}', str(to_df[column]), text)
    return text


def get_fields_to_replace(text, prefix=''):
    return set(filter(lambda x: x.startswith(prefix), findall('\{([^\}]*)\}', text)))


def read_structure(filename):
    fhand = open(filename)
    structure = fhand.read()
    fhand.close()
    return structure
