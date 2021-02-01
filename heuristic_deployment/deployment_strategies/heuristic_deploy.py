from min import MinState
import numpy as np
from enum import Enum
from helpers import get_vector_angle as gva, polar_to_vec as p2v, normalize
from deployment_strategies.deployment_strategy import DeploymentStrategy, FollowingStrategy

class HeuristicDeploy(DeploymentStrategy):

    def __init__(self, k=3, following_strategy=FollowingStrategy.SAFE):
        super().__init__(following_strategy)
        self.k = k
        self.__exploration_dir = None
        self.__exploration_vec = None

    def explore(self, MIN, beacons, ENV):
        if self.__exploration_dir is None:
            self.__exploration_dir = HeuristicDeploy.__get_exploration_dir(MIN, self.k)
            self.__exploration_vec = p2v(1, self.__exploration_dir)
        
        obs_vec = HeuristicDeploy.__get_obstacle_avoidance_vec(MIN, ENV)

        self.v = normalize(self.__exploration_vec + obs_vec)

        if np.abs(self.__exploration_dir - gva(self.__exploration_vec + obs_vec)) > np.pi/2 or MIN.get_RSSI(self.target) < np.exp(-2.6):
            MIN.state = MinState.LANDED
            self.v = np.zeros((2, ))
        return self.v

    @staticmethod
    def __get_exploration_dir(MIN, k, rand_lim = 0.1):
        angs_to_neighs = gva(np.array([
            MIN.get_vec_to_other(n) for n in MIN.neighbors
        ]).T)
        num_neighs_of_neighs = np.array([
            len(n.neighbors) for n in MIN.neighbors
        ])

        alphas = num_neighs_of_neighs < k
        sum_alphas = np.sum(alphas)
        theta1 = np.sum(alphas*angs_to_neighs)/sum_alphas if sum_alphas > 0 else 0
        theta2 = np.random.uniform(-rand_lim, rand_lim)
        return theta1 + 0*theta2

    @staticmethod
    def __get_obstacle_avoidance_vec(MIN, ENV):
        xtra_heading_vec = np.zeros((2, ))
        for s in MIN.sensors:
            r = s.sense(ENV).get_val()
            if not r == np.inf:
                abs_ang = MIN.heading + s.host_relative_angle
                xtra_heading_vec += -p2v(1 - r/s.max_range, abs_ang)
        return xtra_heading_vec