"""
Tasks
=============

defines task text and lookup\
provides switcher logic
"""

task_descriptions_dict = {
    "population": {
        "max": "Try to create districts that have very different population sizes.\n\n",
        "min": "Try to balance district populations.\n\n"
    },
    "pvi": {
        "max": "Try to minimize voter efficiency.\n\n",
        "min": "Try to maximize voter efficiency.\n\n"
    },
    "compactness": {
        "max": "Try to make districts with compact shapes.\n\n",
        "min": "Try to create districts that are as oddly shaped as possible.\n\n"
    },
    "projected_votes": {
        "max": "Try to create districts that benefit the Democratic Party.\n\n",
        "min": "Try to create districts that benefit the Republican Party.\n\n"
    },
    "race": {
        "max": "Try to create a few districts that are largely composed \n    of demographic minorities.\n\n",
        "min": "Try to create districts that evenly distribute demographic \n    minorities between districts.\n\n"
    }

}


class TaskSwitcher:

    def __init__(self, feature_list):
        self.construct_task_descriptions(task_descriptions_dict, feature_list)
        self.features = feature_list
        self.n_features = len(feature_list)

    def construct_task_descriptions(self, task_dictionary, feature_names):
        """is the five_norms_r
        :param task_dictionary: the dictionary of text to construct the array from
        :param feature_names: the features to add to the array, IN ORDERfeature_ordering = ['population', 'pvi', 'compactness', 'projected_votes', 'race']
        :return: self.task_descriptions, an array indexed by feature and then max/min
        """
        self.task_descriptions = [[] for feature in feature_names]
        for i, feature in enumerate(feature_names):
            self.task_descriptions[i] = [task_dictionary[feature]["min"], task_dictionary[feature]["max"]]
        return self.task_descriptions

    def get_task_str(self, feature_index, feature_value):
        """
        :param feature_index: the index of the feature to query
        :param feature_value: the value of the that feature to get a string for (in {-1, 0, 1}
        :return: '' if 0, otherwise the feature's max or min text
        """
        if feature_value == 0:
            return ''
        else:
            val = 0 if feature_value == -1 else 1
            return self.task_descriptions[feature_index][val]

    def get_task_text(self, task_arr):
        assert len(task_arr) == self.n_features
        task_text = ''
        for feature_index in range(len(task_arr)):
            task_text += self.get_task_str(feature_index, task_arr[feature_index])
        return task_text


if __name__ == '__main__':
    feature_ordering = ['population', 'pvi', 'compactness', 'projected_votes', 'race']
    ts = TaskSwitcher(feature_ordering)
    print(ts.get_task_text([1.0, 0, 1.0, 1.0, 1.0]))
