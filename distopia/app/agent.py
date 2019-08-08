import os
import json
import numpy as np
import csv

import distopia
from distopia.app.voronoi_data import GeoDataCounty, GeoDataPrecinct2017
from distopia.precinct import Precinct
from distopia.mapping.voronoi import VoronoiMapping



class VoronoiAgent(object):

    voronoi_mapping = None

    use_county_dataset = True

    geo_data = None

    precincts = []

    screen_size = (1900, 800)

    metrics = ['demographics', ]

    data_loader = None

    metric_data = None

    def create_voronoi(self):
        """Loads and initializes all the data and voronoi mapping.
        """
        if self.use_county_dataset:
            geo_data = self.geo_data = GeoDataCounty()
            geo_data.containing_rect = self.county_containing_rect
        else:
            geo_data = self.geo_data = GeoDataPrecinct2017()
            geo_data.containing_rect = self.precinct_2017_containing_rect

        geo_data.screen_size = self.screen_size
        try:
            geo_data.load_npz_data()
        except FileNotFoundError:
            geo_data.load_data()
            geo_data.generate_polygons()
            geo_data.scale_to_screen()
            geo_data.smooth_vertices()

        self.voronoi_mapping = vor = VoronoiMapping()
        vor.screen_size = self.screen_size
        self.precincts = precincts = []

        for i, (name, polygons) in enumerate(
                zip(geo_data.get_ordered_record_names(), geo_data.polygons)):
            precinct = Precinct(
                name=name, boundary=polygons[0].reshape(-1).tolist(),
                identity=i, location=polygons[0].mean(axis=0).tolist())
            precincts.append(precinct)

        vor.set_precincts(precincts)

    def load_config(self):
        fname = os.path.join(
            os.path.dirname(distopia.__file__), 'data', 'config.json')
        with open(fname, 'r') as fp:
            for key, val in json.load(fp).items():
                setattr(self, key, val)

    def load_data(self):
        """Builds the GUI.
        """
        self.load_config()
        self.create_voronoi()
        self.metric_data = self.geo_data.load_metrics(
            self.metrics, self.precincts)
        self.geo_data.set_precinct_adjacency(self.precincts)

    def get_voronoi_districts(self, fiducials):
        vor = self.voronoi_mapping
        keys = []
        for fid_id, locations in fiducials.items():
            for location in locations:
                keys.append(vor.add_fiducial(location, fid_id))
        try:
            districts = vor.apply_voronoi()
        except Exception as e:
            print("Voronoi failed, {}".format(e))
            raise
        finally:
            for key in keys:
                vor.remove_fiducial(key)

        return districts

    def compute_voronoi_metrics(self, districts):
        if not districts:
            return [], []
        self.metric_data.compute_district_metrics(districts)
        state_metrics = self.metric_data.create_state_metrics(districts)

        return state_metrics, districts


if __name__ == '__main__':
    import time
    import random
    agent = VoronoiAgent()
    agent.load_data()
    print('data loaded')

    w, h = agent.screen_size
    t = [0, ] * 100
    for i in range(len(t)):
        ts = time.clock()
        fids = {i: [(random.random() * w, random.random() * h)] for i in range(8)}
        print(fids)
        try:
            districts = agent.get_voronoi_districts(fids)
            state_metrics, districts = agent.compute_voronoi_metrics(districts)
            assert len(districts) == len(fids)
            for district in districts:
                print("District {}:".format(district))
            #     for name, metric in district.metrics.items():
            #         print("{}\t{}".format(name, metric.get_data()))
            # for metric in state_metrics:
            #     print("\n\n{}\t{}".format(metric.name, metric.get_data()))
        except Exception:
            print("Couldn't compute Vornoi for {}".format(fids))
            # raise
        t[i] = time.clock() - ts
    print('done in {} - {}'.format(min(t), max(t)))
