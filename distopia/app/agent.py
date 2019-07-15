import os
import json
import numpy as np
import csv

import distopia
from distopia.app.voronoi_data import GeoDataCounty
from distopia.precinct import Precinct
from distopia.mapping.voronoi import VoronoiMapping
from distopia.precinct.metrics import PrecinctHistogram#, PrecinctScalar
from distopia.district.metrics import DistrictHistogramAggregateMetric#, \
    #DistrictScalarAggregateMetric
from distopia.metrics import MeanStateMetric, StdStateMetric


class VoronoiAgent(object):

    voronoi_mapping = None

    use_county_dataset = True

    geo_data = None

    precincts = []

    screen_size = (1900, 800)

    metrics = ['demographics', ]

    data_loader = None

    def create_district_metrics(self, districts):
        for district in districts:
            for name in self.metrics:
                # if name == 'income':
                #     continue
                district.metrics[name] = \
                    DistrictHistogramAggregateMetric(
                        district=district, name=name)

            # name = 'income'
            # if name in self.metrics:
            #     district.metrics[name] = \
            #         DistrictScalarAggregateMetric(district=district, name=name)

    def load_precinct_metrics(self):
        assert self.use_county_dataset

        geo_data = self.geo_data
        names = set(r[3] for r in geo_data.records)
        names = {v: v for v in names}
        names['Saint Croix'] = 'St. Croix'

        root = os.path.join(
            os.path.dirname(distopia.__file__), 'data', 'County_Boundaries_24K', 'aggregate')
        for name in self.metrics:
            # if name == 'income':
            #     continue

            fname = os.path.join(root, '{}.csv'.format(name))
            with open(fname) as fh:
                reader = csv.reader(fh)
                header = next(reader)[1:]
                scalar_header = header[0]
                scalar_max_header = header[1]
                header = header[2:]

                # csv order is label, scalar, total, then hist
                data = {}
                scalars = {}
                scalar_maxes = {}
                for row in reader:
                    scalars[row[0]] = float(row[1])
                    scalar_maxes[row[0]] = float(row[2])
                    data[row[0]] = list(map(float, row[3:]))

            for precinct, record in zip(self.precincts, geo_data.records):
                precinct_name = names[record[3]]
                precinct.metrics[name] = PrecinctHistogram(
                    name=name, labels=header, data=data[precinct_name], 
                    scalar_value=scalars[precinct_name], scalar_maximum=scalar_maxes[precinct_name],
                    scalar_label=scalar_header)

        # name = 'income'
        # if name in self.metrics:
        #     fname = os.path.join(root, '{}.csv'.format(name))
        #     with open(fname) as fh:
        #         reader = csv.reader(fh)
        #         _ = next(reader)[1:]  # header

        #         data = {}
        #         for row in reader:
        #             data[row[0]] = float(row[1])

        #     for precinct, record in zip(self.precincts, geo_data.records):
        #         precinct_name = names[record[3]]
        #         precinct.metrics[name] = PrecinctScalar(
        #             name=name, value=data[precinct_name])

    def load_precinct_adjacency(self):
        assert self.use_county_dataset
        fname = os.path.join(
            os.path.dirname(distopia.__file__), 'data', 'County_Boundaries_24K', 'adjacency.json')

        with open(fname, 'r') as fh:
            counties = json.load(fh)

        precincts = self.precincts
        for i, neighbours in counties.items():
            precincts[int(i)].neighbours = [precincts[p] for p in neighbours]

    def create_state_metrics(self, districts):
        state_mets = []
        for name in self.metrics:
            state_mets.append(MeanStateMetric(name,districts))
        return state_mets

    def create_voronoi(self):
        """Loads and initializes all the data and voronoi mapping.
        """
        self.geo_data = geo_data = GeoDataCounty()
        if self.use_county_dataset:
            geo_data.dataset_name = 'County_Boundaries_24K'
        else:
            geo_data.dataset_name = 'WI_Election_Data_with_2017_Wards'
            geo_data.source_coordinates = ''

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

        for i, (record, polygons) in enumerate(
                zip(geo_data.records, geo_data.polygons)):
            precinct = Precinct(
                name=str(record[0]), boundary=polygons[0].reshape(-1).tolist(),
                identity=i, location=polygons[0].mean(axis=0).tolist())
            precincts.append(precinct)

        vor.set_precincts(precincts)

    def load_config(self):
        fname = os.path.join(
            os.path.dirname(distopia.__file__), 'data', 'config.json')
        with open(fname, 'r') as fp:
            for key, val in json.load(fp).items():
                setattr(self, key, val)
        if self.metrics:
            self.metrics.sort() # just paranoia but fix the metric order

    def load_data(self):
        """Builds the GUI.
        """
        self.load_config()
        self.create_voronoi()
        self.load_precinct_metrics()
        self.load_precinct_adjacency()

    def get_voronoi_districts(self, fiducials):
        vor = self.voronoi_mapping
        keys = []
        for fid_id, locations in fiducials.items():
            for location in locations:
                keys.append(vor.add_fiducial(location, fid_id))
        try:
            districts = vor.apply_voronoi()
        finally:
            for key in keys:
                vor.remove_fiducial(key)

        if not districts:
            return []
        else:
            return districts

    def compute_voronoi_metrics(self, districts):
        
        if not districts:
            return [], []


        self.create_district_metrics(districts)
        
        # we must calculate the district metrics first so we can use them for the state metrics
        district_metrics = {}
        for district in districts:
            district.compute_metrics()
            district.compute_scalar_sum()
            district_metrics[district.identity] = list(district.metrics.values())

        # calculate the state metrics using the district metrics
        state_mets = self.create_state_metrics(districts)
        state_metrics = []
        for metric in state_mets:
            metric.compute()
            state_metrics.append(metric)



        return state_metrics, district_metrics


if __name__ == '__main__':
    import time
    import random
    agent = VoronoiAgent()
    agent.load_data()
    print('data loaded')

    w, h = agent.screen_size
    t = [0, ] * 1
    for i in range(len(t)):
        ts = time.clock()
        fids = {i: [(random.random() * w, random.random() * h)] for i in range(4)}
        print(fids)
        try:
            state_v,district_v = agent.compute_voronoi_metrics(fids)
            for d in district_v:
                print("District {}:\n".format(d))
                for stat in district_v[d]:
                    print("\t{}\n".format(stat.get_data()))
            # for met in state_v:
            #     print(met.get_data())
        except Exception:
            print("Couldn't compute Vornoi for {}".format(fids))
            raise
        t[i] = time.clock() - ts
    print('done in {} - {}'.format(min(t), max(t)))
