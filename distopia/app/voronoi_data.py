"""
Census and Election Data
============================

Some of our data sources:

- https://elections.wi.gov/elections-voting/statistics
- https://github.com/nvkelso/election-geodata/issues/2
- https://doi.org/10.7910/DVN/NH5S2I
- https://hub.arcgis.com/datasets/f0532acbe3304e20a11dbd598c5654f7_0
- https://elections.wi.gov/elections-voting/results/2016/fall-general
- https://elections.wi.gov/sites/default/files/11.4.14%20Election%20Results-all%20offices-w%20x%20w%20report.pdf
- https://www.cityofmadison.com/planning/unit_planning/map_aldermanic/ald_dist_8x10.pdf
- https://data-wi-dnr.opendata.arcgis.com/datasets/county-boundaries-24k
- https://www.arcgis.com/home/item.html?id=62d5782482cd45f2898fe7e3d4272c10

We assume that in wisconsin, wards are precincts.
"""

import os.path
import numpy as np
import math
import json
import zipfile
import csv

import distopia
from distopia.precinct.metrics import PrecinctHistogram
from distopia.district.metrics import DistrictHistogramAggregateMetric, \
    DistrictScalarMetric
from distopia.metrics import MeanStateMetric

__all__ = ('GeoDataCounty', 'GeoDataPrecinct2017', 'MetricData')


