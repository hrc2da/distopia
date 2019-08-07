from distopia.app.agent import VoronoiAgent
from random import randint
import numpy as np
from copy import deepcopy


def gencoordinates(m, n, j, k, seen=None):
  '''Generate random coordinates in range x: (m,n) y:(j,k)
  
  instantiate generator and call next(g)
  
  based on:
  https://stackoverflow.com/questions/30890434/how-to-generate-random-pairs-of-
  numbers-in-python-including-pairs-with-one-entr
  '''  
  if seen is None:
    seen = set()
  x, y = randint(m, n), randint(j, k)
  while len(seen) < (n + 1 - m)**2:
      while (x, y) in seen:
          x, y = randint(m, n), randint(m, n)
      seen.add((x, y))
      yield (x, y)
  return


# TODO: need to update occupied when changing state
class GreedyAgent:
  def __init__(self,x_lim=(100,900),y_lim=(100,900),step_size=5):
    self.x_min,self.x_max = x_lim
    self.y_min,self.y_max = y_lim
    self.step = step_size
    self.occupied = set()
    self.coord_generator = gencoordinates(self.x_min, self.x_max,
                                          self.y_min, self.y_max, self.occupied)
    self.evaluator = VoronoiAgent()
    self.evaluator.load_data()
  
  
  def set_task(self,task):
    self.reward_weights = task
  
  def reset(self, initial=None, n_districts=8, max_blocks=5):
    '''Initialize the state randomly.
    '''
    self.coord_generator.clear()
    if initial is not None:
      self.state = initial
      return self.state
    
    else:
      self.state = {}
      # Place one block for each district, randomly
      for i in range(n_districts):
        self.state[i] = [next(self.coord_generator)]
        # add more blocks...
        #for j in range(randint(max_blocks-1)):
          
      return self.state
      
      
  def get_neighborhood(self,n_steps):
    '''Get all the configs that have one block n_steps away from the current
    '''
    neighborhood = []
    for district in self.state:
      for block in district:
        neighborhood += self.get_neighbors(district, block)
  
  def get_neighbors(self,district,block):
    '''Get all the designs that move "block" by one step.
    
    
    ignores moves to coords that are occupied or out of bounds
    '''
    neighbors = []
    
    moves = [np.array((self.step, 0)),np.array(-self.step, 0), 
             np.array(0, self.step), np.array(0, -self.step)]
    
    constraints = [lambda x,y : x < self.x_max, 
                   lambda x,y : x > self.x_min, 
                   lambda x,y : y < self.y_max, 
                   lambda x,y : y > self.y_min]
    
    x,y = self.state[district][block]
    
    for i,move in enumerate(moves):
      mx,my = x,y + move
      if constraints[i](mx,my) and (mx,my) not in self.occupied:
        new_neighbor = deepcopy(self.state)
        new_neighbor[district][block] = (mx,my)
        neighbors.append(new_neighbor)
    
    return neighbors
    
    
    
    
  def get_metrics(self, design):
    '''Get the vector of metrics associated with a design 
    
    returns m-length np array
    '''
    try:
      return self.evaluator.get_metrics() #TODO: call the right function!
    except:
      return None
    
    
    
  def get_reward(self, metrics):
    '''Get the scalar reward associated with metrics
    '''
    if metrics is None:
      return float("-inf")
    else:
      return np.dot(self.reward_weights, metrics)
    
    
  def run(self, n_steps, initial=None, eps=0.9, eps_decay=0.9):
    '''
    '''
    self.reset(initial)
    for i in range(n_steps):
      neighborhood = self.get_neighborhood(1)
      metrics = [self.get_metrics(n) for n in neighborhood]
      rewards = [self.get_reward(m) for m in metrics]
      best_idx = np.argmax(rewards)
      if np.random.rand() > eps:
        # mask out the legal options
        legal_mask = np.array([1 if r > float("-inf") else 0 for r in rewards])
        # convert to probability
        legal_mask /= np.sum(legal_mask)
        best_idx = np.random.choice(rewards, legal_mask)
      # TODO: need to update occupied when changing state
      self.state = neighborhood[best_idx]
      
