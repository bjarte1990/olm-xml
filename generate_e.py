from generator import *
import pandas as pd
import re
from math import isnan
from datetime import datetime, timedelta
import numpy as np
from time import strftime, gmtime

NAMESPACE = "HU.OMSZ.AQ"
YEAR = "2016"
DATESTRING = strftime("%Y%m%d", gmtime())
LOCALID = "HU_OMSZ_" + DATESTRING
PART = "E"

STRUCTURE_LOCATION = 'structures/e/{filename}'

obp_string = '<aqd:content xlink:href="{namespace}/OBP-{station_eoi_code}_' \
             '{component_code}_{spo_id}_{oc_id}_{year}"/>\n'


GET_RESPONSIBLE_QUERY = "SELECT * FROM (AQD_responsible_authority ra " \
                        "INNER JOIN person p on p.ps_code = ra.ps_code) " \
                        "INNER JOIN organization o on o.og_code = ra.og_code " \
                        "WHERE ra.nn_code_iso2 = 'hu' AND ra.ac_code_comb = {code_comb}"

CODE_COMB = 3

def format_component_code(component_code):
    return ''.join(['0'] * (5 - len(str(component_code)))) + str(component_code)


def get_obp_list():
    #sampling_point_df = pd.read_excel('AQIS_HU_SamplingPoint-003_2016_mod.xls')
    sampling_point_df = pd.read_excel('AQIS_HU_SamplingPoint-all_jav.xls')

    code_list = [20,10,431,464,8,9,7,482,1,21,5,5014,5015,5018,5029,5380,5419,5610,5655,
                 6001,7018,7013,7014,7015,7029,611,7380,7419,656]
    reduced_sp_df = sampling_point_df.drop_duplicates(
        subset=['station_eoi_code', 'component_code'], keep='last')
    reduced_sp_df = reduced_sp_df[reduced_sp_df['component_code'].isin(code_list)]
    time_series = get_timeseries()
    obp_list = ''
    observ = ''
    for index, row in reduced_sp_df.iterrows():
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
                               x[0].split(' ')[1] +
                                    #('00:00' if x[0].split(' ')[1] == '24:00' else x[0].split(' ')[1]) +
                               ', ' + str(x[1]), data['timeseries']))

            metric = data['metric']
            observ_time = data['time']
        except KeyError as k:
            ts = ''
            metric = ''
            # todo check if it is okay!!!
            print(row)
            observ_time = 'NaD'
        observ += get_pollutant_observing(row, ts, metric, observ_time) + '\n'

    return obp_list.rstrip(), observ.rstrip()


