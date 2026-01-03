# logger.py
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

import csv
import time
import os

class Logger:
    def __init__(self, filename=None):
        if filename is None:
            filename = f"log_{int(time.time())}.csv"
        self.filename = filename
        self.data = []

    def log(self, timestamp, drones):
        row = {'timestamp': timestamp}
        for i, drone in enumerate(drones):
            status = drone.state.get_status()
            # Flatten the dictionary
            for key, value in status.items():
                if hasattr(value, '__len__'):
                    for j, v in enumerate(value):
                        row[f'drone_{i}_{key}_{j}'] = v
                else:
                    row[f'drone_{i}_{key}'] = value
        self.data.append(row)

    def save(self):
        if not self.data:
            return
        
        fieldnames = self.data[0].keys()
        
        with open(self.filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data)
        print(f"Log saved to {self.filename}")
