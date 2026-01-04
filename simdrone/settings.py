# settings.py
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
import json
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel
from PyQt6.QtCore import Qt




class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings (VS Code Style)")
        self.setFixedSize(600, 400)
        self.config = config  # dict: {'display': {'width': 1000, 'height': 700}, 'camera': {'top_height': 20}, ...}

        layout = QVBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search settings...")
        self.search_bar.textChanged.connect(self.filter_settings)
        layout.addWidget(self.search_bar)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Setting", "Value"])
        self.tree.setColumnWidth(0, 300)
        layout.addWidget(self.tree)

        btn_layout = QVBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_settings()

    def load_settings(self):
        self.tree.clear()
        for category, items in self.config.items():
            cat_item = QTreeWidgetItem([category, ""])
            for key, value in items.items():
                child = QTreeWidgetItem([key, str(value)])
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsEditable)  # 값 편집 가능
                cat_item.addChild(child)
            self.tree.addTopLevelItem(cat_item)
        self.tree.expandAll()

    def filter_settings(self, text):
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            cat_item.setHidden(True)
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                if text.lower() in child.text(0).lower():
                    child.setHidden(False)
                    cat_item.setHidden(False)
                else:
                    child.setHidden(True)

    def apply_changes(self):
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            category = cat_item.text(0)
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                key = child.text(0)
                value = child.text(1)
                try:
                    value = int(value) if value.isdigit() else float(value) if '.' in value else value
                except:
                    pass
                self.config[category][key] = value
        self.accept()