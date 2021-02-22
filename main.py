from environment import Env

from beacons.SCS.scs import SCS
from beacons.MIN.min import Min, MinState

from deployment.following_strategies.attractive_follow import AttractiveFollow
from deployment.following_strategies.straight_line_follow import StraightLineFollow
from deployment.exploration_strategies.potential_fields_explore import PotentialFieldsExplore
from deployment.exploration_strategies.heuristic_explore import HeuristicExplore
from deployment.following_strategies.no_follow import NoFollow
from deployment.exploration_strategies.line_explore import LineExplore
from deployment.deployment_fsm import DeploymentFSM

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def simulate(dt, mins, scs, env):
  scs.insert_into_environment(env)
  beacons = np.array([scs], dtype=object)

  for m in mins:
    m.insert_into_environment(env)
    while not m.state == MinState.LANDED:
          m.do_step(beacons, scs, env, dt)
    beacons = np.append(beacons, m)
    for b in beacons:
      b.compute_neighbors(beacons)
    print(f"min {m.ID} landed at pos\t\t\t {m.pos}")
    if not m.deployment_strategy.get_target() is None:
          print(f"Its target now has {len(m.deployment_strategy.get_target().neighbors)} neighs\n------------------", )
  print(f"minimum number of neighbors: {min(beacons, key=lambda b: len(b.neighbors))}")    

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
        [-10, -10],
        [ -10, -5],
        [ 10,  -5],
        [10,  -10],
      ])
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
      np.array([
        [-2,  -2],
        [-2,  2],
        [ 2,  2],
        [ 2, -2],
      ]),
      np.array([
        [-0.5, -0.5],
        [ 0.5, -0.5],
        [ 0.5, 0.5],
        [-0.5, 0.5],
      ])
    ]

  env = Env(
    # np.array([
    #   -9.8, -5.2
    # ]),
    np.array([
      0, 0
    ]),
    obstacle_corners =  [] #obstacle_corners_2D_3#[]#obstacle_corners_2D_1 #[]
  )

# %%Parameter initialization
  _animate, save_animation = True, False
  start_animation_from_min_ID = 0

  max_range = 3#0.51083#float(-np.log(-0.6))#3 #0.75    0.51083

  N_mins = 10  #7#2*5#3
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
        NoFollow(),
        LineExplore(
          RSSI_threshold=0.5,
          K_o=0.01,
          ndims=1,
        )
      ),      
      xi_max=3,
      d_perf=1,
      d_none=3
    ) for _ in range(N_mins)
  ]

  simulate(dt, mins, scs, env)
  fig, ax = plt.subplots(nrows=2,ncols=1)

  # fig2, ax2 = plt.subplots(1)
  # ax2.set_title("Force applied")

  if _animate:
    for mn in mins[:start_animation_from_min_ID]:
      mn.plot(ax[0])
      mn.plot_traj_line(ax[0])
      mn.plot_force_traj_line(ax[1])

    offset, min_counter = [0], [start_animation_from_min_ID]

    def init():
      if type(ax) == np.ndarray:
        scs.plot(ax[0])
        env.plot(ax[0])
        artists = []
        for mn in mins:
          artists += mn.plot(ax[0])
          artists += (mn.plot_traj_line(ax[0]), ) #Type: Line2D(_line6)
          artists += (mn.plot_force_traj_line(ax[1]), )
          mn.plot_pos_from_pos_traj_index(0)
          mn.plot_force_from_traj_index(0)
      else:
        scs.plot(ax[0])
        env.plot(ax[0])
        artists = []
        for mn in mins:
          artists += mn.plot(ax[0])
          artists += (mn.plot_traj_line(ax[0]), )
          mn.plot_pos_from_pos_traj_index(0)
      return artists

    def animate(i):
      if i - offset[0] >= mins[min_counter[0]].get_pos_traj_length():
        offset[0] += mins[min_counter[0]].get_pos_traj_length()
        min_counter[0] += 1
      return mins[min_counter[0]].plot_pos_from_pos_traj_index(i - offset[0]), mins[min_counter[0]].plot_force_from_traj_index(i-offset[0]) #2

    anim = FuncAnimation(fig, animate, init_func=init, interval=2, blit=False)
    if save_animation:
      animation_name = "animation.gif"
      print("Saving animation")
      anim.save(animation_name)
      print(f"Animation saved to {animation_name}")

  else:
    env.plot(ax[0])
    scs.plot(ax[0])
    for mn in mins:
      mn.plot(ax[0])
      mn.plot_traj_line(ax[0])
      mn.plot_force_traj_line(ax[1])
      ax[1].legend()
      
  plt.show()

