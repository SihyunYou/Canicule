# -*- coding: utf-8 -*-
from compter import *
import matplotlib.pyplot as plt
import numpy as np
import mplcyberpunk
import matplotlib.pylab as pylab
from scipy.ndimage import gaussian_filter1d
import sys

user = sys.argv[1]

plt.style.use("cyberpunk")
FIGURE, AXE = plt.subplots(1, figsize=(15, 6))
pylab.rcParams.update({   
            'legend.fontsize': 'x-large',
            'figure.figsize': (15, 5),
            'legend.fontsize': 13,
            'axes.labelsize': 12,
            'axes.titlesize':17,
            'xtick.labelsize':15,
            'ytick.labelsize':15,
            'font.family' : 'S-Core Dream'})

FIGURE.patch.set_facecolor('black')
AXE.set_facecolor('black')
plt.plot(np.arange(1, len(evaluation_jour) + 1), gaussian_filter1d(evaluation_jour, 0.5), 'o-', label = 'Profitability(%)')
plt.xticks(np.arange(1, len(evaluation_jour) + 1, 6))
AXE.set_yticks(np.arange(0, max(evaluation_jour) * 1.3, 0.4))
AXE.set_xlabel('D - DAY+')
AXE.legend(loc='upper right')
mplcyberpunk.make_lines_glow(AXE)
mplcyberpunk.add_underglow(AXE)
plt.show()

plt.style.use("cyberpunk")
FIGURE, AXE = plt.subplots(1, figsize=(15, 6))
pylab.rcParams.update({   
            'legend.fontsize': 'x-large',
            'figure.figsize': (15, 5),
            'legend.fontsize': 13,
            'axes.labelsize': 12,
            'axes.titlesize':17,
            'xtick.labelsize':15,
            'ytick.labelsize':15,
            'font.family' : 'S-Core Dream'})
FIGURE.patch.set_facecolor('black')
AXE.set_facecolor('black')
plt.plot(np.arange(1, len(somme_profit_list[user]) + 1), gaussian_filter1d(somme_profit_list[user], 0.5), '-', color='#BFFF00')
AXE.set_xlabel('Event')
mplcyberpunk.make_lines_glow(AXE)
mplcyberpunk.add_underglow(AXE)
plt.show()