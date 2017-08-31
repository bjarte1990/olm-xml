import sys
import pandas as pd
import math

from generator import *

NAMESPACE = 'HU.OMSZ.AQ'
STRUCTURE_PATH = 'structures/d/'

CONTENT_STRING = '<aqd:content xlink:href="' + NAMESPACE + '/{name}"/>\n'

NETWORK_QUERY = "SELECT network.nw_name as network_name, " \
                "organization.og_name as manager_organization_name, " \
                "network.nw_eu_code as network_code, organization.og_address as address, " \
                "organization.og_city as city, " \
                "organization.og_website_address as manager_organization_website_address, " \
                "organization.og_phone_number as manager_organization_phone_number, " \
                "network.nw_startdate as network_start_date, network.nw_enddate as network_end_date " \
                "FROM organization INNER JOIN " \
                "(network INNER JOIN network_function " \
                "ON network.nw_code = network_function.nw_code) " \
                "ON organization.og_code = network_function.og_code " \
                "WHERE network.nn_code_iso2='HU';"

def format_component_code(component_code):
    return ''.join(['0'] * (5 - len(str(component_code)))) + str(component_code)


def generate_process_feature(p):
    structure = read_structure('process.txt')
    structure = sub('\{NAMESPACE\}', NAMESPACE, structure)

    if p['method_type'] == 'active':
        method_structure = read_structure('sampling_method.txt')
        method_structure = sub('\{method\}', 'other', method_structure)
        method_structure = sub('\{other_method\}', 'UNKNOWN', method_structure)
    else:
        method_structure = read_structure('measurement_method.txt')
    structure = sub('\{sampling_method\}', method_structure, structure)

    # fix fields
    other_equipment_string_flag = False
    if isinstance(p['equipmentcode'], int):
        structure = sub('\{process.equipmentcode\}', 'other', structure)
        structure = sub('\{other_equipment_part\}', '<aqd:otherEquipment>"' + p['equipmentname'] +
                           '"</aqd:otherEquipment>', structure)
        other_equipment_string_flag = True
    else:
        structure = sub('\{other_equipment_part\}', '<aqd:otherEquipment/>', structure)
    if isinstance(p['techniquecode'], int):
        structure = sub('\{process.techniquecode\}', 'other', structure)
        # active eseten nincs ilyen
        if p['method_type'] == 'active':
            structure = sub('\{other_first_tag\}', '<aqd:otherAnalyticalTechnique>"' + p['techniquename'] +
                               '"</aqd:otherAnalyticalTechnique>', structure)
        else:
            structure = sub('\{other_first_tag\}', '<aqd:otherMeasurementMethod>"' + p['techniquename'] +
                               '"</aqd:otherMeasurementMethod>', structure)
    else:
        if p['method_type'] == 'active':
            if other_equipment_string_flag:
                structure = sub('\{other_first_tag\}', '<aqd:otherAnalyticalTechnique>"'
                                                          '"</aqd:otherAnalyticalTechnique>', structure)
            else:
                structure = sub('\{other_first_tag\}', '<aqd:otherAnalyticalTechnique/>', structure)
        else:
            structure = sub('\{other_first_tag\}', '<aqd:otherMeasurementMethod/>', structure)

    fields = get_fields_to_replace(structure, 'process')

    structure = sub_all(fields, p, structure)
    return structure


def generate_network_feature(n, fromdb=False):
    structure = read_structure(STRUCTURE_PATH + 'network.txt')
    structure = sub('\{NAMESPACE\}', NAMESPACE, structure)
    if fromdb:
        structure = sub('\{address1\}', n['address'], structure)
        structure = sub('\{address2\}', n['city'], structure)
    else:
        structure = sub('\{address1\}', ' '.join(n['manager_organization_address'].split()[:2]), structure)
        structure = sub('\{address2\}', n['manager_organization_address'].split()[1], structure)
        n['network_start_date'] = str(n['network_start_date'])[:4] + '-' + \
                                  str(n['network_start_date'])[4:6] + '-' + \
                                  str(n['network_start_date'])[6:]
        if not isinstance(n['network_end_date'], float):
            n['network_end_date'] = str(n['network_end_date'])[:4] + '-' + \
                                      str(n['network_end_date'])[4:6] + '-' + \
                                      str(n['network_end_date'])[6:]

    if isinstance(n['network_end_date'], float):
        structure = sub('\{endposition\}',
                           '<gml:endPosition indeterminatePosition="unknown"/>', structure)
    else:
        structure = sub('\{endposition\}', '<gml:beginPosition>'
                                              '{network.network_end_date}T00:00:00+01:00'
                                              '</gml:beginPosition>', structure)

    fields = get_fields_to_replace(structure, 'network')
    structure = sub_all(fields, n, structure)

    return structure


