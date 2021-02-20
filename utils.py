import os
from operator import itemgetter

from src.bess import Bess
from src.load import LoadT1, LoadT2, LoadT3
from src.pod import Pod
from src.pontlab import Pontlab
from src.pv import PV
from src.wind import Wind
from src.storage import SimpleStorage
import json
import numpy as np

np.random.seed(10)
scale_factor = 1000  # 1000000

########################################################
uvax_old = {'uvaxid': 27,
            'plants': [
                {'id': 1041,
                 'name': 'PONTLAB_1',
                 'type': 'PONTLAB',
                 'baseline': None,
                 'description': ''},
                {'id': 1042,
                 'name': 'PONTLAB_2',
                 'type': 'PONTLAB',
                 'baseline': None,
                 'description': ''},
                {'id': 1043,
                 'name': 'LOAD_4',
                 'type': 'LOAD_T3',
                 'baseline': None,
                 'description': '[shift - loss]'},
                {'id': 1044,
                 'name': 'PV_1',
                 'type': 'PV',
                 'baseline': None,
                 'description': ''},
                {'id': 1045,
                 'name': 'PV_2',
                 'type': 'PV',
                 'baseline': None,
                 'description': ''},
                {'id': 1046,
                 'name': 'WIND_1',
                 'type': 'WIND',
                 'baseline': None,
                 'description': ''},
                {'id': 1047,
                 'name': 'WIND_2',
                 'type': 'WIND',
                 'baseline': None,
                 'description': ''},
                {'id': 1048,
                 'name': 'LOAD_1',
                 'type': 'LOAD_T2',
                 'baseline': None,
                 'description': '[no_shift - loss]'},
                {'id': 1049,
                 'name': 'LOAD_2',
                 'type': 'LOAD_T1',
                 'baseline': None,
                 'description': '[no_shift - no_loss]'},
                {'id': 1050,
                 'name': 'LOAD_3',
                 'type': 'LOAD_T3',
                 'baseline': None,
                 'description': '[shift - no_loss]'},
                {'id': 1051,
                 'name': 'BESS_1',
                 'type': 'BESS',
                 'baseline': None,
                 'description': ''},
                {'id': 1052,
                 'name': 'BESS_2',
                 'type': 'BESS',
                 'baseline': None,
                 'description': ''},
                {'id': 1000,
                 'name': 'CONF_1',
                 'type': 'MIX',
                 'description': '[ PV - WIND - SIMPLE_STORAGE - LOAD_T2 - LOADT3 ]',
                 'subplants': [
                     {'id': 1045,
                      'name': 'PV_2',
                      'type': 'PV',
                      'baseline': None},
                     {'id': 1046,
                      'name': 'WIND_1',
                      'type': 'WIND',
                      'baseline': None},
                     {'id': 1051,
                      'name': 'STORAGE_1',
                      'type': 'SIMPLE_STORAGE',
                      'baseline': None},
                     {'id': 1048,
                      'name': 'LOAD_1',
                      'type': 'LOAD_T2',
                      'baseline': None},
                     {'id': 1050,
                      'name': 'LOAD_3',
                      'type': 'LOAD_T3',
                      'baseline': None}
                 ]},
                {'id': 2000,
                 'name': 'CONF_2',
                 'type': 'MIX',
                 'description': '[ PV - WIND - SIMPLE_STORAGE - LOADT3 ]',
                 'subplants': [
                     {'id': 1044,
                      'name': 'PV_1',
                      'type': 'PV',
                      'baseline': None},
                     {'id': 1046,
                      'name': 'WIND_1',
                      'type': 'WIND',
                      'baseline': None},
                     {'id': 1052,
                      'name': 'STORAGE_2',
                      'type': 'SIMPLE_STORAGE',
                      'baseline': None},
                     {'id': 1043,
                      'name': 'LOAD_4',
                      'type': 'LOAD_T3',
                      'baseline': None},
                     {'id': 1050,
                      'name': 'LOAD_3',
                      'type': 'LOAD_T3',
                      'baseline': None}
                 ]}
            ]
            }

