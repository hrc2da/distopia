from flask import Flask
from flask import request
import sys
sys.path.append("../..")
from distopia.app.agent import VoronoiAgent
import os
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
        blocks = request.json
        districts = d_agent.get_voronoi_districts(blocks)
        metrics = d_agent.compute_voronoi_metrics(districts)
        return jsonify((data,metrics)) # this may choke as well

if __name__ == "__main__":
    app.run()