from generator import *
import pandas as pd
import re
from math import isnan
from datetime import datetime, timedelta

NAMESPACE = 'HU.OMSZ.AQ'
YEAR = '2015'

STRUCTURE_LOCATION = 'structures/e/{filename}'

obp_string = '<aqd:content xlink:href="{namespace}/OBP-{station_eoi_code}_' \
             '{component_code}_{spo_id}_{oc_id}_{year}"/>\n'


def format_component_code(component_code):
    return ''.join(['0'] * (5 - len(str(component_code)))) + str(component_code)


def get_obp_list(sampling_point_df):
    sampling_point_df = pd.read_excel('AQIS_HU_SamplingPoint-001_mod.xls')
    time_series = get_timeseries()
    obp_list = ''
    observ = ''
    for index, row in sampling_point_df.iterrows():
        current_spo = re.sub('\{namespace\}', NAMESPACE, obp_string)
        current_spo = re.sub('\{year\}', YEAR, current_spo)
        current_spo = re.sub('\{component_code\}',
                             format_component_code(row['component_code']), current_spo)
        current_spo = re.sub('\{station_eoi_code\}', row['station_eoi_code'], current_spo)
        current_spo = re.sub('\{spo_id\}', str(row['spo_id']), current_spo)
        if not isnan(row['oc_id']):
            current_spo = re.sub('\{oc_id\}', str(int(row['oc_id'])), current_spo)
        else:
            current_spo = re.sub('\{oc_id\}', str(int(row['oc_id_new'])), current_spo)

        obp_list += current_spo
        try:
            data = time_series[str(row['component_code'])][str(row['station_eoi_code'])]
            ts = list(map(lambda x: x[0].split(' ')[0].split('.')[2] +
                               x[0].split(' ')[0].split('.')[1] +
                               x[0].split(' ')[0].split('.')[0] + ' ' +
                                    ('00:00' if x[0].split(' ')[1] == '24:00' else x[0].split(' ')[1]) +
                               ', ' + str(x[1]), data['timeseries']))

            metric = data['metric']
            observ_time = data['time']
        except KeyError as k:
            ts = ''
            metric = ''
            observ_time = ''
        observ += get_pollutant_observing(row, ts, metric, observ_time) + '\n'

    return obp_list.rstrip(), observ.rstrip()


def get_timeseries():
    files = ['BENZOL', 'CO', 'MP XILOL', 'NO2', 'NOX', 'O3', 'SO2', 'TOLUOL', 'PM10']

    with open('timeseries/mapping.txt') as f:
        mapping = dict(
            map(lambda x: x.split(':'), map(lambda y: y.rstrip(), f.readlines())))

    stations_df = pd.read_excel('Allomaskodok.xls')

    pollutants = {}

    for file in files:
        observ_time = pd.read_excel('timeseries/' + file + '.xls').iloc[0].index[0]
        if 'Day' in observ_time:
            observ_time = 'day'
        elif 'Hr.' in observ_time:
            observ_time = 'hour'
        df = pd.read_excel('timeseries/' + file + '.xls', skiprows=2)

        station_names = list(df.columns)
        station_names.remove('Date & Time')

        station_dict = {}

        for station in station_names:
            current_df = df[['Date & Time', station]]
            current_df = current_df.drop(current_df.index[[0, 1]])
            current_df = current_df.drop(current_df.tail(8).index)

            st_code = \
            stations_df[stations_df['Állomásnév'] == station]['EoI állomáskód'].values[0]
            station_dict[st_code] = dict()
            station_dict[st_code]['metric'] = df[station][1]
            station_dict[st_code]['time'] = observ_time
            station_dict[st_code]['timeseries'] = [tuple(x) for x in current_df.values]

        pollutants[mapping[file]] = station_dict

    return pollutants

def get_pollutant_observing(sp_df, time_series, metric, observ_time):

    time_format = '%Y-%m-%dT%H:%M:%S+01:00'


    # if it is an old device
    if isnan(sp_df['oc_id_new']):
         # and still on, we read the whole file
         # if not on, read the 'first part'
         if not isnan(sp_df['oc_enddate']):
             time_series = list(filter(lambda x: x.split()[0] < str(sp_df['oc_enddate']),
                                       time_series))
    else:
        time_series = list(filter(lambda x: x.split()[0] >= str(sp_df['oc_startdate']),
                                  time_series))
    # todo fix metric
    values = ''
    for ts in time_series:
        dt, f = ts.split(',')
        t = datetime.strptime(dt, "%Y%m%d %H:%M")
        if observ_time == 'hour':
            end_time = t + timedelta(hours=1)
        elif observ_time == 'day':
            end_time = t + timedelta(days=1)
        else:
            end_time = t + timedelta(months=1)
        values += '%s,%s,%s@@' % (t.strftime(time_format), end_time.strftime(time_format),
                                 f.strip())

    structure = read_structure(STRUCTURE_LOCATION.format(filename='samplings.txt'))
    structure = re.sub('\{namespace\}', NAMESPACE, structure)
    structure = re.sub('\{year\}', YEAR, structure)
    structure = re.sub('\{next_year\}', str(int(YEAR) + 1), structure)
    structure = re.sub('\{value_count\}', str(len(time_series)), structure)
    structure = re.sub('\{values\}', values, structure)
    structure = re.sub('\{observation_quantity\}', observ_time, structure)
    structure = re.sub('\{original_component_code\}', str(sp_df['component_code']),
                       structure)
    try:
        structure = re.sub('\{process_id\}', sp_df['process_id'], structure)
    except:
        structure = re.sub('\{process_id\}', sp_df['process_id_new'], structure)
    structure = re.sub('\{current_time\}', datetime.now().strftime(time_format), structure)

    structure = re.sub('\{component_code\}',
                         format_component_code(sp_df['component_code']), structure)
    structure = re.sub('\{station_eoi_code\}', sp_df['station_eoi_code'], structure)
    structure = re.sub('\{spo_id\}', str(sp_df['spo_id']), structure)
    if not isnan(sp_df['oc_id']):
        structure = re.sub('\{oc_id\}', str(int(sp_df['oc_id'])), structure)
    else:
        structure = re.sub('\{oc_id\}', str(int(sp_df['oc_id_new'])), structure)

    return structure


def main(drv, mdb):
    con = init_connection(drv, mdb)
    sampling_point_df = pd.read_excel('AQIS_HU_SamplingPoint-001_mod.xls')

    obp_list_string, observations = get_obp_list(sampling_point_df)

    save_xml(observations, filename='E.xml')


if __name__ == '__main__':
    main("{Microsoft Access Driver (*.mdb, *.accdb)}", "C:\\olm.mdb")