uvax = {'uvaxid': 27,
        'plants': [
            {'id': 1041,
             'name': 'PONTLAB_1',
             'type': 'PONTLAB',
             'description': '',
             'subplants': [
                 {'id': 1041,
                  'name': 'PONTLAB_1',
                  'type': 'PONTLAB',
                  'baseline': None}
             ]},
            {'id': 1042,
             'name': 'PONTLAB_2',
             'type': 'PONTLAB',
             'description': '',
             'subplants': [
                 {'id': 1042,
                  'name': 'PONTLAB_2',
                  'type': 'PONTLAB',
                  'baseline': None}
             ]},
            {'id': 1043,
             'name': 'LOAD_4',
             'type': 'LOAD_T3',
             'description': '[shift - loss]',
             'subplants': [
                 {'id': 1043,
                  'name': 'LOAD_4',
                  'type': 'LOAD_T3',
                  'baseline': None}
             ]},
            {'id': 1044,
             'name': 'PV_1',
             'type': 'PV',
             'description': '',
             'subplants': [
                 {'id': 1044,
                  'name': 'PV_1',
                  'type': 'PV',
                  'baseline': None}
             ]},
            {'id': 1045,
             'name': 'PV_2',
             'type': 'PV',
             'description': '',
             'subplants': [
                 {'id': 1045,
                  'name': 'PV_2',
                  'type': 'PV',
                  'baseline': None}
             ]},
            {'id': 1046,
             'name': 'WIND_1',
             'type': 'WIND',
             'description': '',
             'subplants': [
                 {'id': 1046,
                  'name': 'WIND_1',
                  'type': 'WIND',
                  'baseline': None}
             ]},
            {'id': 1047,
             'name': 'WIND_1',
             'type': 'WIND',
             'description': '',
             'subplants': [
                 {'id': 1047,
                  'name': 'WIND_1',
                  'type': 'WIND',
                  'baseline': None}
             ]},
            {'id': 1048,
             'name': 'LOAD_1',
             'type': 'LOAD_T2',
             'description': '[no_shift - loss]',
             'subplants': [
                 {'id': 1048,
                  'name': 'LOAD_1',
                  'type': 'LOAD_T2',
                  'baseline': None}
             ]},
            {'id': 1049,
             'name': 'LOAD_2',
             'type': 'LOAD_T1',
             'description': '[no_shift - no_loss]',
             'subplants': [
                 {'id': 1049,
                  'name': 'LOAD_2',
                  'type': 'LOAD_T1',
                  'baseline': None}
             ]},
            {'id': 1050,
             'name': 'LOAD_3',
             'type': 'LOAD_T3',
             'description': '[shift - no_loss]',
             'subplants': [
                 {'id': 1050,
                  'name': 'LOAD_3',
                  'type': 'LOAD_T3',
                  'baseline': None}
             ]},
            {'id': 1051,
             'name': 'BESS_1',
             'type': 'BESS',
             'description': '',
             'subplants': [
                 {'id': 1051,
                  'name': 'BESS_1',
                  'type': 'BESS',
                  'baseline': None}
             ]},
            {'id': 1052,
             'name': 'BESS_2',
             'type': 'BESS',
             'description': '',
             'subplants': [
                 {'id': 1052,
                  'name': 'BESS_2',
                  'type': 'BESS',
                  'baseline': None}
             ]},
            {'id': 1000,
             'name': 'CONF_1',
             'type': 'MIX',
             'description': '[ PV - WIND - SIMPLE_STORAGE - LOAD_T2 - LOADT3 ]',
             'subplants': [
                 {'id': 1045,
                  'name': 'PV_2',
                  'type': 'PV',
                  'baseline': None},
                 {'id': 1046,
                  'name': 'WIND_1',
                  'type': 'WIND',
                  'baseline': None},
                 {'id': 1051,
                  'name': 'STORAGE_1',
                  'type': 'SIMPLE_STORAGE',
                  'baseline': None},
                 {'id': 1048,
                  'name': 'LOAD_1',
                  'type': 'LOAD_T2',
                  'baseline': None},
                 {'id': 1050,
                  'name': 'LOAD_3',
                  'type': 'LOAD_T3',
                  'baseline': None}
             ]},
            {'id': 2000,
             'name': 'CONF_2',
             'type': 'MIX',
             'description': '[ PV - WIND - SIMPLE_STORAGE - LOADT3 ]',
             'subplants': [
                 {'id': 1044,
                  'name': 'PV_1',
                  'type': 'PV',
                  'baseline': None},
                 {'id': 1046,
                  'name': 'WIND_1',
                  'type': 'WIND',
                  'baseline': None},
                 {'id': 1052,
                  'name': 'STORAGE_2',
                  'type': 'SIMPLE_STORAGE',
                  'baseline': None},
                 {'id': 1043,
                  'name': 'LOAD_4',
                  'type': 'LOAD_T3',
                  'baseline': None},
                 {'id': 1050,
                  'name': 'LOAD_3',
                  'type': 'LOAD_T3',
                  'baseline': None}
             ]}
        ]
        }


