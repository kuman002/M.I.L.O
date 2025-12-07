"""
Module: crypto_manager.py
Description: Handles hashing and secure audit logging.
"""

"""
Module: crypto_manager.py
Description: Handles hashing and secure audit logging.
"""
import hashlib
import time
import json
import os

class CryptoManager:
    def __init__(self, log_file="data/audit_log.json"):
        self.log_file = log_file
        # Create log file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump([], f)

    def _calculate_hash(self, data_string):
        """Returns SHA-256 hash of a string."""
        return hashlib.sha256(data_string.encode()).hexdigest()

    def log_transaction(self, user_action, details):
        """
        Logs an action with a cryptographic link to the previous entry.
        """
        # Load existing log
        with open(self.log_file, 'r') as f:
            chain = json.load(f)

        # Get previous hash
        prev_hash = chain[-1]['hash'] if chain else "0"

        # Create new block
        timestamp = time.time()
        data_payload = f"{prev_hash}{user_action}{details}{timestamp}"
        new_hash = self._calculate_hash(data_payload)

        block = {
            'timestamp': timestamp,
            'action': user_action,
            'details': details,
            'prev_hash': prev_hash,
            'hash': new_hash
        }

        chain.append(block)

        # Save back to file
        with open(self.log_file, 'w') as f:
            json.dump(chain, f, indent=4)
            
        return new_hash