def get_timeseries():
    files = [('BENZOL','20'), ('CO','10'), ('ETILBENZOL','431'), ('MP XILOL','464'),
             ('NO2','8'),('NOX','9'), ('O3','7'), ('OXYLENE','482'), ('SO2','1'),
             ('TOLUOL','21'), ('PM10','5'),('PM10','5014'),('PM10','5015'),('PM10','5018'),
             ('PM10','5029'),('PM10','5380'),('PM10', '5419'),('PM10','5610'),
             ('PM10','5655'),('PM25','6001'),
             ]


    # with open('timeseries/mapping.txt') as f:
    #     mapping = dict(
    #         map(lambda x: x.split(':'), map(lambda y: y.rstrip(), f.readlines())))

    stations_df = pd.read_excel('Allomaskodok_e.xls')

    pollutants = {}

    for file,code in files:
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
            stations_df[stations_df['Station name'] == station]['EoI code'].values[0]

            #stations_df[stations_df['Állomásnév'] == station]['EoI állomáskód'].values[0]
            station_dict[st_code] = dict()
            station_dict[st_code]['metric'] = df[station][1]
            station_dict[st_code]['time'] = observ_time
            station_dict[st_code]['timeseries'] = [tuple(x) for x in current_df.values]

        pollutants[code] = station_dict

    ## riv
    riv_mapping = {'PM10':'5','PM2.5':'6001', 'AS':'7018','Cd':'7014','Ni':'7015',
                   'BaP':'7029','BaA':'611','Bfo':'7380','dBaA':'7419','I1P':'656'}
    print(riv_mapping.keys())
    riv_dfs = pd.read_excel('timeseries/riv_adatsorok2016.xls',
                            sheetname=list(riv_mapping.keys()), skiprows=1)
    for sheet, riv_df in riv_dfs.items():
        new_cols = ['timestamps']
        new_cols.extend(list(riv_df.columns)[1:])
        riv_df.columns = new_cols
        try:
            in_pollutants = pollutants[riv_mapping[sheet]]
            in_pollutants_flag = True
        except KeyError:
            in_pollutants = {}
            in_pollutants_flag = False
        for code in new_cols[1:]:
            dates = map(lambda x: str(x), list(riv_df['timestamps']))
            values = map(lambda x: str(x), list(riv_df[code]))
            timeseries = list(filter(lambda x: x[1] != "nan",
                                (map(lambda x, y: (x[6:8]+'.'+x[4:6]+'.'+x[:4]+' 24:00', y),
                                  dates, values))))
            new_entry = {'time': 'day', 'metric': 'ug/m3', 'timeseries': timeseries}
            in_pollutants[code] = new_entry
            pollutants[riv_mapping[sheet]] = in_pollutants


        print(sheet)

    ## add K-Puszta
    k_puszta = pd.read_excel('timeseries/kpuszta_no2so2pmo3_2016.xls', sheetname=None,
                             skiprows=7)
    k_puszta_mapping = {'NO2':'8','SO2':'1','PM10':'5','O3':'7'}
    for sheet,kp_df in k_puszta.items():
        kp_df = kp_df.drop(kp_df.columns[0], axis=1)
        kp_df.columns=['time', 'value']
        in_pollutants = pollutants[k_puszta_mapping[sheet]]
        if sheet == 'O3':
            time_cat = 'hour'
            timeseries = []
            for i, time_row in kp_df.iterrows():
                d,t = str(time_row['time']).split()
                y,m,d = d.split('-')
                timeseries.append((d+'.'+m+'.'+y+' '+t[:5], time_row['value']))
        else:
            time_cat = 'day'
            timeseries = []
            for i, time_row in kp_df.iterrows():
                d, t = str(time_row['time']).split()
                y, m, d = d.split('-')
                timeseries.append((d + '.' + m + '.' + y + ' 24:00' , time_row['value']))

        kpuszta_new = {'time': time_cat, 'metric': 'ug/m3', 'timeseries': timeseries}
        in_pollutants['HU0002R'] = kpuszta_new
        pollutants[k_puszta_mapping[sheet]] = in_pollutants

    ## add k-puszta from riv
    k_puszta_riv_df = pd.read_excel('timeseries/riv_adatsorok2016.xls',
                            sheetname='Ülepedés-K-puszta', skiprows=2)
    new_cols = ['timeseries', '7018', '611', '7029', '7380', '7014', '7419', '7013', '656',
                '7015']
    k_puszta_riv_df.columns = new_cols
    k_puszta_riv_times = ['31.01.2016 24:00', '29.02.2016 24:00', '31.03.2016 24:00',
                          '30.04.2016 24:00', '31.05.2016 24:00', '30.06.2016 24:00',
                          '31.07.2016 24:00', '31.08.2016 24:00', '30.09.2016 24:00',
                          '31.10.2016 24:00', '30.11.2016 24:00', '31.12.2016 24:00']
    k_puszta_riv_df = k_puszta_riv_df[np.isfinite(k_puszta_riv_df['timeseries'])]

    for code in new_cols[1:]:
        try:
            in_pollutants = pollutants[code]
        except KeyError:
            in_pollutants = {}
        timeseries = map(lambda x,y: (x,str(y)), k_puszta_riv_times,k_puszta_riv_df[code])
        timeseries = list(filter(lambda x: x[1] != 'nan', timeseries))
        in_pollutants['HU0002R'] = {'time': 'month', 'metric': 'ug/m3',
                                    'timeseries': timeseries}
        pollutants[code] = in_pollutants
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
    time_string_format = '%s-%s-%sT%s:%s:%s+01:00'
    # todo fix metric
    values = ''
    month_changer = '00'

    for ts in time_series:
        dt, f = ts.split(',')
        try:

            date_part, hour_part = dt.split(' ')
            year, month, day, hour, minute = (date_part[:4], date_part[4:6], date_part[6:8],
                                              hour_part.split(':')[0],
                                              hour_part.split(':')[1])
            end_time = time_string_format % (year, month, day, hour, minute, '00')
            # t = datetime.strptime(dt, "%Y%m%d %H:%M")
            if observ_time == 'hour':
                # start_time = t + timedelta(hours=1)
                start_hour = int(hour) - 1
                start_hour = '0' + str(start_hour) if start_hour < 10 else str(start_hour)
                start_time = time_string_format % (
                year, month, day, start_hour, minute, '00')
            elif observ_time == 'day':
                start_time = time_string_format % (year, month, day, '00', minute, '00')
            else:
                start_day = '01'
                start_hour = '01'
                start_time = time_string_format % (year, month, start_day,
                                                   start_hour, minute, '00')

            float(f)
            values += '%s,%s,%s,1,1@@' % (start_time, end_time, f.strip())
            # if month > month_changer:
            #     values += '\n'
            #     month_changer = month
        except ValueError:
            values += '%s,%s,-9999,1,-1@@' % (start_time, end_time)
            continue

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
    responsible_df = pd.read_sql_query(GET_RESPONSIBLE_QUERY.format(code_comb=CODE_COMB),
                                       con)
    #sampling_point_df = pd.read_excel('AQIS_HU_SamplingPoint-003_2016_mod.xls')

    obp_list_string, observations = get_obp_list()

    resp = read_structure(STRUCTURE_LOCATION.format(filename='resp.txt'))
    xml = read_structure(STRUCTURE_LOCATION.format(filename='header_e.txt'))

    resp = sub('\{localid\}', LOCALID, resp)
    resp = sub('\{part\}', PART, resp)
    resp_to_replace = get_fields_to_replace(resp, prefix='resp')

    responsible_string = ''

    # todo is a loop necessary in this case?
    for index, row in responsible_df.iterrows():
        actual_person = sub_all(resp_to_replace, row, resp)
        # todo hardcode
        actual_person = sub('\{obp_list\}', obp_list_string, actual_person)
        print(actual_person)
        responsible_string += actual_person

    xml = sub('\{responsible_xml_part\}', responsible_string, xml)
    xml = sub('\{eval_xml_part\}', observations.rstrip(), xml)
    xml = sub('\{localid\}', LOCALID, xml)
    xml = sub('\{year\}', YEAR, xml)
    xml = sub('\{part\}', PART, xml)
    save_xml(xml, filename='REP_D-' + LOCALID + '_E_001.xml')

    #save_xml(obp_list_string+observations, filename='E.xml')


if __name__ == '__main__':
    main("{Microsoft Access Driver (*.mdb, *.accdb)}", "C:\\olm.mdb")