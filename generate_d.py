import pandas as pd
import math
from time import strftime, gmtime

from generator import *

NAMESPACE = 'HU.OMSZ.AQ'
STRUCTURE_PATH = 'structures/d/'
STRUCTURE_LOCATION = 'structures/d/{filename}'

YEAR = "2016"
DATESTRING = strftime("%Y%m%d", gmtime())
LOCALID = "HU_OMSZ_" + DATESTRING
PART = "D"

CONTENT_STRING = '\t\t\t<aqd:content xlink:href="' + NAMESPACE + '/{name}"/>\n'

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

GET_RESPONSIBLE_QUERY = "SELECT * FROM (AQD_responsible_authority ra " \
                        "INNER JOIN person p on p.ps_code = ra.ps_code) " \
                        "INNER JOIN organization o on o.og_code = ra.og_code " \
                        "WHERE ra.nn_code_iso2 = 'hu' AND ra.ac_code_comb = {code_comb}"

CODE_COMB = 3


def format_component_code(component_code):
    return ''.join(['0'] * (5 - len(str(component_code)))) + str(component_code)


def generate_process_feature(p):
    structure = read_structure('process.txt')
    structure = sub('\{NAMESPACE\}', NAMESPACE, structure)

    if p['method_type'] == 'active':
        method_structure = read_structure('sampling_method.txt')
        method_structure = sub('\{method\}', 'other', method_structure)
        # todo is it okay?
        # method_structure = sub('\{other_method\}', 'UNKNOWN', method_structure)
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
        n['network_start_date'] = str(n['network_start_date']).split()[0]
        n['network_end_date'] = str(n['network_end_date']).split()[0]
    else:
        structure = sub('\{address1\}', ' '.join(n['manager_organization_address'].split()[:2]), structure)
        structure = sub('\{address2\}', n['manager_organization_address'].split()[1], structure)
        n['network_start_date'] = str(n['network_start_date'])[:4] + '-' + \
                                  str(n['network_start_date'])[4:6] + '-' + \
                                  str(n['network_start_date'])[6:8]
        if not isinstance(n['network_end_date'], float):
            n['network_end_date'] = str(n['network_end_date'])[:4] + '-' + \
                                      str(n['network_end_date'])[4:6] + '-' + \
                                      str(n['network_end_date'])[6:8]

    if isinstance(n['network_end_date'], float):
        structure = sub('\{endposition\}',
                           '<gml:endPosition indeterminatePosition="unknown"/>', structure)
    else:
        structure = sub('\{endposition\}', '<gml:endPosition>'
                                              '{network.network_end_date}T00:00:00+01:00'
                                              '</gml:endPosition>', structure)

    fields = get_fields_to_replace(structure, 'network')
    structure = sub_all(fields, n, structure)

    return structure


def generate_station_feature(s):
    structure = read_structure(STRUCTURE_PATH + 'station.txt')
    structure = sub('\{NAMESPACE\}', NAMESPACE, structure)
    structure = sub('\{date\}', str(s['station_start_date'])[:4] + "-" + str(s['station_start_date'])[4:6] + '-' +
                       str(s['station_start_date'])[6:8], structure)
    print(s['station_eoi_code'])
    if math.isnan(s['station_end_date']):
        structure = sub('\{end_date\}', ' indeterminatePosition = "unknown" /', structure)
    else:
        print(str(s['station_end_date']))
        structure = sub('\{end_date\}', '>' + str(s['station_end_date'])[:4] + "-"
                        + str(s['station_end_date'])[4:6] + '-'
                        + str(s['station_end_date'])[6:8]
                        + 'T00:00:00+01:00</gml:endPosition', structure)
    meteoparams_list = ''
    try:
        parameters = s['meteorological_parameters'].split(',')
    except:
        parameters = [str(s['meteorological_parameters'])]
    for met_par in parameters:
        meteoparams_list += '\t\t\t<aqd:meteoParams xlink:href="http://dd.eionet.europa.eu/vocabulary/' \
                  'aq/meteoparameter/{met_par}"/>\n'.format(met_par=met_par)

    structure = sub('\{meteoparams\}', meteoparams_list.rstrip(), structure)
    fields = get_fields_to_replace(structure, 'station')
    structure = sub_all(fields, s, structure)

    return structure


def generate_observings(sp,full):
    structure = read_structure(STRUCTURE_PATH + 'observing.txt')
    observing_string = ''

    current = full.loc[(full['station_eoi_code'] == sp['station_eoi_code'])
                   & (full['component_code'] == sp['component_code'])
                   & (full['spo_id'] == sp['spo_id'])
                   #& (full['oc_id'] == sp['oc_id'])
                    ]

    for i, row in current.iterrows():
        print(row)
        if math.isnan(row['oc_id']):
            row['oc_id'] = int(row['oc_id_new'])
        else:
            row['oc_id'] = int(row['oc_id'])

        current_structure = read_structure(STRUCTURE_PATH + 'observing.txt')
        long_component_code = format_component_code(row['component_code'])
        current_structure = sub('\{long_component_code\}', long_component_code,
                                current_structure)
        current_structure = sub('\{spo_start_date\}',
                        str(sp['spo_startdate'])[:4] + "-" + str(sp['spo_startdate'])[
                                                             4:6] + '-' +
                        str(sp['spo_startdate'])[6:8], current_structure)
        fields = get_fields_to_replace(current_structure)
        current_structure = sub_all(fields, row, current_structure) + '\n'
        observing_string += current_structure

    return observing_string.rstrip()

