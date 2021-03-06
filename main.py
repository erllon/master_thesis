from environment import Env

from beacons.SCS.scs import SCS
from beacons.MIN.min import Min, MinState

from deployment.following_strategies.attractive_follow import AttractiveFollow
from deployment.following_strategies.straight_line_follow import StraightLineFollow
from deployment.following_strategies.new_attractive_follow import NewAttractiveFollow
from deployment.exploration_strategies.potential_fields_explore import PotentialFieldsExplore
from deployment.exploration_strategies.new_potential_fields_explore import NewPotentialFieldsExplore
from deployment.exploration_strategies.heuristic_explore import HeuristicExplore
from deployment.following_strategies.no_follow import NoFollow
from deployment.exploration_strategies.line_explore import LineExplore, LineExploreKind
from deployment.deployment_fsm import DeploymentFSM

from plot_fields import FieldPlotter

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from helpers import polar_to_vec as p2v

def simulate(dt, mins, scs, env):
  scs.insert_into_environment(env)
  beacons = np.array([scs], dtype=object)

  #scs.generate_target_pos(beacons,env, mins[0])
  mins[0].target_pos = p2v(mins[0].target_r,np.random.uniform(0, np.pi/2))
  mins[0].prev = scs
  for i in range(len(mins)):
    mins[i].insert_into_environment(env)
    while not mins[i].state == MinState.LANDED:
      mins[i].do_step(beacons, scs, env, dt)
    if i < len(mins)-1: #as long as i is not the index of the last min
      if i-1 > 0: #"prev_drone" for drone 1 will be the scs
        mins[i].generate_target_pos(beacons,env,mins[i-1], mins[i+1])
      else:
        mins[i].generate_target_pos(beacons,env,scs, mins[i+1])
      mins[i+1].prev = mins[i]
    beacons = np.append(beacons, mins[i])
    for b in beacons:
      b.compute_neighbors(beacons)
    print(f"min {mins[i].ID} landed at pos\t\t\t {mins[i].pos}")
    print(f"min {mins[i].ID} target\t\t\t\t {mins[i].target_pos}")
    print(f"min {mins[i].ID} neighbors: {[n.ID for n in mins[i].neighbors]}")
    if not mins[i].deployment_strategy.get_target() is None:
          print(f"Its target now has {len(mins[i].deployment_strategy.get_target().neighbors)} neighs\n------------------", )
  print(f"minimum number of neighbors: {min(beacons, key=lambda b: len(b.neighbors))}") 
  return beacons   

if __name__ == "__main__":
# %% Plotting styles
  # set styles
  try:
      # installed with "pip install SciencePLots" (https://github.com/garrettj403/SciencePlots.git)
      # gives quite nice plots
      plt_styles = ["science", "grid", "bright", "no-latex"]
      plt.style.use(plt_styles)
      print(f"pyplot using style set {plt_styles}")
  except Exception as e:
      print(e)
      print("setting grid and only grid and legend manually")
      plt.rcParams.update(
          {
              # setgrid
              "axes.grid": False,#True,
              "grid.linestyle": ":",
              "grid.color": "k",
              "grid.alpha": 0.5,
              "grid.linewidth": 0.5,
              # Legend
              "legend.frameon": True,
              "legend.framealpha": 1.0,
              "legend.fancybox": True,
              "legend.numpoints": 1,
          }
      )
# %% Environment initialization
  obstacle_corners_1D = [
      np.array([
        [-10, -10],
        [ -6, -10],
      ]),
    ]

  obstacle_corners_2D_1 = [
      np.array([
        [-0.1, -0.1],
        [-0.1,   10],
        [10,     10],
        [10,     -0.1],
      ]),
      # np.array([
      #   [4.0,  5],
      #   [4.0, -0.1],
      #   [5.0, -0.1],
      #   [5.0,  5]
      # ])
    ]
  obstacle_corners_2D_2 = [
      np.array([
        [-10, -10],
        [ -10, -9],
        [ 10,  -9],
        [10,  -10],
      ]),
      np.array([
        [-9.99, -9.01],
        [-9.99, -9.5],
        [-8, -9.5],
        [-8, -9.01],
      ]),
      np.array([
        [-7 ,-9.99],
        [-6, -9.99],
        [-6, -9.8],
        [-7, -9.8]
      ])
    ]

  obstacle_corners_2D_3 = [
      # np.array([
      #   [3,  -2],
      #   [3,  2],
      #   [7,  2],
      #   [7, -2],
      # ]),
      np.array([
        [3, -6],
        [3,  6],
        [7,  6],
        [7, -6],
      ]),
      # np.array([
      #   [-0.5, -0.5],
      #   [ 0.5, -0.5],
      #   [ 0.5, 0.5],
      #   [-0.5, 0.5],
      # ])
    ]

  env = Env(
    # np.array([
    #   -9.8, -5.2
    # ]),
    np.array([
      0, 0
    ]),
    obstacle_corners = obstacle_corners_2D_1#[]#obstacle_corners_2D_1 #[]
  )

