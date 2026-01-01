# utils.py
# Copyright 2026 MinSup Kim
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import numpy as np

from utils import *




class TransformState:
    def __init__(self, position=[0.0, 0.0, 0.0], rotation=[0.0, 0.0, 0.0]):
        self.position = np.array(position, dtype=float)
        self.rotation = np.array(rotation, dtype=float)  # pitch, yaw, roll (degrees)

    def translate(self, delta):
        self.position += np.array(delta)

    def rotate(self, delta):
        self.rotation += np.array(delta)
        self.rotation[0] = np.clip(self.rotation[0], -89.9, 89.9)  # pitch limit
