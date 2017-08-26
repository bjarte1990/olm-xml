from generate_c import *
import pandas as pd

REASON_STRING = '<aqd:reason xlink:href="http://dd.eionet.europa.eu/vocabulary/aq/exceedancereason/{reason}"/>'
NUMBER_EXCEEDENCE_STRING = '<aqd:numberExceedances>{exc_number_max}</aqd:numberExceedances>'
NUMERICAL_EXCEEDANCE_STRING = '<aqd:numericalExceedance>{exc_value_max}</aqd:numericalExceedance>'
ROAD_LENGTH_STRING = '<aqd:roadLength uom="http://dd.eionet.europa.eu/vocabulary/uom/length/km">{exc_road_length}</aqd:roadLength>'
POPULATION_EXPOSED_STRING = '<aqd:populationExposed>{exc_exp_population}</aqd:populationExposed>'
SURFACE_AREA_STRING = '<aqd:surfaceArea uom="http://dd.eionet.europa.eu/vocabulary/uom/area/km2">{exc_area}</aqd:surfaceArea>'
COMMENT_STRING = '<aqd:comment />'

G_SAMPLING_POINTS_STRING = '\n\t\t\t\t\t\t\t<aqd:stationUsed ' \
                         'xlink:href="{namespace}/' \
                         'SPO-{sn_eu_code}_{cp_number}_{mc_group_code}"/>'


def create_reason_string(reasons):
    reason_string = ''
    for reason in reasons.split(';'):
        reason_string += re.sub('\{reason\}',reason,REASON_STRING) + '\n'
    return reason_string


def generate_sampling_points_for_g(sampling_points_df):
    structure = re.sub('\{namespace\}', NAMESPACE, G_SAMPLING_POINTS_STRING)
    poll_to_replace = get_fields_to_replace(structure)

    pollutants_string = ''
    for index, row in sampling_points_df.iterrows():
        pollutants_string += sub_all(poll_to_replace, row, structure)

    return pollutants_string.rstrip()


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

    # current_structure = re.sub('\{exc\.stations\}', 'STATIONS ARE MISSING!!!!!!!',
    #                            current_structure)

    current_structure = re.sub('\{exc\.population\}', exc_exp_population_string,
                               current_structure)

    current_structure = re.sub('\{exc\.reason\}', exc_reason_string, current_structure)

    current_structure = re.sub('\{exc.comment\}', '<aqd:comment/ >', current_structure)

    return current_structure


def get_detailed_evaluation(zone_metrics_df, sampling_points_df):
    eval_file = 'Attainments_HU-001_exportv3.xls'
    station_file = 'AQIS_HU_Station-001_mod.xls'
    false_structure = read_structure('areas_g_false.txt')
    true_structure = read_structure('areas_g_true.txt')

    evaluation_df = pd.read_excel(eval_file)
    station_df = pd.read_excel(station_file)[['station_eoi_code', 'station_type_of_area']]

    zone_evaluation_df = zone_metrics_df.merge(evaluation_df,
                                               left_on=['zn_code', 'env_poll_code'],
                                               right_on=['zone_code', 'ENV_pollutant'])

    # zone_evaluation_df = zone_evaluation_df.merge(station_df, left_on=['zn_code'],
    #                                               right_on=['station_eoi_code'])
    #
    # print(zone_evaluation_df)
    zone_evaluation_string = ''
    for index, row in zone_evaluation_df.iterrows():
        if row['attainment'] == 'Y':
            current_structure = false_structure
        else: #if row['attainment_final'] == 'Y': #Y&N
            current_structure = true_structure
            current_structure = parse_info(row, current_structure)

        areas_to_replace = get_fields_to_replace(current_structure, prefix='zone')
        cp_number = ''.join(['0'] * (5 - len(str(row['cp_number'])))) + str(
            row['cp_number'])
        actual_area = re.sub('\{ZEROS#cp_number\}', cp_number, current_structure)
        actual_area = sub_all(areas_to_replace, row, actual_area)
        zone_evaluation_string += actual_area

        actual_sampling_points = sampling_points_df[
            sampling_points_df['cp_number'] == row['cp_number']]
        actual_sampling_points = actual_sampling_points.loc[
            (actual_sampling_points['zn_code'] == row['zn_code'])]

        sn_codes = list(actual_sampling_points['sn_code'].drop_duplicates())

        actual_sampling_points = sampling_points_df[
            sampling_points_df['sn_code'].isin(sn_codes)]
        actual_sampling_points = actual_sampling_points.loc[
            (actual_sampling_points['cp_number'] == row['cp_number'])]

        actual_sampling_points = actual_sampling_points.merge(station_df,
                                                              left_on='sn_eu_code',
                                                              right_on='station_eoi_code')
        station_class_string = '\n'
        for station_type in set(actual_sampling_points['station_type_of_area']):
            station_class_string += '<aqd:areaClassification xlink:href=' \
                                    '"http://dd.eionet.europa.eu/vocabulary/aq/' \
                                    'areaclassification/{t}"/>\n'.format(t=station_type)
        zone_evaluation_string = re.sub('\{area_classification\}', station_class_string,
                                        zone_evaluation_string)

        zone_evaluation_string = re.sub('\{exc\.stations\}',
                                        generate_sampling_points_for_g(actual_sampling_points),
                                        zone_evaluation_string)
        # station_df[station_df['station_eoi_code'] == 'HU0017A'][
        #     'station_type_of_area'].item()

    zone_evaluation_string = re.sub('\{year\}', YEAR, zone_evaluation_string)
    #todo namespaces
    return zone_evaluation_string


def main(drv, mdb):
    con = init_connection(drv, mdb)
    zone_metrics_df = pd.read_sql_query(ZONE_METRIC_SQL, con)
    zone_metrics_df = zone_metrics_df.drop_duplicates(subset=['zn_code', 'cp_number',
                                                              'objective_type',
                                                              'rep_metric', ])
    sampling_points_df = pd.read_sql_query(SAMPLING_POINT_QUERY, con)

    zone_evaluation_string = get_detailed_evaluation(zone_metrics_df, sampling_points_df)
    print(zone_evaluation_string)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])