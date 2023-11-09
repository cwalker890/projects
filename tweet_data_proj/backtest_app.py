import portfolio
import logging
import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('backtest')


class BacktestApp(object):
    """
    Backtest - Driver application used to run backtesting and test the
               Portfolio class
    """
    def run_backtest(self):
        # Define source data files
        stocks_file = './src_data/yf_stock_data.csv'
        tweets_file = './src_data/all_tweets.csv'

        # Create Portfolio object
        logger.info('Creating Portfolio instance...')
        pf = portfolio.Portfolio()

        # Direct Portfolio objec to run backtest using the provided source
        # data files
        logger.info('Directing portfolio to run a backtest using files '
                    '%s and %s', stocks_file, tweets_file)
        pf.run_backtest(stocks_file, tweets_file)

        print()

        # Get and print the portfolio value for each day in backtest period
        logger.info('Retrieving Portfolio values by day:')
        dates = pf.df['date'].unique()
        for date in dates:
            logger.info('Portfolio value on %s: %s', date,
                        f"${pf.total_value(date):,.2f}")

        print()

        # Get net percent gain or loss
        pct_gain_loss = pf.net_gain_or_loss()
        logger.info(f"Net Gain or Loss: {pct_gain_loss:.2f}%")

        print()

        # Get percent gain or loss
        max_drawdown = pf.percent_drawdown()
        logger.info(f"Maximum drawdown: {max_drawdown:.2f}%")

BacktestApp().run_backtest()
