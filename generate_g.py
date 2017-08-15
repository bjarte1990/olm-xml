from generator import *
from generate_c import *
import pandas as pd
import numpy as np

REASON_STRING = '<aqd:reason xlink:href="http://dd.eionet.europa.eu/vocabulary/aq/exceedancereason/{reason}"/>'
NUMBER_EXCEEDENCE_STRING = '<aqd:numberExceedances>{exc_number_max}</aqd:numberExceedances>'
NUMERICAL_EXCEEDANCE_STRING = '<aqd:numericalExceedance>{exc_value_max}</aqd:numericalExceedance>'
ROAD_LENGTH_STRING = '<aqd:roadLength uom="http://dd.eionet.europa.eu/vocabulary/uom/length/km">{exc_road_length}</aqd:roadLength>'
POPULATION_EXPOSED_STRING = '<aqd:populationExposed>{exc_exp_population}</aqd:populationExposed>'
SURFACE_AREA_STRING = '<aqd:surfaceArea uom="http://dd.eionet.europa.eu/vocabulary/uom/area/km2">{exc_area}</aqd:surfaceArea>'
COMMENT_STRING = '<aqd:comment />'


def create_reason_string(reasons):
    reason_string = ''
    for reason in reasons.split(';'):
        reason_string += re.sub('\{reason\}',reason,REASON_STRING) + '\n'
    return reason_string


def parse_info(row, current_structure):

    exc_number_max_string = ''
    exc_value_max_string = ''
    exc_area_string = ''
    exc_road_length_string = ''
    exc_exp_population_string = ''
    exc_reason_string = ''
    exc_comment_string = ''

    if not pd.isnull(row['exc_number_max']):
        exc_number_max_string = re.sub('\{exc_number_max\}', str(row['exc_number_max']),
                                       NUMBER_EXCEEDENCE_STRING)

    if not pd.isnull(row['exc_value_max']):
        exc_value_max_string = re.sub('\{exc_value_max\}', str(row['exc_value_max']),
                                      NUMERICAL_EXCEEDANCE_STRING)

    if not pd.isnull(row['exc_area']):
        exc_area_string = re.sub('\{exc_area\}', str(row['exc_area']), SURFACE_AREA_STRING)

    if not pd.isnull(row['exc_road_length']):
        exc_road_length_string = re.sub('\{exc_road_length\}', str(row['exc_road_length']),
                                        ROAD_LENGTH_STRING)

    if not pd.isnull(row['exc_exp_population']):
        exc_exp_population_string = re.sub('\{exc_exp_population\}',
                                           str(row['exc_exp_population']),
                                           POPULATION_EXPOSED_STRING)

    if not pd.isnull(row['exc_reason']):
        exc_reason_string = create_reason_string(row['exc_reason'])

    if not pd.isnull(row['exc_comment']):
        exc_comment_string = re.sub('\{exc_comment\}', str(row['exc_comment']), COMMENT_STRING)

    # sub 1by1
    current_structure = re.sub('\{exc\.number_exceedence\}', exc_number_max_string,
                               current_structure)
    current_structure = re.sub('\{exc\.numerical_exceedence\}', exc_value_max_string,
                               current_structure)

    current_structure = re.sub('\{exc\.surface_area\}', exc_area_string,
                               current_structure)

    current_structure = re.sub('\{exc\.road_length\}', exc_road_length_string,
                               current_structure)

    current_structure = re.sub('\{exc\.stations\}', 'STATIONS ARE MISSING!!!!!!!',
                               current_structure)

    current_structure = re.sub('\{exc\.population\}', exc_exp_population_string,
                               current_structure)

    current_structure = re.sub('\{exc\.reason\}', exc_reason_string, current_structure)

    current_structure = re.sub('\{exc.comment\}', '<aqd:comment/ >', current_structure)

    return current_structure


def get_detailed_evaluation():
    eval_file = 'Attainments_HU-001_exportv3.xls'
    false_structure = read_structure('areas_g_false.txt')
    true_structure = read_structure('areas_g_true.txt')

    evaluation_df = pd.read_excel(eval_file)

    # zone_evaluation_df = zone_metrics_df.merge(evaluation_df,
    #                                            left_on=['zn_code', 'env_poll_code'],
    #                                            right_on=['zone_code', 'ENV_pollutant'])
    zone_evaluation_df = evaluation_df

    zone_evaluation_string = ''

    for index, row in zone_evaluation_df.iterrows():
        if row['attainment'] == 'Y':
            current_structure = false_structure
        elif row['attainment_final'] == 'Y': #Y&N
            current_structure = true_structure
            current_structure = parse_info(row, current_structure)
            print(current_structure)
            print()



def main(drv, mdb):
    con = init_connection(drv, mdb)

    get_detailed_evaluation()

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])