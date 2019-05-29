"""
States Metrics
=================

Defines metrics that summarize the state based on the districts.
"""
from distopia.district.metrics import DistrictAggregateMetric
import numpy as np

__all__ = ('StateMetric', )


class StateMetric(object):
    """Metrics used across :class:`distopia.district.District`.
    """

    name = ''
    """A globally unique metric name that describes the metric.
    """

    districts = []

    scalar_value = 0

    scalar_maximum = 0

    scalar_label = ''

    data = []

    labels = []

    def __init__(self, name, districts, **kwargs):
        super(StateMetric, self).__init__(**kwargs)
        self.name = name
        self.districts = districts

    def compute(self):
        raise NotImplementedError

    def get_data(self):
        raise NotImplementedError


class MeanStateMetric(StateMetric):

    def compute(self):
        name = self.name
        metrics = [district.metrics[name] for district in self.districts]
        assert all((isinstance(m, DistrictAggregateMetric) for m in metrics))
        if not metrics:
            self.scalar_value = 0
            self.scalar_maximum = 0
        else:
            self.scalar_value = sum(
                (m.scalar_value for m in metrics)) / float(len(metrics))
            self.scalar_maximum = max((m.scalar_maximum for m in metrics))
        self.scalar_label = name

    def get_data(self):
        return {
            "name": self.name, "labels": self.labels, "data": self.data,
            "scalar_value": self.scalar_value,
            "scalar_maximum": self.scalar_maximum,
            "scalar_label": self.scalar_label}

class StdStateMetric(StateMetric):

    def compute(self):
        name = self.name
        metrics = [district.metrics[name] for district in self.districts]
        assert all((isinstance(m, DistrictAggregateMetric) for m in metrics))

        if not metrics:
            self.scalar_value = 0
        else:
            self.scalar_value = np.std((m.scalar_value for m in metrics))
            self.scalar_maximum = max((m.scalar_maximum for m in metrics)) # maybe take std of maxes instead?
    
    def get_data(self):
        return {
            "name": self.name, "labels": self.labels, "data": self.data,
            "scalar_value": self.scalar_value,
            "scalar_maximum": self.scalar_maximum,
            "scalar_label": self.scalar_label}