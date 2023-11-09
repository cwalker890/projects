import json
import os.path
from datetime import datetime
import logging
import logging.config
import boto3

# Define logger
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('ledger')

s3_client = boto3.client('s3')
s3 = boto3.resource('s3')
bucket = "cory-walker-blockchain"

class Ledger(object):
    """
    A class representing a ledger, which is a record of financial/blockchain
    transactions

    """
    def __init__(self, filedir):
        """
        Initializes the blockchain object with the specified file directory
        Creates a unique blockchain file directory
        Sets currrent tid to 0
        Sets current transaction count to 0
        Sets current file number to 0
        Sets the name of the initial blockchain file
        Creates the blockchain directory if it does not exist

        Parameters:
            self : the instance of the class
            filedir : the path to the directory where the blockchain data will
                      be stored

        Returns:
            N/A
        """
        self.now = datetime.now()
        self.dt_str = self.now.strftime("%Y%m%d_%H%M%S")
        self.filedir = filedir + '_' + self.dt_str

        self.current_tid = 0
        self.trans_count = 0
        self.filenum = 0

        self.set_current_filename()

    def from_file(self, filename):
        """
        Pulls a Json files and converts it into a ledger object

        Parameters:
            self : the instance of the class
            filename: The name of the Json file

        Returns:
            ledger_data: The json ledger data
        """
        # Define ledger data dictionary
        ledger_data = {'hdr': {}, 'transactions': []}
        try:
            # Open file and use JSON load function to read into ledger data
            # dictionary
            s3_object = s3_client.get_object(
                Bucket=bucket,
                Key=filename
            )
            obj = s3.Object(bucket, filename)
            data = obj.get()['Body'].read().decode('utf-8')
            ledger_data = json.loads(data)

            #if os.path.exists(filename):
            #    with open(filename, encoding='utf-8') as infile:
            #        ledger_data = json.load(infile)       
        except FileNotFoundError:
            logger.exception("The file could not be found: %s", filename)
        except TypeError as e:
            logger.exception(
                "TypeError occurred while trying to read from file. Msg: %s",
                e)
        except Exception as e:
            pass
        return ledger_data

    def to_file(self, ledger_data, filename):
        """
        Writes ledger data entry(ies) to Json file

        Parameters:
            self : the instance of the class
            ledger_data: The Json ledger data
            filename: The name of the Json file

        Returns:
            N/A
        """
        try:
            # Use JSON dumps function to read into JSON object, then write
            # JSON object to file
            json_obj = json.dumps(ledger_data, indent=4)
            s3_client.put_object(
                Bucket=bucket,
                Body=json_obj,
                Key=filename
            )
            
            #with open(filename, "w", encoding='utf-8') as outfile:
            #    outfile.write(json_obj)
        except TypeError as e:
            logger.exception(
                "TypeError occurred while trying to write to file. Msg: %s", e)
        except FileNotFoundError:
            logger.exception("The file" + str(filename) + " was not found.")
        except Exception as e:
            logger.debug("An unknown exception has occurred in to file: %s", e)

    def add_block_header(self, block_header):
        """
        Adds a header to a new block

        Parameters:
            self : the instance of the class
            block_header : the header (dictionary) being added

        Returns:
            N/A
        """
        # Get data from current file
        ledger_data = self.from_file(self.filename)

        # Add the block header to the file
        try:
            ledger_data['hdr'] = block_header
        except Exception as e:
            logger.debug("An unknown exception has occurred: " + str(e))

        # Write file
        self.to_file(ledger_data, self.filename)

    def add_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction

        Parameters:
            self : the instance of the class
            sender: The name of the person sending the amount
            recipient: The name of the person receiving the specified amount
            amount: The number amount that the transaction is sending

        Returns:
            new_tid: The new transaction id created from the transaction
        """
        new_tid = self.current_tid

        # Create new transaction
        try:
            new_transaction = {'tid': new_tid, 'sender': sender,
                               'receiver': recipient, 'amount': amount}
        except KeyError:
            logger.exception(
                "The incorrect key was used for the new transaction")
        except Exception as e:
            logger.exception('Error occurred. Exception is: %s', e)

        # Add new transaction
        logger.debug('Adding new transaction: %s', new_transaction)
        self.do_add(new_transaction)

        return new_tid

    def cancel_transaction(self, tid):
        """
        Validates transaction id exists and then creates a cancelled
        transaction record

        Parameters:
            self : the instance of the class
            tid: The transaction id to be cancelled

        Returns:
            new_tid: The newly created cancelld transaction id
        """
        if self.transaction_exists(tid):
            # Set transaction ID for cancellation transaction
            new_tid = self.current_tid
            try:
                # Create cancellation transaction
                cancelled_transaction = {'tid': new_tid, 'cancelled_tid': tid}
            except KeyError:
                logger.exception(
                    "The wrong key was used for the cancelled transaction")
            except Exception as e:
                logger.debug('Error occurred. Exception marked as: %s', e)

            logger.debug('Adding cancellation: %s', cancelled_transaction)
            # Add cancellation transaction
            self.do_add(cancelled_transaction)

            return new_tid

        return -1

    def do_add(self, transaction):
        """
        Common function to use between add_transaction and cancel_transaction
        to write data to json file based on current blockchain location or
        create new blockchain file

        Parameters:
            self : the instance of the class
            transaction: The transaction to be added or cancelled

        Returns:
            N/A
        """
        # Get data from current file
        ledger_data = self.from_file(self.filename)

        # Append transaction to ledger data
        ledger_data['transactions'].append(transaction)

        # Writer/rewrite to file
        self.to_file(ledger_data, self.filename)

        # Increment current ID
        self.current_tid += 1

        # Increment transaction count
        self.trans_count += 1

        # If transaction count is now 256, append next block to the end of
        # the current block file, set name for the new block file, and reset
        # the transaction count to 0
        if self.trans_count == 256:
            self.filenum += 1
            self.add_next_block()
            self.set_current_filename()
            self.trans_count = 0
            logger.debug('Transitioning to next block: %s', self.filename)

    def add_next_block(self):
        """
        Adds the next block entry to the current block chain file

        Parameters:
            self : the instance of the class

        Returns:
            N/A
        """
        # Get data from current block file
        ledger_data = self.from_file(self.filename)

        # Append next block to ledger data
        try:
            ledger_data['next_block'] = 'block_' + str(self.filenum) + '.json'
        except Exception as e:
            logger.debug("An unknown exception has occurred in add_next_block: " + str(e))

        # Writer/rewrite file
        self.to_file(ledger_data, self.filename)

    def transaction_count(self):
        """
        Calculates total number of valid transactions found in the blockchain

        Parameters:
            self : the instance of the class

        Returns:
            The total number of valid transactions in the blockchain file
        """
        count = 0
        # Iterate through files using generator method
        for f in self.yield_block_files(self.filedir):
            print(f)
            # Get ledger data from file
            ledger_data = self.from_file(f)
            # Iterate through transactions in file
            for t in ledger_data['transactions']:
                # If transaction does not contain 'cancelled_tid', increment
                # count variable
                if not(t.__contains__('cancelled_tid')):
                    count += 1
        return count

    def cancelled_transaction_count(self):
        """
        Calculates the total number of cancelled transactions found in the
        blockchain

        Parameters:
            self : the instance of the class

        Returns:
            Total numbers of cancelled transactions
        """
        count = 0
        # Iterate through files using generator method
        for f in self.yield_block_files(self.filedir):
            # Get ledger data from file
            ledger_data = self.from_file(f)
            # Iterate through transactions in file
            for t in ledger_data['transactions']:
                # If transaction contains 'cancelled_tid', increment
                # count variable
                if(t.__contains__('cancelled_tid')):
                    count += 1
        return count

    def net_value(self):
        """
        Calculates the net value of all transactions found in the
        blockchain

        Parameters:
            self : the instance of the class

        Returns:
            The net value of all transactions in the blockchain file
        """
        net = 0
        # Iterate through files using generator method
        for f in self.yield_block_files(self.filedir):
            # Get ledger data from file
            ledger_data = self.from_file(f)
            # Iterate through transactions in file
            for t in ledger_data['transactions']:
                try:
                    # Add transaction amount to net value
                    net += t['amount']
                except:
                    # If entry doesn't contain 'amount' key, skip and continue
                    continue
        return net

    def average_value(self):
        """
        Calculates the average value of all transactions found in the
        blockchain

        Parameters:
            self : the instance of the class

        Returns:
            The average value of all transactions in the blockchain file
        """
        total = 0
        count = 0
        average = 0
        # Iterate through files using generator method
        for f in self.yield_block_files(self.filedir):
            # Get ledger data from file
            ledger_data = self.from_file(f)
            # Iterate through transactions in file
            for t in ledger_data['transactions']:
                try:
                    # Add transaction amount to total and increment count
                    total += t['amount']
                    count += 1
                except:
                    # If entry doesn't contain 'amount' key, skip and continue
                    continue

        # If there are no transactions, prevent division by zero
        if count > 0:
            average = total/count
        return average

    def print_ledger(self):
        """
        Prints all the transactions in the blockchain file

        Parameters:
            self : the instance of the class

        Returns:
            N/A
        """
        print('Transactions:')
        # Iterate through files using generator method
        for f in self.yield_block_files(self.filedir):
            # Get ledger data from file
            ledger_data = self.from_file(f)
            # Iterate through transactions in file and print each transaction
            for t in ledger_data['transactions']:
                print(' ', t)

    def set_current_filename(self):
        """
        Sets the current blockchain filename to the next filename in the
        sequence

        Parameters:
            self : the instance of the class

        Returns:
            N/A
        """
        self.filename = self.filedir + '/block_' + str(self.filenum) + '.json'

    def yield_block_files(self, dir):
        """
        Generator method that yields single block files as a part of a loop
        operation performed by the caller. During each loop iteration by the
        caller, the next block file is returned.

        Parameters:
            self : the instance of the class
            dir : the directory containing the block files

        Returns:
            The next block file
        """
        # Iterate through elements in specified directory and if element is a
        # file, yield the file back to the caller
        response = s3_client.list_objects(
            Bucket=bucket, 
            Prefix=dir
        )
        
        for f in response['Contents']:
            yield f['Key']
        
        #for f in os.listdir(dir):
        #    if os.path.isfile(os.path.join(dir, f)):
        #        yield f
        
    def transaction_exists(self, tid):
        """
        Checks if a transaction with the specified tid exists in the blockchain

        Parameters:
            self : the instance of the class
            tid : transaction id to search for

        Returns:
            True if the transaction with the specified tid exits,
            False otherwise
        """
        for f in self.yield_block_files(self.filedir):
            # Get ledger data from file
            ledger_data = self.from_file(f)
            # Iterate through transactions in file
            for t in ledger_data['transactions']:
                # If tid is found and is not a cancellation, return true/found
                if t['tid'] == tid and not(t.__contains__('cancelled_tid')):
                    return True
        return False

    def get_transaction_count_by_user(self):
        """
        Calculates the number of transactions for each user

        Parameters:
            self : the instance of the class

        Returns:
            transaction_count: This is a dictionary containing how many
            transactions a user has sent or received across the blockchain
        """
        # Define dictionary to maintain transaction counts for users
        transaction_count = {'Alice': 0, 'Bob': 0, 'Jon': 0, 'Howard': 0,
                             'Rocky': 0}

        # Iterate through files using generator method
        for f in self.yield_block_files(self.filedir):
            # Get ledger data from file
            ledger_data = self.from_file(f)
            # Iterate through transactions in file
            for t in ledger_data['transactions']:
                # Increment count sender and receiver
                try:
                    sender = t['sender']
                    receiver = t['receiver']
                    transaction_count[sender] += 1
                    transaction_count[receiver] += 1
                except KeyError:
                    # Skip cancellations
                    continue
                except Exception as e:
                    logger.error(
                        "Unknown exception has occurred: %s", e)

        return(transaction_count)

    def get_debits(self):
        """
        Calculates and returns the sum of all debits for each user

        Parameters:
            self : the instance of the class

        Returns:
            debit_count: This is a dictionary containing the sum of all debits
            for each user
        """
        # Define dictionary to maintain total amount of debits for users
        debit_amounts = {}

        # Iterate through files using generator method
        for f in self.yield_block_files(self.filedir):
            # Get ledger data from file
            ledger_data = self.from_file(f)
            # Iterate through transactions in file
            for t in ledger_data['transactions']:
                # Add transaction amount to total debit amount for receiver
                try:
                    sender = t['sender']
                    amount = t['amount']
                    if sender in debit_amounts:
                        debit_amounts[sender] += amount
                    else:
                        debit_amounts[sender] = amount
                except KeyError:
                    # Skip cancellations
                    continue
                except Exception as e:
                    logger.error(
                        "Unknown exception has occurred: %s", e)

        return(debit_amounts)

    def get_credits(self):
        """
        Calculates and returns the sum of all credits for each user

        Parameters:
            self : the instance of the class

        Returns:
            credit_count: This is a dictionary containing the sum of all
            credits for each user
        """
        # Define dictionary to maintain total amount of credits for users
        credit_amounts = {}

        # Iterate through files using generator method
        for f in self.yield_block_files(self.filedir):
            # Get ledger data from file
            ledger_data = self.from_file(f)
            # Iterate through transactions in file
            for t in ledger_data['transactions']:
                # Add transaction amount to total credit amount for sender
                try:
                    receiver = t['receiver'] 
                    amount = t['amount']
                    if receiver in credit_amounts:
                        credit_amounts[receiver] += amount
                    else:
                        credit_amounts[receiver] = amount
                except KeyError:
                    # Skip cancellations
                    continue
                except Exception as e:
                    logger.error(
                        "Unknown exception has occurred: %s", e)

        return(credit_amounts)
    
    def generate_report(self):
        """
       Generates report of transaction data

        Parameters:
            self : the instance of the class

        Returns:
            N/A
        """
        report = "Blockchain Report - Generated: " + self.now.strftime("%b %d %Y %H:%M:%S %Z") + "\n\n"
        report += "Blockchain File Directory: " + self.filedir + "\n"
        report += "-------------------------------------------"
        report += "-------------------\n\n\n"
        report += "General Statistics\n"
        report += "--------------------------------------------------------------\n"
        report += "Total Transactions:  " + str(self.transaction_count()) + "\n"
        report += "Total Cancellations:  " + str(self.cancelled_transaction_count()) + "\n\n"
        report += "Net Value of All Transactions: " + "${:0,.2f}".format(float(self.net_value())) + "\n"
        report += "Average Value of Transactions: " + "${:0,.2f}".format(float(self.average_value())) + "\n\n\n"
        report += "User Statistics\n"
        report += "--------------------------------------------------------------\n"
        report += "Total Transactions By User:\n"
        user_transactions = self.get_transaction_count_by_user()
        for user in user_transactions:
            report += "  {:<8} {:<10}\n".format(user, user_transactions[user])
        report += "\nTotal Debits By User:\n"
        user_debits = self.get_debits()
        for user in user_debits:
            report += "  {:<8} ${:0.2f}\n".format(user, user_debits[user])
        report += "\nTotal Credits By User:\n"
        user_credits = self.get_credits()
        for user in user_credits:
            report += "  {:<8} ${:0.2f}\n".format(user, user_credits[user])
            
        s3_client.put_object(
            Bucket = bucket,
            Key='report_' + self.dt_str + '.txt',
            Body = report)

