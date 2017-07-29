import sys
import re
import pandas as pd
from generator import *

NAMESPACE = "HU.OMSZ.AQ"
YEAR = "2015"

CODE_COMB = 3

AREAS_STRING = '<aqd:content xlink:href="{namespace}/ARE-{zn_code}_{cp_number}_' \
               '{objective_type}_{rep_metric}_{year}"/>'

#todo must get rid of it
GET_RESPONSIBLE_QUERY = "SELECT * FROM (AQD_responsible_authority ra " \
                        "INNER JOIN person p on p.ps_code = ra.ps_code) " \
                        "INNER JOIN organization o on o.og_code = ra.og_code " \
                        "WHERE ra.nn_code_iso2 = 'hu' AND ra.ac_code_comb = {code_comb}"

# todo filtering to H is good?
ZONE_METRIC_SQL = "SELECT p.nn_code_iso2, p.zn_code, p.cp_number, eo.pt_poll_code, " \
                  "eo.objective_type, eo.rep_metric, eo.pt_code " \
                  "FROM AQD_zone_pollutant p INNER JOIN AQD_environmental_objective eo " \
                  "ON p.cp_number = eo.cp_number " \
                  "WHERE p.nn_code_iso2 = 'hu' " \
                  "AND eo.objective_type NOT IN ('lvmot', 'eco', 'ert') " \
                  "AND eo.pt_code = 'H' " \
                  "GROUP BY p.nn_code_iso2, p.zn_code, p.cp_number, eo.pt_poll_code, " \
                  "eo.objective_type, eo.rep_metric, eo.pt_code"

SAMPLING_POINT_QUERY = "SELECT sp.zn_code, sp.cp_number, sp.mc_group_code, s.sn_eu_code " \
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

def create_areas(zone_metrics_df):
    structure = read_structure('areas.txt')
    areas_to_replace = get_fields_to_replace(structure, prefix='zone')
    print(areas_to_replace)
    #todo deal with WHATISTHIS

    areas_string = ''
    for index, row in zone_metrics_df.iterrows():
        # todo find better solution
        cp_number = ''.join(['0'] * (5 - len(str(row['cp_number'])))) + str(
            row['cp_number'])
        actual_area = re.sub('\{ZEROS#cp_number\}', cp_number, structure)
        actual_area = sub_all(areas_to_replace, row, actual_area)

        areas_string += actual_area

    areas_string = re.sub('\{year\}', YEAR, areas_string)

    print(areas_string)

def main(drv, mdb):
    con = init_connection(drv, mdb)
    responsible_df = pd.read_sql_query(GET_RESPONSIBLE_QUERY.format(code_comb=CODE_COMB), con)
    zone_metrics_df = pd.read_sql_query(ZONE_METRIC_SQL, con)

    responsible_string = create_responsible_part(responsible_df,zone_metrics_df)

    sampling_points_df = pd.read_sql_query(SAMPLING_POINT_QUERY, con)

    create_areas(zone_metrics_df)
    #print(responsible_string)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])