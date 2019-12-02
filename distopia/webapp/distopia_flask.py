import sys
sys.path.append("../..")
import json
import numpy as np
import pickle as pkl

from flask import Flask, request, jsonify, render_template, abort
from distopia.app.agent import VoronoiAgent
from distopia.app.ros import RosBridge

with open("team_standardization_params.pkl", 'rb') as infile:
    st_mean,st_std = pkl.load(infile)

#globals:
sessions = 0
app = Flask(__name__)

json_metric_extractors = {

        # overall normalization plan: run one-hots in either direction to get rough bounds
        # then z-normalize and trim on edges
        # 'population' : lambda s,d : s.scalar_std,
        # standard deviation of each district's total populations (-1)
        # normalization: [0, single_district std]
        #'population': lambda s, d: np.std([dm['metrics']['population']['scalar_value'] for dm in d]),
        'population': lambda s, d: np.std([[m['scalar_value'] for m in dm['metrics'] if m['name'] == 'population'][0] for dm in d]),
        # mean of district margin of victories (-1)
        # normalization: [0,1]
        'pvi': lambda s, d: s['scalar_maximum'],
        # minimum compactness among districts (maximize the minimum compactness, penalize non-compactness) (+1)
        # normalization: [0,1]
        #'compactness': lambda s, d: np.min([dm['metrics']['compactness']['scalar_value'] for dm in d]),
        'compactness': lambda s, d: np.mean([[m['scalar_value'] for m in dm['metrics'] if m['name'] == 'compactness'][0] for dm in d]),
        # TODO: change compactness from min to avg
        # mean ratio of democrats over all voters in each district (could go either way)
        # normalization: [0,1]
        'projected_votes': lambda s, d: np.mean([[m['scalar_value']/m['scalar_maximum'] for m in dm['metrics'] if m['name'] == 'projected_votes'][0] for dm in d]),
        #[dm['metrics']['projected_votes']['scalar_value'] / dm['metrics']['projected_votes']['scalar_maximum'] for dm in d]),
        # std of ratio of nonminority to minority over districts
        # normalization: [0, ]
        'race': lambda s, d: np.std([[m['scalar_value'] for m in dm['metrics'] if m['name'] == 'race'][0] for dm in d]),
        #lambda s, d: np.std([dm['metrics']['race']['scalar_value'] / dm['metrics']['race']['scalar_maximum'] for dm in d]),
        # scalar value is std of counties within each district. we take a max (-1) to minimize variance within district (communities of interest)
        'income': lambda s, d: np.max([dm['metrics']['income']['scalar_value'] for dm in d]),
        # 'education' : lambda s,d : s.scalar_std,

        # maximum sized district (-1) to minimize difficulty of access
        # normalization [0,size of wisconsin]
        'area': lambda s, d: s['scalar_maximum']
    }
metrics = ['population','pvi','compactness']

def standardize(sequence):
    global st_mean
    global st_std
    return (sequence - st_mean)/st_std

@app.route("/")
def root():
    global sessions
    sessions += 1
    return render_template("index.html", session_id = sessions)


@app.route("/evaluate", methods=['POST'])
def evaluate():
    # only support POST
    if request.method == 'POST':
        d_agent = VoronoiAgent()
        d_agent.load_data()
        blocks = request.json["blocks"]
        counter = request.json["packet_count"]
        
        districts = d_agent.get_voronoi_districts(blocks)

        f_locs = [block for district in blocks.values() for block in district]
        f_ids = [k for k,v in blocks.items() for _ in range(len(v))]
        logical_ids = [k for k,v in blocks.items() for _ in range(len(v))]
        #state_metrics, districts = d_agent.compute_voronoi_metrics(districts)
        state_data,districts_data,blocks_data = RosBridge.make_computation_packet(f_locs,f_ids,logical_ids,districts,d_agent.metric_data.compute_district_metrics,d_agent.metric_data.create_state_metrics)
        if(len(districts_data) < 8):
            abort(400)
        for district in districts_data:
            if len(district['precincts']) < 1:
                abort(400)
        # only move on if we have a valid districting
        outcome_dict = dict()
        for state_metric in state_data:
            outcome_dict[state_metric['name']] = json_metric_extractors[state_metric['name']](state_metric,districts_data)
        outcomes = [outcome_dict[metric] for metric in metrics]
        count = counter + 1
        
        districts_obj = {
            'count': count, 'districts': districts_data,
            'metrics': state_data,
            'standardized_metrics': standardize(np.array(outcomes)).tolist()}
        return jsonify(districts_obj)

if __name__ == "__main__":
    app.run(host='0.0.0.0')