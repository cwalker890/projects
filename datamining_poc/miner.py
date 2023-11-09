import struct
import json
import hashlib
import random
import logging
import logging.config

# Define logger
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('miner')


class Miner(object):
    """
    Miner - A class used to represent a miner who performs crypto-currency
            mining to start new blocks in the blockchain ledger

    """
    # Set the maximum value for random numbers and nonces to a large value
    # to help ensure that mining will succeed
    MAX_VAL = 2**32-1

    def __init__(self, name):
        """
        Initializes an instance of the Miner class.

        Parameters:
            self : the instance of the class
            name : the name of the miner

        Returns:
            N/A
        """
        logger.info('%s: Creating Miner %s...', __name__, name)

        # Define attribute to maintain miner's name
        self.name = name
        # Define block header attribute for this miner
        self.block_hdr = {'miner': self.name,
                          'previous_hash': '',
                          'rand': ''}
        # Define the resulting hash attribute
        self.hash_hex = None

    def do_work(self, prev_hash):
        """
        Performs crypto-currency mining by the miner

        Parameters:
            self : the instance of the class
            dest_ledger : the ledger object being mined and to which the new
                          block will be added

        Returns:
            hash_hex : the resulting hash when mining is successfully
                       completed
        """
        # Define SHA256 hash object
        block_hash = hashlib.sha256()
        # Define flag to indicate when proof of work is complete
        proof_of_work_complete = False
        # Set the previous hash in the block header
        self.block_hdr['previous_hash'] = prev_hash

        # Loop until the proof of work is complete
        while not proof_of_work_complete:
            # Before updating the original hash object with the block header,
            # make a copy of the original for continued use with subsequent
            # block headers containing different random numbers
            block_hash_copy1 = block_hash.copy()

            # Set a new random number in block header attribute
            self.block_hdr['rand'] = random.randint(0, Miner.MAX_VAL)

            # Compute initial hash using the header
            block_hash_copy1.update(json.dumps(self.block_hdr).encode())

            # Iterate through nonce values
            for nonce in range(Miner.MAX_VAL):
                # Convert the current nonce value to binary encoding
                nonce_bin = struct.pack("<I", nonce)

                # Make a copy of the copied hash object for continued use
                # with subsequent nonce values
                block_hash_copy2 = block_hash_copy1.copy()

                # Update hash object with nonce
                block_hash_copy2.update(nonce_bin)
                # Compute cryptohash and store in the hash attribute
                self.hash_hex = block_hash_copy2.hexdigest()

                # If the leading 2 bytes of the resulting hash are zero,
                # set flag to true and break out of inner loop
                if self.hash_hex[:4] == '0000':
                    proof_of_work_complete = True
                    break

        # Return the resulting hash
        return self.hash_hex
