import ledger
import trangen
import logging
import logging.config

FILE_DIR = '/blockchain_files/'
NUM_TRANSACTIONS = 513

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('test_driver')


def lambda_handler(event, context):
   
    logger.info('Creating new ledger...')
    ledger1 = ledger.Ledger(FILE_DIR)

    # Create and run TranGEN to generate transactions and add them to the
    # ledger
    logger.info(
        'Creating tranGEN and attempting to generate transactions...')
    tg = trangen.TranGEN()
    tg.generate_transactions(ledger1, NUM_TRANSACTIONS)

    # Display the transaction count
    logger.info('Total transaction count: %d',
                ledger1.transaction_count())

    # Display the cancelled transaction count
    logger.info('Cancelled transaction count: %d',
                ledger1.cancelled_transaction_count())

    # Displays net value of transactions
    logger.info('Net value of transactions: %s',
                "${:0,.2f}".format(float(ledger1.net_value())))

    # Displays average amount from transactions
    logger.info('Average value of transactions: %s',
                "${:0,.2f}".format(float(ledger1.average_value())))

    # Displays transaction count by user
    logger.info('Transactions by user: %s',
                ledger1.get_transaction_count_by_user())
        # Displays total amount of debits by user
    logger.info('Debit amounts by user: %s', ledger1.get_debits())
        # Displays total amount of credits by user
    logger.info('Credit amounts by user: %s', ledger1.get_credits())

    ledger1.generate_report()
    
    return {
        "statusCode": 200,
        "body": "hi "
    }