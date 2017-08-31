from pandas import read_excel, read_sql_query
from generator import *

# variables
NAMESPACE = 'HU.OMSZ.AQ'
CODE_COMB = 3
LOCALID = "HU_OMSZ_20161017"
PART = "B"

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


def get_pollutants_for_zone(con, zone_code):
    structure = read_structure(STRUCTURE_LOCATION.format(filename='pollutants.txt'))

    q = GET_POLLUTANT_QUERY.format(zn_code=zone_code)
    pollutant_df = read_sql_query(q, con)

    poll_to_replace = get_fields_to_replace(structure)

    pollutant_string = ''

    for index, row in pollutant_df.iterrows():
        pollutant_string += sub_all(poll_to_replace, row, structure) + '\n'

    pollutant_string = pollutant_string.rstrip()
    return pollutant_string


def modify_zones_df(zones_df):
    modified_df = read_excel('Zones_HU-001_mod.xls')
    for _, row in modified_df.iterrows():
        if row['change'] == 'M':
            idx = zones_df[zones_df['zn_code'] == row['zone_code']].index
            zones_df.set_value(idx, 'zn_startyear', row['start_year'])
            zones_df.set_value(idx, 'zn_type', row['zone_type'])
            zones_df.set_value(idx, 'zn_name', row['zone_name'])
            zones_df.set_value(idx, 'zn_area', row['zone_area (in km2)'])
            zones_df.set_value(idx, 'zn_population', row['zone_population'])
            zones_df.set_value(idx, 'zn_population_year', row['zone_population_year'])
            zones_df.set_value(idx, 'zn_geometry', row['zone_geometry_file'])
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
                             get_pollutants_for_zone(con, row['zn_code']), actual_zone)
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

    return xml


def main(drv, mdb):

    con = init_connection(drv, mdb)

    zones_df = read_sql_query(GET_ZONES_QUERY, con)
    zones_df = modify_zones_df(zones_df)
    responsible_df = read_sql_query(GET_RESPONSIBLE_QUERY, con)

    xml = create_xml_structure(con, responsible_df, zones_df)

    save_xml(xml)


if __name__ == '__main__':
    main("{Microsoft Access Driver (*.mdb, *.accdb)}", "C:\\olm.mdb")



