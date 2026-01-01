from os.path import dirname
from sys import path

path.insert(0, dirname(__file__))

from drone import Quadcopter
from simulator import Simulator