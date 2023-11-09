import miner
import random
import logging
import logging.config
import time

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('trangen')


class TranGEN(object):
    """
    TranGEN - transaction generator class, which randomly generates a
              specified number of blockchain ledger transactions and
              adds them to the ledger.
    """
    def __init__(self):
        """
        Initializes an instance of the TranGEN class.

        Parameters:
            self : the instance of the class

        Returns:
            N/A
        """
        # List attribute containing dictionaries of all users and their
        # initial balances
        self.users = [{'name': 'Alice', 'balance': 1000},
                      {'name': 'Bob', 'balance': 1000},
                      {'name': 'Jon', 'balance': 1000},
                      {'name': 'Howard', 'balance': 1000},
                      {'name': 'Rocky', 'balance': 1000}]
        self.last_transaction = {}
        self.transactionCnt = 0
        self.cancelledCnt = 0
        # Start with arbitrary hash since we have no previous hash
        self.prev_hash = ('00005894794791a54be8441cd53d763e2368187d09216a8640'
                          '3982a647326591')

    def generate_transactions(self, dest_ledger, count):
        """
        Generates a specified number of blockchain ledger transactions

        Parameters:
            self : the instance of the class
            dest_ledger : the ledger object to which the transactions will be
                          added
            count : the number of transactions to generate

        Returns:
            N/A
        """
        last_tid = -1
        success = True

        # Mine for new block
        logger.info('%s: Starting initial block...', __name__)
        self.start_new_block(dest_ledger)

        logger.info('%s: Attempt to generate %d transactions...', __name__,
                    count)

        # Add initial transaction
        try:
            last_tid = self.gen_transaction(dest_ledger)
        except Exception as e:
            success = False

        # Loop through the specified range (starting at 1 since the initial
        # transaction was added above
        for x in range(1, count):
            # Once we hit 256 transactions, start a new block
            if x % 256 == 0:
                logger.info('%s: Block is full. Starting new block...',
                            __name__)
                self.start_new_block(dest_ledger)

            do_trans = True
            # Get the current percentage of cancelled transactions
            pct_cancelled = self.cancelledCnt / x * 100

            # If the last transaction was not a cancellation and the current
            # percentage of cancellations is less than 20, consider whether
            # a cancellation should be added
            if last_tid > -1 and pct_cancelled < 20:
                # Generate random value between 1 and 100
                randval = random.randint(1, 100)
                # If the current percentage of cancellations is less than 10
                # or the random value is less than 15, cancel the previous
                # transaction
                if pct_cancelled < 10 or randval < 15:
                    do_trans = False
                    try:
                        last_tid = self.gen_cancellation(dest_ledger)
                    except Exception as e:
                        success = False
            # If a cancellation wasn't added, then add a transaction
            if do_trans:
                try:
                    last_tid = self.gen_transaction(dest_ledger)
                except Exception as e:
                    success = False

        if success:
            logger.info('Generated and added %d transactions to ledger.',
                        count)

    def gen_transaction(self, dest_ledger):
        """
        Generates a single transaction (non-cancellation) and adds it to the
        ledger

        Parameters:
            self : the instance of the class
            dest_ledger : the ledger object to which the transaction will be
                          added

        Returns:
            The transaction ID returned from the ledger
        """
        # Call the get_sender method to obtain a random sender
        # for the transaction who has a balance > 0.  Also, get
        # list index for the sender returned.
        sender_idx, sender = self.get_sender()

        # Randomly generate a transaction amount according to
        # the sender's current balance (1 <= amount <= balance)
        trans_amt = random.randint(1, sender['balance'])

        # Now randomly find a receiver (who cannot be the sender)
        receiver_idx = sender_idx
        while receiver_idx == sender_idx:
            receiver_idx = random.randint(0, 4)
        receiver = self.users[receiver_idx]

        # After determining the sender, receiver, and transaction amount,
        # add the transaction to the ledger
        tid = -1
        try:
            # Add the transaction to the ledger
            tid = dest_ledger.add_transaction(
                sender['name'], receiver['name'], trans_amt)

            # Credit the sender and debit the receiver
            self.users[sender_idx]['balance'] -= trans_amt
            self.users[receiver_idx]['balance'] += trans_amt
            # Save the last transaction
            self.last_transaction['tid'] = tid
            self.last_transaction['sender'] = sender['name']
            self.last_transaction['receiver'] = receiver['name']
            self.last_transaction['amount'] = trans_amt
            # Increment the transaction count
            self.transactionCnt += 1
        except Exception as e:
            logger.error('Error adding transaction. Msg: %s', e)

        return tid

    def gen_cancellation(self, dest_ledger):
        """
        Generates a single cancellation and adds it to the ledger

        Parameters:
            self : the instance of the class
            dest_ledger : the ledger object to which the cancellation will be
                          added

        Returns:
            -1 since it's a cancellation. This will be stored by the caller as
            the last_tid.
        """
        try:
            # Add the cancellaton to the ledger
            dest_ledger.cancel_transaction(self.last_transaction['tid'])

            # Revert the balance for each user
            for user in self.users:
                if user['name'] == self.last_transaction['sender']:
                    user['balance'] += self.last_transaction['amount']
                if user['name'] == self.last_transaction['receiver']:
                    user['balance'] -= self.last_transaction['amount']

            # Increment the cancellation count
            self.cancelledCnt += 1
        except Exception as e:
            logger.error('Error adding transaction. Msg: %s', e)

        return -1

    def get_sender(self):
        """
        Randomly finds and returns a sender for a transaction who has a
        balance > 0

        Parameters:
            self : the instance of the class

        Returns:
            sender_idx : the index of the sender in the self.users list
            sender : the sender, which is a dictionary containing the sender
                     name and balance
        """
        # Initialize sender, sender_idx, and the sender's balance
        sender = {}
        sender_idx = -1
        user_balance = -1

        # Loop until we find a sender with a balance > 0
        while user_balance < 1:
            sender_idx = random.randint(0, 4)
            sender = self.users[sender_idx]
            user_balance = sender['balance']

        # Return the sender index and the sender dictionary
        return sender_idx, sender

    def start_new_block(self, dest_ledger):
        """
        Performs a crypto-mining contest to create a new block

        Parameters:
            self : the instance of the class
            dest_ledger : the ledger object to which the new block will be
                          added

        Returns:
            N/A
        """
        # The names of all miners
        miner_names = ['Alice', 'Bob', 'Charlie']
        # Stores all miner objects
        miners = {}
        # Stores the elapsed time for each miner
        elapsed = {}

        logger.info('%s: Initiating mining to start new block...', __name__)

        # Loop through the list of miner names and direct each to mine
        for miner_name in miner_names:
            elapsed[miner_name] = self.do_mining(miner_name, miners)

        # See who finished first
        winner = min(elapsed, key=elapsed.get)
        logger.info('%s: The winning miner is %s', __name__, winner)

        # Get the block header from winning miner object and add the block
        # header to the new block
        logger.info('%s: Adding header to new block. Header: %s', __name__,
                    miners[winner].block_hdr)
        dest_ledger.add_block_header(miners[winner].block_hdr)

        # Get the resulting hash from winning miner object and save the hash
        # so it can be included in the header when the next block is created
        logger.info('%s: Setting previous hash to: %s', __name__,
                    miners[winner].hash_hex)
        self.prev_hash = miners[winner].hash_hex

    def do_mining(self, miner_name, miners):
        """
        Performs crypto-mining by an individual miner

        Parameters:
            self : the instance of the class
            miner_name : the name of the miner who will be mining
            miners : a dictionary that this method populates with individual
                     miners

        Returns:
            elapsed : the elapsed time for the miner
        """
        # Create the miner object with the specified name
        current_miner = miner.Miner(miner_name)

        # Add the miner to the miners dictionary
        miners[miner_name] = current_miner

        # Initiate mining
        logger.info('%s: Miner %s is going to work...', __name__, miner_name)
        try:
            start = time.time()
            current_miner.do_work(self.prev_hash)
            end = time.time()

            # Upon completion of mining, calculate elapsed time
            elapsed = end - start
            logger.info('%s: %s finished mining with elapsed time: %s',
                        __name__, miner_name, elapsed)
        except Exception as e:
            logger.error('Error for miner %s when mining. Msg: %s',
                         miner_name, e)

        # Return the elapsed time
        return elapsed
