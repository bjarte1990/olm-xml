from pandas import read_excel, read_sql_query
from generator import *
from time import strftime, gmtime
import re

# variables
NAMESPACE = 'HU.OMSZ.AQ'
CODE_COMB = 3
DATESTRING = strftime("%Y%m%d", gmtime())
LOCALID = "HU_OMSZ_" + DATESTRING
PART = "B"
YEAR = '2017'
#2016-10-06T11:35:06+01:00
DATESTRING_LONG = strftime('%Y-%m-%dT%H:%M:%S+01:00')


STRUCTURE_LOCATION = 'structures/b/{filename}'

ZONE_STRING = '\t\t\t<aqd:content xlink:href="' + NAMESPACE + '/{zone_name}"/>'

GET_RESPONSIBLE_QUERY = "SELECT * FROM (AQD_responsible_authority ra " \
                        "INNER JOIN person p on p.ps_code = ra.ps_code) " \
                        "INNER JOIN organization o on o.og_code = ra.og_code " \
                        "WHERE ra.nn_code_iso2 = 'hu' AND ra.ac_code_comb = {code_comb}". \
                        format(code_comb=CODE_COMB)

GET_POLLUTANT_QUERY = "SELECT * FROM AQD_zone_pollutant " \
                      "WHERE nn_code_iso2 = 'hu' " \
                      "AND zn_code = '{zn_code}'"

GET_POLLUTANT_CODES = "SELECT cp_caption, cp_number FROM component"

GET_ZONES_QUERY = "SELECT * FROM AQD_ZONE WHERE nn_code_iso2='hu';"


def get_zone_list(zones_df):
    zone_list = ''
    for index, row in zones_df.iterrows():
        zone_list += sub('\{zone_name\}', 'ZON-' + row['zn_code'], ZONE_STRING) + '\n'

    zone_list = zone_list.rstrip() #remove unnecessary \n
    return zone_list


def create_responsible_part(responsible_df, zones_df):
    structure = read_structure(STRUCTURE_LOCATION.format(filename='resp.txt'))
    # change basics
    structure = sub('\{localid\}', LOCALID, structure)
    structure = sub('\{part\}', PART, structure)
    resp_to_replace = get_fields_to_replace(structure, prefix='resp')

    responsible_string = ''

    for index, row in responsible_df.iterrows():
        actual_person = sub_all(resp_to_replace, row, structure)
        # todo hardcode
        actual_person = sub('\{zone_list\}', get_zone_list(zones_df), actual_person)
        responsible_string += actual_person

    return responsible_string


def get_pollutants_for_zone(con, row):
    structure = read_structure(STRUCTURE_LOCATION.format(filename='pollutants.txt'))

    pollutant_list = map(lambda x: x.split('-'), row['zone_pollutant'].split(';'))
    pollutant_string = '\n'.join(map(lambda x: re.sub('\{cp_number\}', x[0],
                                                      re.sub('\{pt_code\}', x[1],
                                                             structure)), pollutant_list))

    return pollutant_string.rstrip()


def read_zones_from_file():
    zones_df = read_excel('Zones_mod_%s.xls' % YEAR )
    columns = ['change', 'zn_code', 'zn_name', 'zn_startyear', 'end_year',
       'zn_type', 'zn_population', 'zn_population_year',
       'zn_area', 'zone_predecessor', 'zone_pollutant',
       'geometry_type', 'zn_geometry', 'LAU_codes',
       'zone_change_description', 'time_extension_type']
    zones_df.columns = columns

    return zones_df

def create_zones(con, zones_df, responsible_person):
    structure = read_structure(STRUCTURE_LOCATION.format(filename='zones.txt'))
    resp_to_replace = get_fields_to_replace(structure, prefix='resp')
    zone_to_replace = get_fields_to_replace(structure, prefix='zone')
    zones_string = ''

    for index, row in zones_df.iterrows():
        # first replace the responsible person
        actual_zone = sub_all(resp_to_replace, responsible_person, structure)
        # then replace zone data
        actual_zone = sub_all(zone_to_replace, row, actual_zone)
        # finally replace pollution
        actual_zone = sub('\{pollutants_list\}',
                             get_pollutants_for_zone(con, row), actual_zone)
        zones_string += actual_zone + '\n'

    zones_string = zones_string.rstrip()
    return zones_string


def create_xml_structure(con, responsible_df, zones_df):
    responsible = create_responsible_part(responsible_df, zones_df)
    # todo in case of more responsible....
    zones = create_zones(con, zones_df, responsible_df.iloc[0])
    header = read_structure(STRUCTURE_LOCATION.format(filename='header.txt'))

    xml = sub('\{responsible_xml_part\}', responsible, header)
    xml = sub('\{zones_xml_part\}', zones, xml)

    xml = sub('\{DATESTRING\}', DATESTRING, xml)
    xml = sub('\{DATESTRING_LONG\}', DATESTRING_LONG, xml)
    xml = sub('\{YEAR\}', YEAR, xml)

    return xml


def main(drv, mdb):

    con = init_connection(drv, mdb)

    zones_df = read_zones_from_file()
    responsible_df = read_sql_query(GET_RESPONSIBLE_QUERY, con)

    xml = create_xml_structure(con, responsible_df, zones_df)

    save_xml(xml, filename='REP_D-HU_OMSZ_%s_B-003.xml' % DATESTRING)


if __name__ == '__main__':
    main("{Microsoft Access Driver (*.mdb, *.accdb)}", "C:\\olm.mdb")



