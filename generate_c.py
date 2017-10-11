import sys
import pandas as pd
from generator import *
from time import strftime, gmtime

NAMESPACE = "HU.OMSZ.AQ"
YEAR = "2016"
DATESTRING = strftime("%Y%m%d", gmtime())
LOCALID = "HU_OMSZ_" + DATESTRING
PART = "C"

STRUCTURE_LOCATION = 'structures/c/{filename}'
CODE_COMB = 3

#todo authorities code comb
AAQ = 3 #assessmentAirQuality
AMS = 60 #approvalMeasurementSystems
AM = 60 #accuracyMeasurements
AAM = 60 #analysisAssessmentMethod
NWQA = 60 #nationWideQualityAssurance
CMC = 64 #cooperationMSCommission


AREAS_STRING = '\t\t\t<aqd:content xlink:href="{namespace}/ARE-{zn_code}_{cp_number}_' \
               '{objective_type}_{rep_metric}_{year}"/>'

SAMPLING_POINTS_STRING = '\n\t\t\t\t\t<aqd:samplingPointAssessmentMetadata ' \
                         'xlink:href="{namespace}/' \
                         'SPO-{sn_eu_code}_{cp_number}_{mc_group_code}"/>'

GET_AUTHORITIES_QUERY = "SELECT * FROM (AQD_responsible_authority ra " \
                        "INNER JOIN person p on p.ps_code=ra.ps_code) " \
                        "INNER JOIN organization o on o.og_code=ra.og_code " \
                        "WHERE ra.nn_code_iso2 = 'hu'"

#todo must get rid of it
GET_RESPONSIBLE_QUERY = "SELECT * FROM (AQD_responsible_authority ra " \
                        "INNER JOIN person p on p.ps_code = ra.ps_code) " \
                        "INNER JOIN organization o on o.og_code = ra.og_code " \
                        "WHERE ra.nn_code_iso2 = 'hu' AND ra.ac_code_comb = {code_comb}"

# todo filtering to H is good?
# ZONE_METRIC_SQL = "SELECT " \
#                   "p.nn_code_iso2, p.zn_code, p.cp_number, eo.comp_id, eo.pt_poll_code, " \
#                   "eo.env_poll_code, eo.objective_type, eo.rep_metric, eo.pt_code, sp.sn_code  " \
#                   "FROM (AQD_zone_pollutant p INNER JOIN AQD_environmental_objective eo " \
#                   "ON p.cp_number = eo.cp_number) " \
#                   "INNER JOIN AQD_sampling_point_for_compliance sp " \
#                   "ON p.cp_number = sp.cp_number AND p.zn_code = sp.zn_code " \
#                   "WHERE p.nn_code_iso2 = 'hu' " \
#                   "AND eo.objective_type NOT IN ('lvmot', 'eco', 'ert') " \
#                   "AND eo.pt_code = 'H' " \
#                   "GROUP BY p.nn_code_iso2, p.zn_code, p.cp_number, " \
#                   "eo.comp_id, eo.pt_poll_code, eo.env_poll_code," \
#                   "eo.objective_type, eo.rep_metric, eo.pt_code, sp.sn_code"

ZONE_METRIC_SQL = "SELECT p.zn_code, p.cp_number, eo.objective_type, eo.rep_metric, " \
                  "eo.pt_code, eo.env_poll_code FROM " \
                  "AQD_zone_pollutant p INNER JOIN AQD_environmental_objective eo " \
                  "ON p.cp_number = eo.cp_number AND p.pt_code = eo.pt_code " \
                  "WHERE p.nn_code_iso2 = 'HU' AND eo.objective_type NOT IN " \
                  "('LVMOT', 'ECO', 'ERT') " \
                  "ORDER BY p.zn_code, eo.env_poll_code"


SAMPLING_POINT_QUERY = "SELECT sp.sn_code, sp.zn_code, sp.cp_number, sp.mc_group_code, " \
                       "s.sn_eu_code " \
                       "FROM AQD_sampling_point_for_compliance sp INNER JOIN station s " \
                       "ON sp.sn_code = s.sn_code " \
                       "WHERE s.nn_code_iso2 = 'hu'"