def generate_sampling_point_feature(sp, full):
    structure = read_structure(STRUCTURE_PATH + 'sampling_point.txt')

    observings = generate_observings(sp, full)
    structure = sub('\{observing\}', observings, structure)
    #stored as double
    if math.isnan(sp['oc_id']):
        sp['oc_id'] = int(sp['oc_id_new'])
    else:
        sp['oc_id'] = int(sp['oc_id'])
    component_code = format_component_code(sp['component_code'])
    structure = sub('\{NAMESPACE\}', NAMESPACE, structure)
    structure = sub('\{component_code\}', component_code, structure)

    structure = sub('\{spo_start_date\}', str(sp['spo_startdate'])[:4] + "-" + str(sp['spo_startdate'])[4:6] + '-' +
                       str(sp['spo_startdate'])[6:8], structure)
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
    if math.isnan(spf['station_distance_from_kerb']):
        spf['station_distance_from_kerb'] = 0
    if math.isnan(spf['station_distance_to_junction']):
        spf['station_distance_to_junction'] = 0
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
    print(network_db_df)
    station_df = pd.read_excel('AQIS_HU_Station-001_mod_s_add.xls')

    #sampling_point_df = pd.read_excel('AQIS_HU_SamplingPoint-003_2016_mod.xls')
    sampling_point_df = pd.read_excel('AQIS_HU_SamplingPoint-all_jav.xls')
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
    #print(network_features)

    for index, row in station_df.iterrows():
        #todo handle suspended stations
        try:
            name = 'STA-' + row['station_eoi_code']
            station_list += CONTENT_STRING.format(name=name)
            station_features += generate_station_feature(row)
        except Exception as e:
            print(e)
            break
    sampling_point_merge = sampling_point_df.merge(station_df, on='station_eoi_code')
    test = sampling_point_df.merge(station_df, on='station_eoi_code').\
            drop_duplicates(subset=['station_eoi_code', 'component_code', 'spo_id', 'oc_id'])

    # generate sampling_points
    for index, row in sampling_point_df.merge(station_df, on='station_eoi_code').\
            drop_duplicates(subset=['station_eoi_code', 'component_code', 'spo_id']).iterrows():
    # for index, row in sampling_point_df.merge(station_df, on='station_eoi_code').iterrows():
    #     if math.isnan(row['oc_id']):
    #         row['oc_id'] = int(row['oc_id_new'])
    #     else:
    #         row['oc_id'] = int(row['oc_id'])
        sp_part = row['station_eoi_code'] + '_' + format_component_code(row['component_code']) + \
               '_' + str(row['spo_id'])
        name = 'SPO-' + sp_part
        #todo check if it is okay
        #name_f = 'SPO_F-' + sp_part + '_' + str(int(row['oc_id']))
        sampling_point_list += CONTENT_STRING.format(name=name)
        print(row['station_eoi_code'])
        sampling_point_features += generate_sampling_point_feature(row, test)
    for index, row in sampling_point_df.merge(station_df, on='station_eoi_code').\
            drop_duplicates(subset=['station_eoi_code', 'component_code', 'spo_id', 'oc_id']).iterrows():
        if math.isnan(row['oc_id']):
            row['oc_id'] = int(row['oc_id_new'])
        else:
            row['oc_id'] = int(row['oc_id'])
        sp_part = row['station_eoi_code'] + '_' + format_component_code(
            row['component_code']) + \
                  '_' + str(row['spo_id'])
        # todo check if it is okay
        name_f = 'SPO_F-' + sp_part + '_' + str(int(row['oc_id']))
        sampling_point_f_list += CONTENT_STRING.format(name=name_f)
        sampling_point_f_features += generate_sampling_point_f_feature(row)

    #print(sampling_point_features)
    print(sampling_point_list)
    #print(sampling_point_f_features)
    all_list = process_list + network_list + station_list + sampling_point_list \
               + sampling_point_f_list
    features = process_features + network_features \
               + station_features + sampling_point_features + sampling_point_f_features

    return all_list, features.rstrip()


def create_responsible_part(responsible_df, all_list):
    structure = read_structure(STRUCTURE_LOCATION.format(filename='resp.txt'))
    # change basics
    structure = sub('\{localid\}', LOCALID, structure)
    structure = sub('\{part\}', PART, structure)
    resp_to_replace = get_fields_to_replace(structure, prefix='resp')

    responsible_string = ''

    # todo is a loop necessary in this case?
    for index, row in responsible_df.iterrows():
        actual_person = sub_all(resp_to_replace, row, structure)
        # todo hardcode
        actual_person = sub('\{all_list\}', all_list,
                            actual_person)
        responsible_string += actual_person

    return responsible_string


def main(drv, mdb):
    con = init_connection(drv, mdb)
    responsible_df = pd.read_sql_query(GET_RESPONSIBLE_QUERY.format(code_comb=CODE_COMB),
                                       con)
    all_list, features = generate_contents(con)
    responsible_string = create_responsible_part(responsible_df, all_list)
    xml = read_structure(STRUCTURE_LOCATION.format(filename='header_d.txt'))

    xml = sub('\{responsible_xml_part\}', responsible_string, xml)
    xml = sub('\{body\}', features, xml)

    xml = sub('\{localid\}', LOCALID, xml)
    xml = sub('\{year\}', YEAR, xml)
    xml = sub('\{datestring\}', DATESTRING, xml)
    save_xml(xml, filename='REP_D-' + LOCALID + '_D_001.xml')

if __name__ == '__main__':
    main("{Microsoft Access Driver (*.mdb, *.accdb)}", "C:\\olm.mdb")
