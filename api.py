from flask import Flask, request
from src.aggregator import Aggregator
from src.local_optimization_result import LocalOptimizationResult
import json
import numpy as np
from flask import jsonify

from utils import subdict, searchbyId, load_baseline, init_aggregator, uvax

np.random.seed(10)

app = Flask(__name__)

"""
api functions
"""


@app.route('/')
@app.route('/api/get_plants', methods=['GET', 'POST'])
def get_plants():
    if request.method == 'GET':
        mask = ['id', 'name', 'description']
        plants = {'data': []}
        [plants['data'].append(subdict(i, mask)) for i in uvax['plants']]
        return jsonify(plants)


@app.route('/api/get_baselines', methods=['GET', 'POST'])
def get_baselines_from_config():
    if request.method == 'GET':
        config = json.loads(request.get_json())
        plants = {'data': [],
                  'date': '2020-11-05'  # config['date']
                  }

        for x in config['plants']:
            el = searchbyId(x['id'], uvax['plants']).copy()
            el['name'] = x['name']
            # if el['type'] == 'MIX':
            for sub_el in el['subplants']:
                if sub_el['type'] != 'SIMPLE_STORAGE':
                    sub_el['baseline'] = load_baseline(sub_el, plants['date'])
            # else:
            #    el['baseline'] = load_baseline(el, plants['date'])
            el['quantity'] = x['quantity']
            plants['data'].append(el)

        return jsonify(plants)


@app.route('/api/local_optimization', methods=['GET', 'POST'])
def local_optimization():
    content = request.json

    aggregator = Aggregator()
    init_aggregator(aggregator, content)

    aggregator.resolve_pods_multiprocessing()
    local_opt_result = LocalOptimizationResult(date=content['date'])
    local_opt_result.populate(aggregator.pods)

    return jsonify(local_opt_result.__dict__)


@app.route('/api/aggregate', methods=['GET', 'POST'])
def aggregate():
    content = request.json
    local_opt_result = LocalOptimizationResult(**json.loads(content))
    aggregator = Aggregator()
    aggregator.set_local_optimization_result(local_opt_result)
    result = aggregator.aggregate()

    return jsonify(result)


@app.route('/api/optimize_and_aggregate', methods=['GET', 'POST'])
def optimize_and_aggregate():
    content = request.json
    aggregator = Aggregator()
    init_aggregator(aggregator, content)

    result = aggregator.resolve_pods_and_aggregate()
    return jsonify(result)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=4996)