def get_areas_string(zone_metrics_df):
    # todo init competent authorities, now it is hardcoded
    structure = AREAS_STRING
    areas_string = '<aqd:content xlink:href="{namespace}/REP_C-{year}_{year}"/>\n'.format(
        namespace=NAMESPACE, year=YEAR)

    for index, row in zone_metrics_df.iterrows():
        # 5 char long code
        cp_number = ''.join(['0']*(5-len(str(row['cp_number'])))) + str(row['cp_number'])
        areas_string += structure.format(namespace=NAMESPACE,
                                         year=YEAR,
                                         zn_code=row['zn_code'],
                                         cp_number=cp_number,
                                         objective_type=row['objective_type'],
                                         rep_metric=row['rep_metric']) + '\n'

    areas_string = areas_string.rstrip()
    return areas_string


def get_authorities_components_df(authorities_df):
    components = dict()
    components['aaq'] = authorities_df[authorities_df['ac_code_comb'] == AAQ].reset_index()
    components['ams'] = authorities_df[authorities_df['ac_code_comb'] == AMS].reset_index()
    components['am'] = authorities_df[authorities_df['ac_code_comb'] == AM].reset_index()
    components['aam'] = authorities_df[authorities_df['ac_code_comb'] == AAM].reset_index()
    components['nwqa'] = authorities_df[authorities_df['ac_code_comb'] == NWQA].reset_index()
    components['cmc'] = authorities_df[authorities_df['ac_code_comb'] == CMC].reset_index()

    return components


def change_authorites_in_structure(authority_df, prefix, structure):
    au_to_replace = get_fields_to_replace(structure, prefix=prefix)

    return sub_all(au_to_replace, authority_df.loc[0], structure)


def create_authorities(authorities_df):
    structure = read_structure(STRUCTURE_LOCATION.format(filename='authorities.txt'))
    components = get_authorities_components_df(authorities_df)
    for key,value in components.items():
        structure = change_authorites_in_structure(value, key, structure)

    return structure


# todo not nice, have to make a common solution for B and C
def create_responsible_part(responsible_df, zone_metrics_df):
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
        actual_person = sub('\{zone_list\}', get_areas_string(zone_metrics_df),
                            actual_person)
        responsible_string += actual_person

    return responsible_string


def generate_sampling_points(sampling_points_df):
    structure = sub('\{namespace\}', NAMESPACE, SAMPLING_POINTS_STRING)
    poll_to_replace = get_fields_to_replace(structure)

    pollutants_string = ''
    for index, row in sampling_points_df.iterrows():
        cp_number = ''.join(['0'] * (5 - len(str(row['cp_number'])))) + str(
            row['cp_number'])
        structure = sub('\{cp_number\}', cp_number, structure)
        pollutants_string += sub_all(poll_to_replace, row, structure)

    return pollutants_string.rstrip()


def include_modifications(actual_sampling_points, mod_df):
    final_df = actual_sampling_points
    for index,row in actual_sampling_points.iterrows():
        tmp = mod_df[mod_df['station_eoi_code'] == row['sn_eu_code']]
        tmp = tmp[tmp['component_code'] == row['cp_number']]
        if tmp['change'].iloc[0] == 'M':
            final_df = final_df.append(row)

    return final_df.sort_values(['sn_eu_code'])


def create_areas(zone_metrics_df, sampling_points_df):
    structure = read_structure(STRUCTURE_LOCATION.format(filename='areas.txt'))
    areas_to_replace = get_fields_to_replace(structure, prefix='zone')

    mod_df = pd.read_excel('AQIS_HU_SamplingPoint-003_2016_mod.xls')

    areas_string = ''
    for index, row in zone_metrics_df.iterrows():
        # todo find better solution
        cp_number = ''.join(['0'] * (5 - len(str(row['cp_number'])))) + str(
            row['cp_number'])
        actual_area = sub('\{ZEROS#cp_number\}', cp_number, structure)
        actual_area = sub_all(areas_to_replace, row, actual_area)

        areas_string += actual_area + '\n'

        actual_sampling_points = sampling_points_df[
            sampling_points_df['cp_number'] == row['cp_number']]
        actual_sampling_points = actual_sampling_points[
             actual_sampling_points['zn_code'] == row['zn_code']]

        # include M
        #actual_sampling_points = include_modifications(actual_sampling_points,mod_df)

        areas_string = sub('\{sampling_points\}',
                              generate_sampling_points(actual_sampling_points), areas_string)

    areas_string = sub('\{year\}', YEAR, areas_string)

    return areas_string


