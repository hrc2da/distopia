import distopia
from distopia.app.agent import VoronoiAgent
import numpy as np
from skopt import forest_minimize, dump


class RFBO:
    max_cost = 1e9
    '''
        random forest bayes minimization
        takes a single objective for now, e.g. 'name'
    '''
    def __init__(self,objective,objective_fn,n_fiducials=4):
        self.init_agent()
        self.objective_fn = objective_fn
        self.objective_name = objective
        self.n_fiducials=n_fiducials
        try:
            self.objective_id = self.agent.metrics.index(objective)
        except ValueError:
            print("Trying to optimize on {} but it doesn't exist!".format(objective))
            raise
        self.init_cost_dimensions()
        self.n_calls = 0

    def init_agent(self):
        self.agent = VoronoiAgent()
        self.agent.load_data()
        self.width, self.height = self.agent.screen_size
    
    def init_cost_dimensions(self):
        self.cost_dimensions = []
        for i in range(self.n_fiducials):
            self.cost_dimensions.append((0,self.width))
            self.cost_dimensions.append((0,self.height))
        
    def cost_function(self,x):
        '''
            x is a tuple of fiducial x,y coords, e.g (x0,y0,x1,y1...)
        '''
        assert len(x) == 2*self.n_fiducials
        self.n_calls += 1

        fids = {}
        for i in range(0,len(x),2):
            fids[i//2] = [(x[i],x[i+1])]
        
        try:
            state_m,district_m = self.agent.compute_voronoi_metrics(fids)
            
        except Exception:
            print("Couldn't compute Voronoi for {}".format(fids))
            #raise
            return self.max_cost
        try:
            objectives = self.extract_objective(district_m)
            
            cost = self.objective_fn(objectives)
            print("{}:{}".format(self.n_calls,cost))
        except ValueError as v:
            print(v)
            cost =  self.max_cost
        
        return cost
        
    
    def extract_objective(self,districts):
        objective_vals = []
        
        if len(districts) < 1:
            raise ValueError("No Districts")
        for d in districts:
            data = districts[d][self.objective_id].get_data()
            if len(data['data']) < 1:
                raise ValueError("Empty District")
            else:
                objective_vals.append(data['scalar_value'])
        return objective_vals
        

    def minimize(self, max_iters=100):
        
        return forest_minimize(self.cost_function, self.cost_dimensions, n_calls=max_iters)



def metric_max(districts):
    '''
        minimize this to maximize the evenness of the district pops
    '''
    return max(districts)

def metric_std(districts):
    return np.std(districts)

if __name__=='__main__':
    bo = RFBO('population',metric_std)
    max_iterations = 2000
    # initialize randomly
    #fids = {i: [(random.random() * w, random.random() * h)] for i in range(4)}
    res = bo.minimize(max_iterations)
    del res.specs['args']['func'] # delete the objective function so we can pickle!
    dump(res,'rf_res.pkl',store_objective=False)