########################################################
def serialize(obj):
    def check(o):
        for k, v in o.__dict__.items():
            try:
                _ = json.dumps(v)
                o.__dict__[k] = v
            except TypeError:
                o.__dict__[k] = str(v)
        return o

    return json.dumps(check(obj).__dict__, indent=2)


def subdict(d, ks):
    vals = []
    if len(ks) >= 1:
        vals = itemgetter(*ks)(d)
        if len(ks) == 1:
            vals = [vals]
    return dict(zip(ks, vals))


def searchbyId(id, dictlist):
    return [element for element in dictlist if element['id'] == id][0]


def load_baseline(tmp, date):
    list_of_files = os.listdir('Baseline')
    for f in list_of_files:
        if f.startswith(date) and f.__contains__(
                str(tmp['id'])):  # since its all type str you can simply use startswith
            tmp['baseline'] = [x / scale_factor for x in np.load('Baseline/' + f).tolist()]
            break
    return tmp['baseline']


def load_profile(element):
    profile = None
    if element['type'] == 'PV':
        profile = PV(np.array(element['baseline']))
    if element['type'] == 'WIND':
        profile = Wind(np.array(element['baseline']))
    if element['type'] == 'CHP':
        profile = None
    if element['type'] == 'BESS':
        profile = Bess(np.array(element['baseline']))
    if element['type'] == 'PONTLAB':
        profile = Pontlab(np.array(element['baseline']))
    if element['type'] == 'SIMPLE_STORAGE':
        profile = SimpleStorage(70)
    if element['type'] == 'LOAD_T1':
        profile = LoadT1(np.array(element['baseline']))  # [no_shift - no_loss]
    if element['type'] == 'LOAD_T2':
        profile = LoadT2(np.array(element['baseline']), list(range(0, 96)), 25)  # [no_shift - loss]
    if element['type'] == 'LOAD_T3':
        if element['name'] == 'LOAD_4':
            s = list(range(68, 88))  # [x for x in list(range(0, 96)) if x not in s],
            profile = LoadT3(np.array(element['baseline']), list(range(0, 96)), 15)  # [shift - loss]
        else:
            profile = LoadT3(np.array(element['baseline']), list(range(0, 96)), 0)  # [shift - no_loss]
    return profile


def init_aggregator(aggregator, content):
    for element in content['plants']:
        vars()[element['name']] = Pod(name=element['name'])
        # if element['type'] == 'MIX':
        for sub_el in element['subplants']:
            profile = load_profile(sub_el)
            if profile != None:
                vars()[element['name']].add_profile(profile)
        # else:
        #    profile = load_profile(element)
        #    if profile != None:
        #        vars()[element['name']].add_profile(profile)

        aggregator.add_pod(vars()[element['name']])