def generate_station_feature(s):
    structure = read_structure(STRUCTURE_PATH + 'station.txt')
    structure = sub('\{NAMESPACE\}', NAMESPACE, structure)
    structure = sub('\{date\}', str(s['station_start_date'])[:4] + "-" + str(s['station_start_date'])[4:6] + '-' +
                       str(s['station_start_date'])[6:], structure)
    fields = get_fields_to_replace(structure, 'station')
    structure = sub_all(fields, s, structure)

    return structure


def generate_sampling_point_feature(sp):
    structure = read_structure(STRUCTURE_PATH + 'sampling_point.txt')
    #stored as double
    if math.isnan(sp['oc_id']):
        sp['oc_id'] = int(sp['oc_id_new'])
    else:
        sp['oc_id'] = int(sp['oc_id'])
    component_code = format_component_code(sp['component_code'])
    structure = sub('\{NAMESPACE\}', NAMESPACE, structure)
    structure = sub('\{component_code\}', component_code, structure)

    structure = sub('\{spo_start_date\}', str(sp['spo_startdate'])[:4] + "-" + str(sp['spo_startdate'])[4:6] + '-' +
                       str(sp['spo_startdate'])[6:], structure)
    #structure = re.sub('\{oc_start_date\}', str(sp['oc_startdate'])[:4] + "-" + str(sp['oc_startdate'])[4:6] + '-' +
    #                   str(sp['oc_startdate'])[6:], structure)

    fields = get_fields_to_replace(structure, 'sp')
    structure = sub_all(fields, sp, structure)

    return structure


def generate_sampling_point_f_feature(spf):
    structure = read_structure(STRUCTURE_PATH + 'sampling_point_f.txt')
    # stored as double
    if math.isnan(spf['oc_id']):
        spf['oc_id'] = int(spf['oc_id_new'])
    else:
        spf['oc_id'] = int(spf['oc_id'])
    component_code = format_component_code(spf['component_code'])
    structure = sub('\{NAMESPACE\}', NAMESPACE, structure)
    structure = sub('\{component_code\}', component_code, structure)

    fields = get_fields_to_replace(structure, 'spf')
    structure = sub_all(fields, spf, structure)

    return structure


def generate_contents(con):
    content_string = '{processes}\n{networks}\n{stations}\n{sampling_points}'
    process_list = ''
    process_features = ''

    network_list = ''
    network_features = ''

    station_list = ''
    station_features = ''

    sampling_point_list = ''
    sampling_point_f_list = ''
    sampling_point_features = ''
    sampling_point_f_features = ''
    process_df = pd.read_excel('AQIS_HU_Process-001_modA.xls')

    network_db_df = pd.read_sql_query(NETWORK_QUERY, con)
    network_db_df['manager_person_last_name'] = 'unknown'
    network_db_df['manager_person_first_name'] = 'unknown'
    network_db_df['manager_person_email_address'] = ''
    network_db_df['network_type'] = ''
    network_file_df = pd.read_excel('AQIS_HU_Network-001_mod.xls')
    network_file_df = network_file_df.sort_values('network_code')
    # drop those from db df which are in file df
    network_db_df = network_db_df[~network_db_df['network_code'].isin(network_file_df['network_code'])]

    station_df = pd.read_excel('AQIS_HU_Station-001_mod.xls')

    sampling_point_df = pd.read_excel('AQIS_HU_SamplingPoint-001_mod.xls')

    # generate processes
    for index, row in process_df.iterrows():
        process_list += CONTENT_STRING.format(name=row['process_id'])
        process_features += generate_process_feature(row)

    #todo: generate networks & stations (using db)
    for index, row in network_db_df.iterrows():
        name = 'NET-' + row['network_code']
        network_list += CONTENT_STRING.format(name=name)
        network_features += generate_network_feature(row, fromdb=True)

    for index, row in network_file_df.iterrows():
        name = 'NET-' + row['network_code']
        network_list += CONTENT_STRING.format(name=name)
        network_features += generate_network_feature(row)

    print(network_list)
    print(network_features)

    for index, row in station_df.iterrows():
        name = 'STA-' + row['station_eoi_code']
        station_list += CONTENT_STRING.format(name=name)
        station_features += generate_station_feature(row)

    # generate sampling_points
    for index, row in sampling_point_df.merge(station_df, on='station_eoi_code').iterrows():
        sp_part = row['station_eoi_code'] + '_' + format_component_code(row['component_code']) + \
               '_' + str(row['spo_id'])
        name = 'SPO-' + sp_part
        #todo check if it is okay
        name_f = 'SPO_F-' + sp_part + '_' + str(row['oc_id'])
        sampling_point_list += CONTENT_STRING.format(name=name)
        sampling_point_f_list += CONTENT_STRING.format(name=name_f)
        sampling_point_features += generate_sampling_point_feature(row)
        sampling_point_f_features += generate_sampling_point_f_feature(row)

    print(sampling_point_features)
    print(sampling_point_f_features)


def main(drv, mdb):
    con = init_connection(drv, mdb)
    generate_contents(con)

if __name__ == '__main__':
    main("{Microsoft Access Driver (*.mdb, *.accdb)}", "C:\\olm.mdb")
