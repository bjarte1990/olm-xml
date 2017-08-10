import sys
import pandas as pd
from generator import *

NAMESPACE = "HU.OMSZ.AQ"
YEAR = "2015"

CODE_COMB = 3

#todo authorities code comb
AAQ = 3 #assessmentAirQuality
AMS = 60 #approvalMeasurementSystems
AM = 60 #accuracyMeasurements
AAM = 60 #analysisAssessmentMethod
NWQA = 60 #nationWideQualityAssurance
CMC = 64 #cooperationMSCommission


AREAS_STRING = '<aqd:content xlink:href="{namespace}/ARE-{zn_code}_{cp_number}_' \
               '{objective_type}_{rep_metric}_{year}"/>'

SAMPLING_POINTS_STRING = '<aqd:samplingPointAssessmentMetadata ' \
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
ZONE_METRIC_SQL = "SELECT " \
                  "p.nn_code_iso2, p.zn_code, p.cp_number, eo.pt_poll_code, " \
                  "eo.objective_type, eo.rep_metric, eo.pt_code, sp.sn_code  " \
                  "FROM (AQD_zone_pollutant p INNER JOIN AQD_environmental_objective eo " \
                  "ON p.cp_number = eo.cp_number) " \
                  "INNER JOIN AQD_sampling_point_for_compliance sp " \
                  "ON p.cp_number = sp.cp_number AND p.zn_code = sp.zn_code " \
                  "WHERE p.nn_code_iso2 = 'hu' " \
                  "AND eo.objective_type NOT IN ('lvmot', 'eco', 'ert') " \
                  "AND eo.pt_code = 'H' " \
                  "GROUP BY p.nn_code_iso2, p.zn_code, p.cp_number, " \
                  "eo.pt_poll_code, " \
                  "eo.objective_type, eo.rep_metric, eo.pt_code, sp.sn_code"


SAMPLING_POINT_QUERY = "SELECT sp.sn_code, sp.zn_code, sp.cp_number, sp.mc_group_code, s.sn_eu_code " \
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
    structure = read_structure('authorities.txt')
    components = get_authorities_components_df(authorities_df)
    for key,value in components.items():
        structure = change_authorites_in_structure(value, key, structure)

    return structure


# todo not nice, have to make a common solution for B and C
def create_responsible_part(responsible_df, zone_metrics_df):
    structure = read_structure('resp.txt')
    resp_to_replace = get_fields_to_replace(structure, prefix='resp')

    responsible_string = ''

    # todo is a loop necessary in this case?
    for index, row in responsible_df.iterrows():
        actual_person = sub_all(resp_to_replace, row, structure)
        # todo hardcode
        actual_person = re.sub('\{zone_list\}', get_areas_string(zone_metrics_df), actual_person)
        responsible_string += actual_person

    return responsible_string


def generate_sampling_points(sampling_points_df):
    structure = re.sub('\{namespace\}', NAMESPACE, SAMPLING_POINTS_STRING)
    poll_to_replace = get_fields_to_replace(structure)

    pollutants_string = ''
    for index, row in sampling_points_df.iterrows():
        pollutants_string += sub_all(poll_to_replace, row, structure) + '\n'

    return pollutants_string.rstrip()


def create_areas(zone_metrics_df, sampling_points_df):
    structure = read_structure('areas.txt')
    areas_to_replace = get_fields_to_replace(structure, prefix='zone')
    #print(areas_to_replace)
    #todo deal with WHATISTHIS

    areas_string = ''
    for index, row in zone_metrics_df.iterrows():
        # todo find better solution
        cp_number = ''.join(['0'] * (5 - len(str(row['cp_number'])))) + str(
            row['cp_number'])
        actual_area = re.sub('\{ZEROS#cp_number\}', cp_number, structure)
        actual_area = sub_all(areas_to_replace, row, actual_area)

        areas_string += actual_area

        actual_sampling_points = sampling_points_df[
            sampling_points_df['cp_number'] == row['cp_number']]
        actual_sampling_points = actual_sampling_points.loc[
             (actual_sampling_points['zn_code'] == row['zn_code'])]

        sn_codes = list(actual_sampling_points['sn_code'].drop_duplicates())

        actual_sampling_points = sampling_points_df[
            sampling_points_df['sn_code'].isin(sn_codes)]
        actual_sampling_points = actual_sampling_points.loc[
            (actual_sampling_points['cp_number'] == row['cp_number'])]

        areas_string = re.sub('\{sampling_points\}',
                              generate_sampling_points(actual_sampling_points), areas_string)

    areas_string = re.sub('\{year\}', YEAR, areas_string)

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

    return responsible_df,authorities_df,zone_metrics_df,sampling_points_df


def generate_string_from_dfs(responsible_df,authorities_df,zone_metrics_df,
                             sampling_points_df):

    responsible_string = create_responsible_part(responsible_df, zone_metrics_df)
    authorities_string = create_authorities(authorities_df)
    zones_string = create_areas(zone_metrics_df, sampling_points_df)

    return responsible_string, authorities_string, zones_string


def generate_xml_structure(con, structure_file_name):
    # define df-s by querying database
    responsible_df, authorities_df, zone_metrics_df, sampling_points_df = create_dfs(con)

    # create xml parts using df-s
    responsible_string, authorities_string, zones_string = generate_string_from_dfs(
        responsible_df, authorities_df, zone_metrics_df, sampling_points_df)

    xml = read_structure('header_c.txt')
    xml = re.sub('\{responsible_xml_part\}', responsible_string, xml)
    xml = re.sub('\{authorities_xml_part\}', authorities_string, xml)
    xml = re.sub('\{zones_xml_part\}', zones_string, xml)

    return xml


def main(drv, mdb):
    con = init_connection(drv, mdb)

    xml = generate_xml_structure(con, 'header_c.txt')

    save_xml(xml, filename='C.xml')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])