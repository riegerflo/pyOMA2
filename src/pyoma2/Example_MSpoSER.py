"""
Created on Wed Jan 24 09:00:24 2024

@author: dagpa
"""

import os

import numpy as np
import pandas as pd
from scipy import signal

from pyoma2.algorithm import (
    SSIcov_algo,
)
from pyoma2.OMA import MultiSetup_PoSER, SingleSetup

# import data files
set1 = np.load(r"src\pyoma2\test_data\3SL\set1.npy", allow_pickle=True)
set2 = np.load(r"src\pyoma2\test_data\3SL\set2.npy", allow_pickle=True)
set3 = np.load(r"src\pyoma2\test_data\3SL\set3.npy", allow_pickle=True)

# import geometry files
_fold = r"src/pyoma2/test_data/3SL"
# Names of the channels
Names = [
    [
        "ch1_1",
        "ch2_1",
        "ch3_1",
        "ch4_1",
        "ch5_1",
        "ch6_1",
        "ch7_1",
        "ch8_1",
        "ch9_1",
        "ch10_1",
    ],
    [
        "ch1_2",
        "ch2_2",
        "ch3_2",
        "ch4_2",
        "ch5_2",
        "ch6_2",
        "ch7_2",
        "ch8_2",
        "ch9_2",
        "ch10_2",
    ],
    [
        "ch1_3",
        "ch2_3",
        "ch3_3",
        "ch4_3",
        "ch5_3",
        "ch6_3",
        "ch7_3",
        "ch8_3",
        "ch9_3",
        "ch10_3",
    ],
]
# Common Backgroung nodes and lines
BG_nodes = np.loadtxt(_fold + os.sep + "BG_nodes.txt")
BG_lines = np.loadtxt(_fold + os.sep + "BG_lines.txt").astype(int)
# Geometry 1
sens_coord = pd.read_csv(_fold + os.sep + "sens_coord.txt", sep="\t")
sens_dir = np.loadtxt(_fold + os.sep + "sens_dir.txt")
# Geometry 2
sens_lines = np.loadtxt(_fold + os.sep + "sens_lines.txt").astype(int)
pts_coord = pd.read_csv(_fold + os.sep + "pts_coord.txt", sep="\t")
sens_map = pd.read_csv(_fold + os.sep + "sens_map.txt", sep="\t")
sens_sign = pd.read_csv(_fold + os.sep + "sens_sign.txt", sep="\t")

# =============================================================================
fs = 100
# ------------------------------------------------------------------------------
# filtering and decimation
_q = 2  # Decimation factor
set1 = signal.decimate(set1, _q, axis=0)  # Decimation
set2 = signal.decimate(set2, _q, axis=0)  # Decimation
set3 = signal.decimate(set3, _q, axis=0)  # Decimation
fs = fs / _q  # [Hz] Decimated sampling frequency
# ------------------------------------------------------------------------------
# create single setup
ss1 = SingleSetup(set1, fs=fs)
ss2 = SingleSetup(set2, fs=fs)
ss3 = SingleSetup(set3, fs=fs)

# Initialise the algorithms for setup 1
ssicov1 = SSIcov_algo(name="SSIcov1", method="cov_mm", br=50, ordmax=80)
# Add algorithms to the class
ss1.add_algorithms(ssicov1)
ss1.run_all()

# # Initialise the algorithms for setup 2
ssicov2 = SSIcov_algo(name="SSIcov2", method="cov_mm", br=50, ordmax=80)
ss2.add_algorithms(ssicov2)
ss2.run_all()

# # Initialise the algorithms for setup 2
ssicov3 = SSIcov_algo(name="SSIcov3", method="cov_mm", br=50, ordmax=80)
ss3.add_algorithms(ssicov3)
ss3.run_all()

# ------------------------------------------------------------------------------
# Plot
ssicov1.plot_STDiag(freqlim=20)
ssicov2.plot_STDiag(freqlim=20)
ssicov3.plot_STDiag(freqlim=20)

# %% =============================================================================
# ss1.MPE_fromPlot("SSIcov1", freqlim=25)
# ss2.MPE_fromPlot("SSIcov2", freqlim=25)
# ss3.MPE_fromPlot("SSIcov3", freqlim=25)
# ------------------------------------------------------------------------------
ss1.MPE(
    "SSIcov1",
    sel_freq=[2.63, 2.69, 3.43, 8.29, 8.42, 10.62, 14.00, 14.09, 17.57],
    order=50,
)
ss2.MPE(
    "SSIcov2",
    sel_freq=[2.63, 2.69, 3.43, 8.29, 8.42, 10.62, 14.00, 14.09, 17.57],
    order=40,
)
ss3.MPE(
    "SSIcov3",
    sel_freq=[2.63, 2.69, 3.43, 8.29, 8.42, 10.62, 14.00, 14.09, 17.57],
    order=40,
)

# %% =============================================================================
# ############### INITIALIZATION OF THE MULTISETUP #############################
# reference indices
ref_ind = [[0, 1, 2], [0, 1, 2], [0, 1, 2]]
# Creating Multi setup
msp = MultiSetup_PoSER(ref_ind=ref_ind, single_setups=[ss1, ss2, ss3])
# Merging results from single setups
result = msp.merge_results()
# dictionary of merged results
res_ssicov = dict(result[SSIcov_algo.__name__])
# -----------------------------------------------------------------------------

# Define geometry1
msp.def_geo1(
    Names,  # Names of the channels
    sens_coord,  # coordinates of the sensors
    sens_dir,  # sensors' direction
    bg_nodes=BG_nodes,  # BG nodes
    bg_lines=BG_lines,  # BG lines
)

# Define geometry 2
msp.def_geo2(
    Names,  # Names of the channels
    pts_coord,
    sens_map,
    order_red="xy",
    sens_sign=sens_sign,
    sens_lines=sens_lines,
    bg_nodes=BG_nodes,
    bg_lines=BG_lines,
)

# Plot the geometry
msp.plot_geo1(scaleF=2)
# -----------------------------------------------------------------------------
# define results variable
algoRes = result[SSIcov_algo.__name__]

# Plot mode 2 (geometry 1)
msp.plot_mode_g1(Algo_Res=algoRes, Geo1=msp.Geo1, mode_numb=2, view="3D", scaleF=2)
# Animate mode 3 (geometry 2)
msp.anim_mode_g2(Algo_Res=algoRes, Geo2=msp.Geo2, mode_numb=3, view="xy", scaleF=3)
