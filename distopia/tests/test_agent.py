from distopia.app.agent import VoronoiAgent
import numpy as np
class TestAgent:

    def test_compute_voronoi_metrics(self):
        # test cleanup after failure
        v = VoronoiAgent()
        v.load_data()

        collinear_obs = {0: [np.array([650, 750])], 1: [np.array([800, 750])], 2: [np.array([750, 750])], 3: [np.array([600, 750])]}
        failure = False
        try:
            raw_districts = v.get_voronoi_districts(collinear_obs)
            v.compute_voronoi_metrics(raw_districts)
        except:
            failure = True
        
        assert failure == True

        valid_obs = {0: [np.array([650, 400])], 1: [np.array([800, 400])], 2: [np.array([750, 750])], 3: [np.array([600, 750])]}
        try:
            raw_districts = v.get_voronoi_districts(valid_obs)
            s,d = v.compute_voronoi_metrics(raw_districts)
            failure = False
        except:
            failure = True
        assert failure == False
        assert len(d) > 0