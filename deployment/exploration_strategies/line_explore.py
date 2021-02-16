from deployment.exploration_strategies.exploration_strategy import (
    ExplorationStrategy,
    AtLandingConditionException
)
from deployment.deployment_helpers import get_obstacle_forces as gof
from beacons.MIN.min import Min, MinState

import numpy as np

class LineExplore(ExplorationStrategy):
  def __init__(self, K_o=1, force_threshold=0.01, RSSI_threshold=0.6, ndims=1): #RSSI_threshold=0.6
    self.K_o = K_o
    self.force_threshold = force_threshold
    self.RSSI_threshold = RSSI_threshold
    self.ndims = ndims
    self.prev_xi_rand = None
    self.prev_neigh_indices = None

  def prepare_exploration(self, target):
      return super().prepare_exploration(target)

  def get_exploration_velocity(self, MIN, beacons, ENV):
    
    # SE OVER HVORDAN TING NEDENFOR BLIR REGNET UT, SAMT SE HVA SOM ER KOMMENTERT BORT
    # RSSIs_all = np.array([np.linalg.norm(MIN.get_vec_to_other(b)) for b in beacons])
    # neigh_indices, = np.where(RSSIs_all < MIN.range)
    # Change state of all neighbors to MinState.NEIGHBOR???
    xi_all = np.array([MIN.get_RSSI(b) for b in beacons]) #np.array([np.linalg.norm(MIN.get_vec_to_other(b)) for b in beacons])#
    neigh_indices, = np.where(xi_all > self.RSSI_threshold) #np.where(RSSIs_all <= MIN.range) 
    xi_neigh = xi_all[neigh_indices]
    
    F = None
    if len(neigh_indices)!=0:
      if self.ndims == 1:
        """ 1D """
        x_is = np.array([beacons[i].pos[0] for i in neigh_indices])#np.array([beacons[i].pos[0] for i in neigh_indices]) #np.array([b.pos[0] for b in beacons])
        k_is = np.zeros(x_is.shape)#np.ones(x_is.shape)# * (np.ones(len(x_is)) + np.array(range(len(x_is)))*0.1)#np.zeros(x_is.shape)#np.ones(x_is.shape)
        k_is[-1] = 1

        epsilon = 3*0.10 #0 because we only want the drones to move to the right?

        if np.array(neigh_indices != self.prev_neigh_indices).all():
          print(f"prev_neigh: {self.prev_neigh_indices} \t current_neigh: {neigh_indices}")
          xi_random = np.random.uniform(epsilon - self.RSSI_threshold, epsilon)
          if self.prev_xi_rand != None:
            if (xi_random - self.prev_xi_rand) > 0.4:
              xi_random = epsilon - 0.05
            print(f"prev_random: {self.prev_xi_rand} \t current RAND: {xi_random}")
            print("-------------------------------------------------")
        else:
          xi_random = self.prev_xi_rand

        F_n = -1*np.sum(k_is*(MIN.pos[0] - x_is - (xi_neigh - epsilon + xi_random)))
        F_o = 0*gof(self.K_o, MIN, ENV)[0]
        F = np.array([F_n + F_o, 0])
        self.prev_xi_rand = xi_random
        self.prev_neigh_indices = neigh_indices
      elif self.ndims == 2:
        """ 2D """
        x_is = np.array([beacons[i].pos for i in neigh_indices])
        k_is = 5*np.ones(len(x_is))#np.array(range(len(x_is)))%2np.ones(len(x_is)) + np.array(range(len(x_is)))#np.ones(len(x_is)) #np.zeros(len(x_is))
        #k_is[-1] = 1
        epsilon_x = 4*0.10
        epsilon_y = 1*0.10
        epsilon = np.hstack((epsilon_x, epsilon_y)).reshape(2, )

        # Update the xi_rands when the neighbor set changes
        # print(f"(self.prev_neigh_indices == None): {(self.prev_neigh_indices == None)}")
        # print(f"(neigh_indices == self.prev_neigh_indices).any(): {(neigh_indices == self.prev_neigh_indices).any()}")
        # print(f"prev_neigh: {self.prev_neigh_indices} \t current_neigh: {neigh_indices}")
        # print(f"prev_rand: {self.prev_RSSIs_rand} \t current_rand: {RSSIs_random}")

        if np.array(neigh_indices != self.prev_neigh_indices).all(): #np.array(self.prev_neigh_indices == None).any() or 
          #print(f"prev_neigh: {self.prev_neigh_indices} \t current_neigh: {neigh_indices}")
          xi_random_x = np.random.uniform(epsilon_x-self.RSSI_threshold, epsilon_x) #self.RSSI_threshold
          xi_random_y = np.random.uniform(epsilon_y-self.RSSI_threshold, epsilon_y)
          if np.array(self.prev_xi_rand != None).any():
            if (xi_random_x - self.prev_xi_rand[0]) > 0.4:
              xi_random_x = epsilon_x - 0.1            
            if (xi_random_y - self.prev_xi_rand[1]) > 0.4:
              xi_random_y = epsilon_y - 0.1
          xi_random = np.hstack((xi_random_x, xi_random_y))         
          #print(f"prev_random: {self.prev_xi_rand} \t current RAND: {xi_random}")
        else:
          xi_random = self.prev_xi_rand

        F_n = np.zeros((2, ))
        for i in range(len(x_is)): #neigh_indices:
          #F_n += (k_is[i]*(x_is[i].reshape(2, ) - MIN.pos.reshape(2, ) + RSSIs_all[i] - epsilon.reshape(2, ) + RSSIs_random)).reshape(2, ) #funker
          F_n -= (k_is[i]*(x_is[i]+ xi_all[i] - (MIN.pos.reshape(2, ) - epsilon + xi_random))).reshape(2, )
          #F_n += (k_is[i]*(MIN.pos.reshape(2, ) - (x_is[i]+ xi_all[i] - epsilon + xi_random))).reshape(2, ) #+= WORKS "PERFECTLY"?!?!

        F_o = gof(self.K_o, MIN, ENV).reshape(2, )
        # print(f"F_n: {F_n}")
        # print(f"F_o: {F_o}")
        # print("-------------")
        F = F_n + F_o
        self.prev_xi_rand = xi_random
        self.prev_neigh_indices = neigh_indices
        # print(f"np.linalg.norm(F): {np.linalg.norm(F)}")
    else:
      print("No neighbors")
      raise AtLandingConditionException
    if np.linalg.norm(F) < self.force_threshold:
      print(f"Force lower than threshold: {np.linalg.norm(F)} < {self.force_threshold}")
      raise AtLandingConditionException
    return F