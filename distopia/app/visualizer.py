"""
Log Visualizer
===============

Reads logs and provides requested designs given a step.
"""

from os import listdir
from os.path import isfile, join
import json

__all__ = ('Visualizer')

class Visualizer:

    ln_path = "./distopia/logs/logs_to_viz/"

    logs = []

    json = None

    is_agent = None

    has_episodes = None

    episodelen = None

    def __init__(self):
        self.logs = [l for l in listdir(self.ln_path) if isfile(join(self.ln_path, l))]

    def filter_human_json(self):
        """
        Returns a filtered JSON that excludes steps in which there 
        are < 4 fiducials placed or there are control messages 
        (results in gaps during human visualization)
        """
        filtered_json = []
        for i in range(len(self.json)):
            json_row = self.get_human_design(i)
            if json_row:
                filtered_json.append(json_row)
        return filtered_json
    
    def prepare_log(self, lognum):
        """
        Returns the log name in the lognum position within the 
        directory at ln_path after preparing that log for 
        visualization
        """
        log_name = self.logs[lognum]
        with open(self.ln_path + log_name) as log:
            self.json = json.load(log)

        self.is_agent = "agent" in log_name
        if not self.is_agent:
            print(self.json[4])
            self.json = self.filter_human_json()
            print(self.json[4])
        self.has_episodes = "episodes" in log_name

        ln_list = log_name[:-5].split("_")
        if "episodelen" in log_name:
            self.episodelen = int(ln_list[ln_list.index('episodelen')+1])
        return log_name[:-5]

    def visualize_design(self, step):
        """
        Returns a design of fiducials and their locations at a 
        given step foreither an agent or a human, based on the 
        log name
        """
        return self.get_agent_design(step) if self.is_agent else self.get_filtered_human_design(step)

    def get_agent_runlog(self, step, json_loc):
        """
        Returns a design of fiducials and their locations at a 
        given step using json_loc, the json portion similar to 
        agents with and without episodes
        """
        for y in json_loc["run_log"]:
            if y["step_no"] == step:
                design = {i:[] for i in range(8)}
                for fid, coords in y["design"].items():
                    coordx, coordy= coords[0]
                    design[int(fid)].append([int(coordx), int(coordy)])
                return design

    def get_agent_design(self, step):
        """
        Returns a design of fiducials and their locations at a 
        given step for an agent with episodes or without, based 
        on the log name
        """
        if self.has_episodes:
            for x in self.json["episodes"]:
                if x["episode_no"] == (step // self.episodelen) + 1:
                    return self.get_agent_runlog(step, x)
        else:
            return self.get_agent_runlog(step, self.json)
    
    def get_filtered_human_design(self, step):
        """
        Returns a design of fiducials and their locations at a
        given step for a human from a filtered JSON
        """
        try:
            return self.json[step]
        except:
            return None

    def get_human_design(self, step):
        """
        Returns a design of fiducials and their locations at a 
        given step for a human
        """
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
    
    def get_max_steps(self):
        """
        Returns the max steps for the current log
        """
        return len(self.json)

    def get_log_count(self):
        """
        Returns the amount of logs inside of the directory of ln_path
        """
        return len(self.logs)

