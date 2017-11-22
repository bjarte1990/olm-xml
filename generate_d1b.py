from time import strftime, gmtime
from generator import *
import re

NAMESPACE = 'HU.OMSZ.AQ'
STRUCTURE_PATH = 'structures/d1b/'
STRUCTURE_LOCATION = 'structures/d1b/{filename}'

YEAR = "2016"
DATESTRING = strftime("%Y%m%d", gmtime())
LOCALID = "HU_OMSZ_" + DATESTRING
PART = "D1b"

MODEL_STRING = '<aqd:content xlink:href="{NAMESPACE}/{id}"/>'

#open files for missing models
def get_are_for_models(filename):
    with open(filename) as f:
        model_list = f.readlines()
    model_list = list(map(lambda x: x.rstrip(), model_list))
    return model_list


def get_model_list_string(model_list):
    model_list_string = ''
    print(model_list)
    #cp_nums = set(map(lambda x: re.findall('([0-9A-Z]+_\d{5})_', x)[0], model_list))
    cp_nums = set(map(lambda x: 'MDL-OBJ_EST_' + re.findall('_(\d{5})_', x)[0], model_list))
    for cp_num in cp_nums:
        local_id =  cp_num
        model_list_string += MODEL_STRING.format(NAMESPACE=NAMESPACE, id=local_id) + '\n'
    return cp_nums,model_list_string

def generate_models_from_local_ids(local_ids):
    structure = read_structure(STRUCTURE_LOCATION.format(filename='structure.txt'))
    model_structures = ''
    for local_id in local_ids:
        cp_num = local_id.split('_')[-1]
        actual_structure = re.sub('\{id\}', local_id, structure)
        actual_structure = re.sub('\{NAMESPACE\}', NAMESPACE, actual_structure)
        actual_structure = re.sub('\{CP_NUM\}', cp_num, actual_structure)
        model_structures += actual_structure + '\n'

    return model_structures

model_list = get_are_for_models(STRUCTURE_LOCATION.format(filename='models.txt'))

cp_nums, model_list_string = get_model_list_string(model_list)

model_structures = generate_models_from_local_ids(cp_nums)

header = read_structure(STRUCTURE_LOCATION.format(filename='header.txt'))

model_process = read_structure(STRUCTURE_LOCATION.format(
    filename='model_process_structure.txt'))
model_area = read_structure(STRUCTURE_LOCATION.format(
    filename='model_area_structure.txt'))

header = re.sub('\{all_list\}', model_list_string, header)
header = re.sub('\{model_process\}', model_process, header)
header = re.sub('\{model\}', model_structures, header)
header = re.sub('\{model_area\}', model_area, header)

save_xml(header, filename='REP_D-' + LOCALID + '_D1b_001.xml')
