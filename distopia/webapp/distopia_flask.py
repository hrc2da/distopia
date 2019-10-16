from flask import Flask
from flask import request, jsonify
from distopia.app.agent import VoronoiAgent
from distopia.app.ros import RosBridge
import os
import json
app = Flask(__name__)

@app.route("/")
def root():
    return app.send_static_file("html/index.html")


@app.route("/evaluate", methods=['POST'])
def evaluate():
    # only support POST
    if request.method == 'POST':
        # this is pseudo-code, it may (likeley will) not run without some tweaks
        d_agent = VoronoiAgent()
        d_agent.load_data()
        blocks = request.json["blocks"]
        counter = request.json["packet_count"]
        #return jsonify("This is sparta!")
        districts = d_agent.get_voronoi_districts(blocks)


        f_locs = [block for district in blocks.values() for block in district]
        f_ids = [k for k,v in blocks.items() for _ in range(len(v))]
        logical_ids = [k for k,v in blocks.items() for _ in range(len(v))]
        #state_metrics, districts = d_agent.compute_voronoi_metrics(districts)
        state_data,districts_data,blocks_data = RosBridge.make_computation_packet(f_locs,f_ids,logical_ids,districts,d_agent.metric_data.compute_district_metrics,d_agent.metric_data.create_state_metrics)
        count = counter + 1
        districts_obj = {
            'count': count, 'districts': districts_data,
            'metrics': state_data}
        return jsonify(districts_obj)

        # fiducials_obj = {'count': count, 'fiducials': blocks_data}
        # blocks_topic.publish({'data': json.dumps(fiducials_obj)})

        # log_obj = {
        #     'districts': districts_obj,
        #     'fiducials': fiducials_obj,
        #     'utc_time': '{}'.format(datetime.datetime.utcnow())
        # }
        # return jsonify(log_obj) # this may choke as well

if __name__ == "__main__":
    app.run()