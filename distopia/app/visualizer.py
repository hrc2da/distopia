# read a file and parse the designs
# pass the designs to distopia via fiducial_layout (json dumps'ed dict)

from os import listdir
from os.path import isfile, join
import json

class Visualizer:

    fn_path = "./distopia/logs/logs_to_viz/"

    files = []

    json = None

    is_agent = None

    has_episodes = None

    episodelen = None

    def __init__(self):
        self.files = [f for f in listdir(self.fn_path) if isfile(join(self.fn_path, f))]

    def retrieve_file(self, filenum):
        filename = self.files[filenum]
        with open(self.fn_path + filename) as logfile:
            self.json = json.load(logfile)

        self.is_agent = "agent" in filename
        self.has_episodes = "episodes" in filename

        fn_list = filename[:-5].split("_")
        if "episodelen" in filename:
            self.episodelen = int(fn_list[fn_list.index('episodelen')+1])
        return filename[:-5]

    def visualize_design(self, step):
        return self.get_agent_design(step) if self.is_agent else self.get_human_design(step)

    def get_agent_runlog(self, step, json_loc):
        for y in json_loc["run_log"]:
            if y["step_no"] == step:
                design = {i:[] for i in range(8)}
                for fid, coords in y["design"].items():
                    coordx, coordy= coords[0]
                    design[int(fid)].append([int(coordx), int(coordy)])
                return design

    def get_agent_design(self, step):
        if self.has_episodes:
            for x in self.json["episodes"]:
                if x["episode_no"] == (step // self.episodelen) + 1:
                    return self.get_agent_runlog(step, x)
        else:
            return self.get_agent_runlog(step, self.json)

    # TODO Skip over phases where human log enters Voronoi logging and fiducial movements are ignored
    '''
    def get_human_design(self, step):
        step = 0
        for row in self.json:
            design = {step: {i:[] for i in range(8)}}
            try:
                row_fiducials = row["fiducials"]["fiducials"]
            except KeyError:
                continue # found an object in JSON without fiducials field
            if len(row_fiducials) == 0:
                continue
            for rf in row_fiducials:
                fid = rf["fid_id"]
                design[fid].append([rf["x"],rf["y"]])
            step += 1
            #publisher.publish(roslibpy.Message({'data':json.dumps(design)}))
            #print("publishing {}".format(i))
        print(design)
        return design'''

    def get_human_design(self, step):
        i = 0
        for row in self.json:
            i += 1
            if i == step:
                design = {i:[] for i in range(8)}
                try:
                    row_fiducials = row["fiducials"]["fiducials"]
                except KeyError:
                    continue # found an object in JSON without fiducials field
                if len(row_fiducials) == 0:
                    continue
                for rf in row_fiducials:
                    fid = rf["fid_id"]
                    design[fid].append([rf["x"],rf["y"]])
                return design

