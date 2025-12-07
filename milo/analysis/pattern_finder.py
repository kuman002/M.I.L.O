"""
Module: pattern_finder.py
Description: Finds patterns in command logs.
"""

# milo/analysis/pattern_finder.py
import os
import collections

class PatternFinder:
    def __init__(self, log_file="data/command_log.csv"):
        self.log_file = log_file

    def log_command(self, command):
        with open(self.log_file, "a") as f:
            f.write(f"{command}\n")

    def get_favorite_command(self):
        if not os.path.exists(self.log_file): return None
        with open(self.log_file, "r") as f:
            commands = [line.strip() for line in f.readlines()]
        if not commands: return None
        
        # Return most common command
        return collections.Counter(commands).most_common(1)[0][0]