class GeoDataBase(object):
    """Represents the census data and the polygons associated with the data.
    """

    records = None

    shapes = None

    polygons = None

    fields = None

    source_coordinates = ''

    source_coordinates_landmark = ''

    target_coordinates = ''

    dataset_name = ''

    screen_size = (1920, 1080)

    containing_rect = None
    """4-tuple describing the rectangle containing all the polygons.
    
    ``(min_x, min_y, max_x, max_y)``
    """

    landmarks = []

    metric_data = None

    @property
    def data_path(self):
        return os.path.join(
            os.path.dirname(distopia.__file__), 'data', self.dataset_name)

    def load_data(self):
        """Loads the data from file.
        """
        import shapefile
        data_path = os.path.join(self.data_path, self.dataset_name)
        shp = shapefile.Reader(data_path)

        self.fields = fields = [
            f[0] for f in shp.fields if not isinstance(f, tuple)]
        self.shapes = list(shp.shapes())
        self.records = records = list(shp.records())

        assert len(records)
        assert len(records[0]) == len(fields)

    def load_landmarks(self):
        from pyproj import Proj, transform
        src, target = self.source_coordinates_landmark, self.target_coordinates
        if not src or not target:
            trans = lambda _0, _1, lon, lat: (lon, lat)
            crs_src = crs_target = None
        else:
            trans = transform
            crs_src = Proj(init=src)
            crs_target = Proj(init=target)

        data_path = os.path.join(self.data_path, 'landmarks.csv')
        landmarks = self.landmarks = []
        if not os.path.exists(data_path):
            return

        min_x, min_y, ratio = self.get_scale_factors()
        with open(data_path) as fh:
            it = csv.reader(fh)
            next(it)
            for row in it:
                x, y, size = row[:3]
                name = row[3] if len(row) > 3 else ''
                label = row[4] if len(row) > 4 else ''
                x, y = trans(crs_src, crs_target, float(y), float(x))

                x = (x - min_x) * ratio
                y = (y - min_y) * ratio

                landmarks.append((x, y, float(size), name, label))

    def load_npz_data(self):
        data = np.load(os.path.join(self.data_path, 'data.npz'))
        self.fields = data['fields'].tolist()
        self.polygons = data['polygons'].tolist()
        self.records = data['records'].tolist()

    def dump_data_to_disk(self):
        with zipfile.ZipFile(
                os.path.join(self.data_path, 'json_data.zip'), 'w',
                compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(
                'fields.json',
                json.dumps(self.fields, indent=2, sort_keys=True))

            zip_file.writestr(
                'records.json',
                json.dumps(self.records, indent=2, sort_keys=True))

            polygons = [[polygon.tolist() for polygon in shape_polygons] for
                        shape_polygons in self.polygons]
            zip_file.writestr(
                'polygons.json',
                json.dumps(polygons, indent=2, sort_keys=True))

        str_max = 0
        int_max = 0
        field_types = [
            'int' if isinstance(r, int) else
            ('str' if isinstance(r, str) else 'float') for
            r in self.records[0]]

        for row in self.records:
            for type_, val in zip(field_types, row):
                if type_ == 'str':
                    str_max = max(str_max, len(val))
                elif type_ == 'int':
                    int_max = max(int_max, val)

        for dtype in [np.uint8, np.uint16, np.uint32, np.uint64]:
            if int_max <= dtype(-1):
                break
        else:
            raise Exception('{} is really big!'.format(int_max))

        types = []
        for type_, name in zip(field_types, self.fields):
            if type_ == 'str':
                types.append((name, np.unicode_, str_max + 6))
            elif type_ == 'int':
                types.append((name, dtype))
            else:
                types.append((name, np.double))
        records = np.array(
            [tuple(r) for r in self.records], dtype=np.dtype(types))

        np.savez_compressed(
            os.path.join(self.data_path, 'data.npz'),
            records=records, polygons=self.polygons, fields=self.fields)

    def generate_polygons(self):
        """Converts the shapes in the data into a list of closed polygons,
        described by their vertices.
        """
        from pyproj import Proj, transform
        src, target = self.source_coordinates, self.target_coordinates
        if not src or not target:
            trans = lambda _0, _1, lon, lat: (lon, lat)
            crs_src = crs_target = None
        else:
            trans = transform
            crs_src = Proj(init=src)
            crs_target = Proj(init=target)

        self.polygons = polygons = []
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for record, shape in zip(self.records, self.shapes):
            if len(shape.parts) == 1:
                arr = np.array(
                    [trans(crs_src, crs_target, lon, lat) for
                     lon, lat in shape.points])

                max_x = max(max_x, np.max(arr[:, 0]))
                max_y = max(max_y, np.max(arr[:, 1]))
                min_x = min(min_x, np.min(arr[:, 0]))
                min_y = min(min_y, np.min(arr[:, 1]))

                poly_list = [arr, ]
            else:
                poly_list = []
                for i, s in enumerate(shape.parts):
                    if i < len(shape.parts) - 1:
                        e = shape.parts[i + 1] - 1
                    else:
                        e = len(shape.points)

                    arr = np.array([
                        trans(crs_src, crs_target, lon, lat) for
                        lon, lat in shape.points[s:e + 1]])

                    max_x = max(max_x, np.max(arr[:, 0]))
                    max_y = max(max_y, np.max(arr[:, 1]))
                    min_x = min(min_x, np.min(arr[:, 0]))
                    min_y = min(min_y, np.min(arr[:, 1]))

                    poly_list.append(arr)
            polygons.append(poly_list)
        self.containing_rect = min_x, min_y, max_x, max_y

    def smooth_vertices(self, tolerance=2):
        for shape_polygons in self.polygons:
            for i, polygon in enumerate(shape_polygons):
                assert len(polygon)
                x0, y0 = polygon[0]
                filtered_poly = [(x0, y0)]

                for x1, y1 in polygon[1:]:
                    if math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2) < tolerance:
                        continue

                    filtered_poly.append((x1, y1))
                    x0, y0 = x1, y1

                if len(filtered_poly) == 1:
                    filtered_poly.append(filtered_poly[0])
                    filtered_poly.append(filtered_poly[0])
                elif len(filtered_poly) == 2:
                    filtered_poly.append(filtered_poly[1])

                shape_polygons[i] = np.array(filtered_poly)

    def get_scale_factors(self):
        if self.screen_size is None:
            raise TypeError('A screen size was not given')

        min_x, min_y, max_x, max_y = self.containing_rect
        width, height = map(float, self.screen_size)
        # normalize to the screen size
        max_x, max_y = math.ceil(max_x), math.ceil(max_y)
        min_x, min_y = math.floor(min_x), math.floor(min_y)
        x_ratio = width / (max_x - min_x)
        y_ratio = height / (max_y - min_y)
        ratio = min(x_ratio, y_ratio)

        return min_x, min_y, ratio

    def scale_to_screen(self):
        """Scales the polygons to the screen size.
        """
        min_x, min_y, ratio = self.get_scale_factors()

        for precinct_polygons in self.polygons:
            for polygon in precinct_polygons:
                polygon[:, 0] -= min_x
                polygon[:, 0] *= ratio
                polygon[:, 1] -= min_y
                polygon[:, 1] *= ratio

    def set_precinct_adjacency(self, precincts):
        fname = os.path.join(self.data_path, 'adjacency.json')
        if not os.path.exists(fname):
            return False

        with open(fname, 'r') as fh:
            precinct_adj = json.load(fh)

        for i, neighbours in precinct_adj.items():
            precincts[int(i)].neighbours = [precincts[p] for p in neighbours]
        return True

    def load_metrics(self, metrics, precincts):
        raise NotImplementedError

    def get_ordered_record_names(self):
        raise NotImplementedError