# %%Parameter initialization
  _animate, save_animation, plot_propterties = False, False, False
  start_animation_from_min_ID = 1

  max_range = 3 #0.51083#float(-np.log(-0.6))#3 #0.75    0.51083

  N_mins = 10 #7#2*5#3
  dt = 0.01#0.01

  scs = SCS(max_range)
  """ Potential fields exploration
  mins = [
    Min(
      max_range,
      DeploymentFSM(
        AttractiveFollow(
          K_o = 0.001,
          same_num_neighs_differentiator=lambda MINs, k: min(MINs, key=k)
        ),
        PotentialFieldsExplore(
          K_n=1,
          K_o=1,
          min_force_threshold=0.1
        )
      )
    ) for _ in range(N_mins)
  ]
  """
  """ Line exploration """

  mins = [
    Min(
      max_range,
      DeploymentFSM(
        # NoFollow(),
        # LineExplore(
        #   # RSSI_threshold=0.5,
        #   K_o= 5*1*(i+1),#30,# 12 0.1,#0.01, #12 works somewhat with TWO_DIM_LOCAL, else much lower (0.4-ish)
        #   kind=LineExploreKind.TWO_DIM_LOCAL,
        # )
        NewAttractiveFollow(K_o=1),
        NewPotentialFieldsExplore(K_o=10)
      ),
      xi_max=3,
      d_perf=1,
      d_none=3,
      delta_expl_angle=np.pi/4
    ) for i in range(N_mins)
  ]

  beacons = simulate(dt, mins, scs, env)
  
  if plot_propterties:
    fig, ax = plt.subplots(nrows=3,ncols=1)
    ax[0].title.set_text("Deployment")
    ax[1].title.set_text(r"$\left\|\| F_{applied} \right\|\|$") #Set title
    ax[2].title.set_text(r"$\xi$ from neighbors")               #Set title
  else:
    fig, ax = plt.subplots(1,1)
    ax.title.set_text("Deployment")

  if _animate: # TODO: if _animate: everything in same fig,  else: drones in one fig, "properties" in another fig
    for mn in mins[:start_animation_from_min_ID]:
      if plot_propterties:
        mn.plot(ax[0])
        mn.plot_traj_line(ax[0])
        mn.plot_vectors(mn.prev, env, ax[0])
        mn.plot_force_traj_line(ax[1])
      else:
        mn.plot(ax)
        mn.plot_vectors(mn.prev, env, ax)      


    offset, min_counter = [0], [start_animation_from_min_ID]

    def init():
      if plot_propterties:
        scs.plot(ax[0])
        env.plot(ax[0])
        artists = []
        for mn in mins:        
          artists += mn.plot(ax[0])
          artists += (mn.plot_traj_line(ax[0]), ) #Type: Line2D(_line6)
          artists += (mn.plot_force_traj_line(ax[1]), )
          artists += (mn.plot_xi_traj_line(ax[2]), )
          mn.plot_pos_from_pos_traj_index(0)
          mn.plot_force_from_traj_index(0)
          mn.plot_xi_from_traj_index(0)
        if start_animation_from_min_ID == 0:
          ax[1].legend()  
      else:
        scs.plot(ax)
        env.plot(ax)
        artists = []
        for mn in mins:
          artists += mn.plot(ax)
          artists += (mn.plot_traj_line(ax), )
          mn.plot_pos_from_pos_traj_index(0)
      return artists

    def animate(i):
      if i - offset[0] >= mins[min_counter[0]].get_pos_traj_length():
        offset[0] += mins[min_counter[0]].get_pos_traj_length()
        min_counter[0] += 1
      plt_pos_traj = mins[min_counter[0]].plot_pos_from_pos_traj_index(i - offset[0])
      #plt_force_traj = mins[min_counter[0]].plot_force_from_traj_index(i-offset[0])
      #plt_xi_traj = mins[min_counter[0]].plot_xi_from_traj_index(i-offset[0])
      return plt_pos_traj#, plt_force_traj, plt_xi_traj  #mins[min_counter[0]].plot_pos_from_pos_traj_index(i - offset[0]), mins[min_counter[0]].plot_force_from_traj_index(i-offset[0]) #2

    anim = FuncAnimation(fig, animate, init_func=init, interval=2, blit=False)
    
    if save_animation:
      animation_name = "animation.gif"
      print("Saving animation")
      anim.save(animation_name)
      print(f"Animation saved to {animation_name}")

  else:
    if plot_propterties:
      env.plot(ax[0])
      scs.plot(ax[0])
      for mn in mins:
        mn.plot(ax[0])
        mn.plot_traj_line(ax[0])
        mn.plot_vectors(mn.prev, env, ax[0])
      mn.plot_force_traj_line(ax[1])
      mn.plot_xi_traj_line(ax[2])
    else:
      env.plot(ax)
      scs.plot(ax)
      for j in range(len(mins)):#mn in mins:
        mins[j].plot(ax)
        mins[j].plot_traj_line(ax)
        if j == 0:
          mins[j].plot_vectors(scs,env,ax)
        else:
          mins[j].plot_vectors(mins[j-1],env,ax)
      ax.legend()
      ax.axis('equal')

  plt.show()