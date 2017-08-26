from generator import *
import pandas as pd
import re
import math

NAMESPACE = 'HU.OMSZ.AQ'
STRUCTURE_PATH = 'structures/d/'

CONTENT_STRING = '<aqd:content xlink:href="' + NAMESPACE + '/{name}"/>\n'


def format_component_code(component_code):
    return ''.join(['0'] * (5 - len(str(component_code)))) + str(component_code)


def generate_process_feature(p):
    structure = read_structure('process.txt')
    structure = re.sub('\{NAMESPACE\}', NAMESPACE, structure)

    if p['method_type'] == 'active':
        method_structure = read_structure('sampling_method.txt')
        method_structure = re.sub('\{method\}', 'other', method_structure)
        method_structure = re.sub('\{other_method\}', 'UNKNOWN', method_structure)
    else:
        method_structure = read_structure('measurement_method.txt')
    structure = re.sub('\{sampling_method\}', method_structure, structure)

    # fix fields
    other_equipment_string_flag = False
    if isinstance(p['equipmentcode'], int):
        structure = re.sub('\{process.equipmentcode\}', 'other', structure)
        structure = re.sub('\{other_equipment_part\}', '<aqd:otherEquipment>"' + p['equipmentname'] +
                           '"</aqd:otherEquipment>', structure)
        other_equipment_string_flag = True
    else:
        structure = re.sub('\{other_equipment_part\}', '<aqd:otherEquipment/>', structure)
    if isinstance(p['techniquecode'], int):
        structure = re.sub('\{process.techniquecode\}', 'other', structure)
        # active eseten nincs ilyen
        if p['method_type'] == 'active':
            structure = re.sub('\{other_first_tag\}', '<aqd:otherAnalyticalTechnique>"' + p['techniquename'] +
                               '"</aqd:otherAnalyticalTechnique>', structure)
        else:
            structure = re.sub('\{other_first_tag\}', '<aqd:otherMeasurementMethod>"' + p['techniquename'] +
                               '"</aqd:otherMeasurementMethod>', structure)
    else:
        if p['method_type'] == 'active':
            if other_equipment_string_flag:
                structure = re.sub('\{other_first_tag\}', '<aqd:otherAnalyticalTechnique>"'
                                                          '"</aqd:otherAnalyticalTechnique>', structure)
            else:
                structure = re.sub('\{other_first_tag\}', '<aqd:otherAnalyticalTechnique/>', structure)
        else:
            structure = re.sub('\{other_first_tag\}', '<aqd:otherMeasurementMethod/>', structure)

    fields = get_fields_to_replace(structure, 'process')

    structure = sub_all(fields, p, structure)
    return structure


def generate_network_feature(n):
    structure = read_structure(STRUCTURE_PATH + 'network.txt')
    structure = re.sub('\{NAMESPACE\}', NAMESPACE, structure)
    structure = re.sub('\{address1\}', ' '.join(n['manager_organization_address'].split()[:2]), structure)
    structure = re.sub('\{address2\}', n['manager_organization_address'].split()[1], structure)

    fields = get_fields_to_replace(structure, 'network')
    structure = sub_all(fields, n, structure)

    return structure


def generate_station_feature(s):
    structure = read_structure(STRUCTURE_PATH + 'station.txt')
    structure = re.sub('\{NAMESPACE\}', NAMESPACE, structure)
    structure = re.sub('\{date\}', str(s['station_start_date'])[:4] + "-" + str(s['station_start_date'])[4:6] + '-' +
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
    structure = re.sub('\{NAMESPACE\}', NAMESPACE, structure)
    structure = re.sub('\{component_code\}', component_code, structure)

    structure = re.sub('\{spo_start_date\}', str(sp['spo_startdate'])[:4] + "-" + str(sp['spo_startdate'])[4:6] + '-' +
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
    structure = re.sub('\{NAMESPACE\}', NAMESPACE, structure)
    structure = re.sub('\{component_code\}', component_code, structure)

    fields = get_fields_to_replace(structure, 'spf')
    structure = sub_all(fields, spf, structure)

    return structure


def generate_contents():
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
    network_df = pd.read_excel('AQIS_HU_Network-001_mod.xls')
    network_df = network_df.sort_values('network_code')

    station_df = pd.read_excel('AQIS_HU_Station-001_mod.xls')

    sampling_point_df = pd.read_excel('AQIS_HU_SamplingPoint-001_mod.xls')

    # generate processes
    for index, row in process_df.iterrows():
        process_list += CONTENT_STRING.format(name=row['process_id'])
        process_features += generate_process_feature(row)

    #todo: generate networks & stations (using db)
    for index, row in network_df.iterrows():
        name = 'NET-' + row['network_code']
        network_list += CONTENT_STRING.format(name=name)
        network_features += generate_network_feature(row)

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

    print(sampling_point_f_features)


def main():
    generate_contents()

if __name__ == '__main__':
    main()