def create_dfs(con):
    responsible_df = pd.read_sql_query(GET_RESPONSIBLE_QUERY.format(code_comb=CODE_COMB),
                                       con)
    authorities_df = pd.read_sql_query(GET_AUTHORITIES_QUERY, con)
    zone_metrics_df = pd.read_sql_query(ZONE_METRIC_SQL, con)
    zone_metrics_df = zone_metrics_df.drop_duplicates(subset=['zn_code', 'cp_number',
                                                              'objective_type',
                                                              'rep_metric', ])
    sampling_points_df = pd.read_sql_query(SAMPLING_POINT_QUERY, con)
    station_codes = pd.read_excel('Allomaskodok.xls')
    sampling_points_from_file = pd.read_excel('AQIS_HU_SamplingPoint-003_2016_mod.xls')
    sampling_points_from_file = sampling_points_from_file.merge(station_codes,
                                                                left_on=['station_name'],
                                                                right_on=['Station name'])
    sampling_points_from_file = sampling_points_from_file[['Zone code', 'component_code',
                                                          'spo_id', 'station_eoi_code']]
    sampling_points_from_file.columns = ['zn_code', 'cp_number', 'mc_group_code',
                                         'sn_eu_code']
    return responsible_df,authorities_df,zone_metrics_df,sampling_points_from_file


def generate_string_from_dfs(responsible_df,authorities_df,zone_metrics_df,
                             sampling_points_df):

    responsible_string = create_responsible_part(responsible_df, zone_metrics_df)
    authorities_string = create_authorities(authorities_df)
    zones_string = create_areas(zone_metrics_df, sampling_points_df)

    return responsible_string, authorities_string, zones_string


def evaluate_zones(zone_metrics_df):
    eval_file_name = 'AssessmentRegimes2016.xls'
    evaluation_df = pd.read_excel(eval_file_name)
    evaluation_df = evaluation_df.dropna(subset=['assessment_method_type',
                                                 'assessment_threshold_exceedance'])
    return zone_metrics_df.merge(evaluation_df, left_on=['zn_code', 'env_poll_code'],
                                right_on=['zone_code', 'ENV_pollutant'])


def generate_xml_structure(con, structure_file_name):
    # define df-s by querying database
    responsible_df, authorities_df, zone_metrics_df, sampling_points_df = create_dfs(con)

    #todo modify zone__metrics_df
    zone_metrics_df = evaluate_zones(zone_metrics_df)

    # create xml parts using df-s
    responsible_string, authorities_string, zones_string = generate_string_from_dfs(
        responsible_df, authorities_df, zone_metrics_df, sampling_points_df)

    xml = read_structure(structure_file_name)
    xml = sub('\{responsible_xml_part\}', responsible_string, xml)
    xml = sub('\{authorities_xml_part\}', authorities_string, xml)
    xml = sub('\{zones_xml_part\}', zones_string, xml)
    xml = sub('\{localid\}', LOCALID, xml)
    xml = sub('\{year\}', YEAR, xml)

    return xml


def main(drv, mdb):
    con = init_connection(drv, mdb)

    xml = generate_xml_structure(con, STRUCTURE_LOCATION.format(filename='header_c.txt'))

    save_xml(xml, filename='REP_D-' + LOCALID + '_C_001.xml')
    print('C generation finished')

if __name__ == '__main__':
    main("{Microsoft Access Driver (*.mdb, *.accdb)}", "C:\\olm.mdb")