class GeoDataCounty(GeoDataBase):

    source_coordinates = 'epsg:3071'

    source_coordinates_landmark = 'epsg:4326'

    target_coordinates = 'epsg:3857'

    dataset_name = 'County_Boundaries_24K'

    def load_metrics(self, metrics, precincts):
        names = {'Saint Croix': 'St. Croix'}
        root = os.path.join(self.data_path, 'aggregate')

        metric_data = self.metric_data = MetricData(
            root_path=root, metrics=metrics, precinct_names_map=names,
            precincts=precincts)
        return metric_data

    def get_ordered_record_names(self):
        return [record[3] for record in self.records]


class GeoDataPrecinct2017(GeoDataBase):

    source_coordinates = ''

    source_coordinates_landmark = ''

    target_coordinates = ''

    dataset_name = 'WI_Election_Data_with_2017_Wards'

    def load_metrics(self, metrics, precincts):
        names = {'Saint Croix': 'St. Croix'}
        root = os.path.join(self.data_path, 'aggregate')

        metric_data = self.metric_data = MetricData(
            root_path=root, metrics=metrics, precinct_names_map=names,
            precincts=precincts)
        return metric_data

    def get_ordered_record_names(self):
        return list(map(str, range(1, len(self.records) + 1)))


class MetricData(object):

    root_path = ''

    precinct_names_map = {}

    metrics = []

    precincts = []

    def __init__(self, root_path, precinct_names_map, metrics, precincts,
                 **kwargs):
        super(MetricData, self).__init__(**kwargs)
        self.root_path = root_path
        self.precinct_names_map = precinct_names_map
        self.metrics = metrics
        self.precincts = precincts

        self.load_precinct_data()

    def load_precinct_data(self):
        root = self.root_path
        for metric_name in self.metrics:
            if metric_name == 'pvi':
                if 'projected_votes' not in self.metrics:
                    raise ValueError(
                        'Cannot compute PVI without projected_votes')
                continue

            fname = os.path.join(root, '{}.csv'.format(metric_name))
            with open(fname) as fh:
                reader = csv.reader(fh)
                header = next(reader)[1:]

                data = {}
                for row in reader:
                    data[row[0]] = list(map(float, row[1:]))

            f = getattr(self, 'load_{}_precinct_data'.format(metric_name), None)
            if f is None:
                self._precinct_histogram(metric_name, header, data)
            else:
                f(header, data)

    def _precinct_histogram(self, metric_name, header, data):
        names = self.precinct_names_map
        for precinct in self.precincts:
            precinct_name = names.get(precinct.name, precinct.name)
            precinct_data = data[precinct_name]
            precinct.metrics[metric_name] = PrecinctHistogram(
                name=metric_name, labels=header[2:], data=precinct_data[2:],
                scalar_label=header[0], scalar_maximum=precinct_data[1],
                scalar_value=precinct_data[0])

    def compute_district_metrics(self, districts):
        for metric_name in self.metrics:
            if metric_name == 'pvi':
                continue

            fn_name = 'compute_scalar_sum'
            if metric_name in ('age', 'income'):
                fn_name = 'compute_scalar_mean'

            for district in districts:
                metric = district.metrics[metric_name] = \
                    DistrictHistogramAggregateMetric(
                        district=district, name=metric_name)
                metric.compute()
                getattr(metric, fn_name)()

        if 'pvi' in self.metrics:
            for district in districts:
                metric = district.metrics['pvi'] = DistrictScalarMetric(
                    district=district, name='pvi')
                vote1, vote2 = district.metrics['projected_votes'].data

                if vote1 < vote2:
                    vote1, vote2 = vote2, vote1
                metric.set_value(vote1 - (vote1 + vote2) / 2., 'pvi')

        if 'compactness' in self.metrics:
            for district in districts:
                metric = district.metrics['compactness'] = \
                    DistrictScalarMetric(district=district, name='compactness')

                if not district.boundary or district.collider is None:
                    metric.set_value(-1., 'compactness')
                    continue

                perimeter = len(district.boundary) / 2.
                area = district.collider.get_area()
                r = perimeter / (2 * math.pi)
                circle_area = math.pi * r ** 2

                metric.set_value(area / circle_area, 'compactness')

    def create_state_metrics(self, districts):
        metrics = []
        for metric_name in self.metrics:
            m = MeanStateMetric(name=metric_name, districts=districts)
            m.compute()
            metrics.append(m)
        return m
