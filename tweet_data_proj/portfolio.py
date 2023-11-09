import logging
import logging.config
import pandas as pd
import numpy as np

# Define logger
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('portfolio')


class Portfolio(object):
    """
    A class representing a stock portfolio, or collection of stocks

    """
    INITIAL_WALLET = 1000000
    BUY_THRESHOLD = 0.35
    SELL_THRESHOLD = 0.65
    RESULTS_FILE = 'backtest_results.csv'

    def __init__(self):
        logger.info('Initializing Portfolio instance...')
        self.df = pd.DataFrame()

    def create_dataframe(self, stocks_file, tweets_file):
        """
        Creates the dataframe used in backtesting from the stock financial
        and the Twitter file. In general, this method reads both files into
        Pandas dataframes, removes all unnecessary columns, and merges the
        stock price from the Yahoo finance file with the contents of the
        Twitter file. The resulting merged dataframe is then sorted and
        grouped by Date and Company Stock Symbol.

        Parameters:
            self : the instance of the Portfolio class

        Returns:
            ret_df : the resulting DataFrame object to be used in backtesting
        """
        logger.info('Running create_dataframe()...')

        logger.info('Reading the financial data from: %s...', stocks_file)

        try:
            # Read the Yahoo Finance file into a DataFrame
            fin_data = pd.read_csv(stocks_file, header=1)

        except FileNotFoundError:
            logger.exception(
                "The stock information file could not be found: %s",
                stocks_file
            )
            raise
        except TypeError as e:
            logger.exception(
                "A TypeError occurred while trying to read from file %s. "
                "Error Msg: %s", stocks_file, e
            )
        except Exception as e:
            logger.debug(
                "An unknown error occurred when trying to read the stock "
                "information file %s. Error Msg: %s", stocks_file, e
            )

        # Remove unnecessary columns
        fin_data_mod = fin_data.iloc[1:, :11]

        # Update date column header and convert date strings to datetime
        # objects
        fin_data_mod.rename(columns={fin_data_mod.columns[0]: 'date'},
                            inplace=True)
        fin_data_mod['date'] = pd.to_datetime(fin_data_mod['date'])

        # Set the index for the DataFrame
        fin_data_mod.set_index('date', inplace=True)

        logger.info('Reading the Twitter data from: %s...', tweets_file)
        try:
            # Read the Twitter file into a DataFrame
            twitter_data = pd.read_csv(tweets_file)

        except FileNotFoundError:
            logger.exception(
                "The twitter file could not be found: %s", tweets_file
            )
            raise
        except TypeError as e:
            logger.exception(
                "A TypeError occurred while trying to read from file %s. "
                "Error Msg: %s", tweets_file, e
            )
        except Exception as e:
            logger.debug(
                "An unknown error occurred when trying to read the Twitter "
                "file %s. Error Msg: %s", tweets_file, e
            )

        # Remove the 'tweet' text column since it's unnecessary
        twitter_data = twitter_data.drop('tweet', axis=1)

        # Update data column header, remove time from the date strings, and
        # convert date strings to datetime objects
        twitter_data.rename(columns={'created_at': 'date'}, inplace=True)
        twitter_data['date'] = twitter_data['date'].str.slice(stop=10)
        twitter_data['date'] = pd.to_datetime(twitter_data['date'])

        # Add a 'price' column
        twitter_data['price'] = ''

        logger.info('Merging data from the two files...')
        # Set the price for each tweet from the data in the Yahoo Finance file
        for index, row in twitter_data.iterrows():
            try:
                company = row['company']
                dt = row['date']
                twitter_data.at[index, 'price'] = fin_data_mod.loc[
                    pd.Timestamp(dt), company]
            except KeyError:
                logger.debug(
                    "The incorrect key was used when iterating through "
                    "the twitter data"
                )
            except Exception as e:
                logger.error(
                    "An unknown error has occured while itterating through "
                    "twitter data: %s", e
                )
        # Convert date string to datetime object
        twitter_data['date'] = pd.to_datetime(twitter_data['date']).dt.date

        logger.info('Sorting and grouping the backtesting data...')
        try:
            # Sort the merged data by date and then company symbol
            twitter_data = twitter_data.sort_values(by=['date', 'company'])

            # Group the data by date and company. Also add a column containing
            # the mean ratio for each company on each date, as well as a
            # column containing the stock price on that date.
            ret_df = twitter_data.groupby(['date', 'company']).agg(
                {'ratio': 'mean', 'price': 'first'}).reset_index()
        except KeyError:
            logger.debug(
                "The incorrect key was used when grouping together data"
            )
        except Exception as e:
            logger.error(
                "An unknown error has occured when grouping data "
                "together: %s", e
            )
        # Add additional columns that will be needed in backtesting
        ret_df['wallet'] = ''
        ret_df['portfolio'] = ''

        return ret_df

    def run_backtest(self, stocks_file, tweets_file):
        """
        Runs a backtest based on the stock financial data and Twitter files
        provided as input.

        Parameters:
            self : the instance of the Portfolio class
            stocks_file : the stock file containing financial information
                          for a set of stocks
            tweeets_file : a file containing tweet information that can be
                           used in the determining sentiment towards stocks

        Returns:
            N/A
        """
        logger.info('Running run_backtest()...')

        wallet = 1000000
        portfolio_value = 0

        # Create the DataFrame attribute that will contain the backtest
        # data and results
        try:
            self.df = self.create_dataframe(stocks_file, tweets_file)
        except Exception as e:
            logger.error(
                "An unknown error occurred when creating dataframe: %s", e
            )

        # Create a dictionary consisting of the following:
        # stock_shares = {'AMZN': {'shares': 0, 'share_price': 0},
        #                 'DIS': {'shares': 0, 'share_price': 0},
        #                 'GOOGL': {'shares': 0, 'share_price': 0},
        #                 ...}
        stock_list = self.df['company'].unique()
        stock_shares = {stock: {'shares': 0, 'share_price': 0}
                        for stock in stock_list}

        logger.info('Processing the backtest data...')
        # Loop through the DataFrame attribute
        for index, row in self.df.iterrows():

            # Determine the buy/sell price of the stock on this row
            buysell_price = (row.loc['price'] * 100)

            # Buy or sell if the ratio meets the sentiment threshold
            if row.loc['ratio'] <= Portfolio.BUY_THRESHOLD:
                # Only buy if we have the funds and we don't already own
                # 100 shares
                if wallet > buysell_price and \
                   stock_shares[row.loc['company']]['shares'] == 0:

                    # Debit the wallet
                    wallet -= buysell_price

                    # Increase the portfolio value by the total purchase price
                    portfolio_value += buysell_price

                    # Update the shares dictionary with the shares owned for
                    # each stock (0 or 100)
                    try:
                        stock_shares[row.loc['company']]['shares'] = 100
                    except KeyError:
                        logger.debug(
                            "An incorrect key was used when updating the "
                            "number of shares in the shares dictionary"
                        )
                    except Exception as e:
                        logger.error(
                            "An unknown exception occured when updating the "
                            "number of shares in the shares dictionary: %s", e
                        )

                    # Update the shares dictionary with the share price for
                    # the purchase
                    try:
                        stock_shares[row.loc['company']]['share_price'] = \
                            row.loc['price']
                    except KeyError:
                        logger.debug(
                            "An incorrect key was used when updating the "
                            "stock price in the shares dictionary."
                        )
                    except Exception as e:
                        logger.error(
                            "An unknown exception occured when updating the "
                            "stock price in the shares dictionary: %s", e
                        )

            elif row.loc['ratio'] >= Portfolio.SELL_THRESHOLD:
                # Only sell if we own shares
                if stock_shares[row.loc['company']]['shares'] > 0:

                    # Credit the wallet
                    wallet += buysell_price

                    # Decrease the portfolio value by the total sell price
                    portfolio_value -= buysell_price

                    # Now see if we made or lost money. First get the original
                    # share price from the stock shares dictionary and
                    # multiply by 100 shares
                    try:
                        orig_purchase_price = \
                            stock_shares[
                                row.loc['company']]['share_price'] * 100
                    except KeyError:
                        logger.debug(
                            "An incorrect key was used when attempting to "
                            "retrieve the original stock purchase price from "
                            "the shares dictionary"
                        )
                    except Exception as e:
                        logger.error(
                            "An unknown error occured when when attempting "
                            "to retrieve the original stock purchase price "
                            "from the shares dictionary: %s", e
                        )
                    # Determine net gain or loss
                    net_gain_loss = buysell_price - orig_purchase_price

                    # Apply net gain or loss to the portfolio value
                    portfolio_value += net_gain_loss

                    # Clear the shares data in the shares dictionary since we
                    # just sold our 100 shares
                    try:
                        stock_shares[row.loc['company']]['shares'] = 0
                        stock_shares[row.loc['company']]['share_price'] = 0
                    except KeyError:
                        logger.debug(
                            "An incorrect key was used when attempting to "
                            "reset the shares data in the shares dictionary"
                        )
                    except Exception as e:
                        logger.error(
                            "An unknown error occured when attempting to "
                            "reset the shares data in the shares dictionary: "
                            "%s", e
                        )
            try:
                # Update the wallet column in the DataFrame
                self.df.at[index, 'wallet'] = wallet

                # Update the portfolio column in the DataFrame
                self.df.at[index, 'portfolio'] = portfolio_value

            except KeyError:
                logger.debug(
                    "An incorrect key was used when attempting to set the "
                    "wallet and portfolio values in the dataframe."
                )
            except Exception as e:
                logger.error(
                    "An unknown error occured when attempting to set the "
                    "wallet and portfolio values in the dataframe.: %s", e
                )

        logger.info('Backtesting complete. Results can be viewed in: %s',
                    Portfolio.RESULTS_FILE)
        try:
            # Write the backtest results to a csv file
            self.df.to_csv(Portfolio.RESULTS_FILE, index=False)

        except FileNotFoundError:
            logger.exception(
                "The file could not be found: %s", Portfolio.RESULTS_FILE
            )
        except ValueError as e:
            logger.exception(
                "A ValueError occurred while trying to write to file %s. "
                "Error Msg: %s", Portfolio.RESULTS_FILE, e
            )
        except Exception as e:
            logger.debug(
                "An unknown error occurred when trying to write to the file "
                "%s. Error Msg: %s", Portfolio.RESULTS_FILE, e
            )

    def total_value(self, date):
        """
        Retrieves the last portfolio value for a specified date

        Parameters:
            self : the instance of the Portfolio class
            date : a specified date to retrieve last portfolio value

        Returns:
            The last portfolio value for the specified date in the form of a
            float or an error if the value cannot be retrieved
        """
        last_value = None

        try:
            # Select rows with the specifed date and read into series
            df_date = self.df.loc[self.df['date'] == date]

            # Get the last row for that set of dates (i.e., the row with the
            # last 'portfolio' value)
            last_value = df_date.tail(1)['portfolio'].iloc[0]

        except KeyError:
            logger.debug(
                "An incorrect key was used when attempting to retrieve the "
                "last row for the specified date."
            )
        except Exception as e:
            logger.error(
                "An unknown error occured when attempting to retrieve the "
                "last row for the specified date.: %s", e
            )

        # Return the result
        return last_value

    def net_gain_or_loss(self):
        """
        Calculates the net percentage gain or loss for a backtesting result

        Parameters:
            self : the instance of the Portfolio class

        Returns:
            A float representing the net gain or loss for the backtesting
            result or an error if the value could not be calculated
        """
        logger.info('Running net_gain_or_loss()...')

        try:
            # Select last row in the backtesting result DataFrame object
            last_row = self.df.iloc[-1]

        except IndexError:
            logger.debug(
                "An index error occured when attempting to retrieve the "
                "last row from the dataframe"
            )
        except Exception as e:
            logger.error(
                "An unknown error occured when attempting to retrieve the "
                "last row from the dataframe: %s", e
            )

        try:
            # Determine the total amount spent on stock purchases over the
            # course of the backtest
            total_spent = Portfolio.INITIAL_WALLET - last_row['wallet']

            # Determine the profit (or loss) by subtracting the $1M starting
            # balance from the sum of the last 'wallet' value and the last
            # 'portfolio' value
            last_wallet = last_row['wallet']
            last_portfolio = last_row['portfolio']
            logger.info('Initial budget: %s',
                        f"${Portfolio.INITIAL_WALLET:,.2f}")
            logger.info('Remaining budget at end of backtest: %s',
                        f"${last_wallet:,.2f}")
            logger.info('Portfolio value at end of backtest: %s',
                        f"${last_portfolio:,.2f}")
            logger.info('Sum of remaining budget and portfolio value: %s',
                        f"${(last_wallet + last_portfolio):,.2f}")

            profit = (last_wallet + last_portfolio) - Portfolio.INITIAL_WALLET
            logger.info('Net gain or loss: %s', f"${profit:,.2f}")

        except KeyError:
            logger.debug(
                "An incorrect key was used when attempting to calculate the "
                "net gain or loss."
            )
        except Exception as e:
            logger.error(
                "An unknown error occured when attempting to calculate the "
                "net gain or loss: %s", e
            )
        # Initially set result to 0
        pct_gain_loss = 0

        # Divide the profit by the amount spent to determine the gain or loss
        if total_spent > 0:
            pct_gain_loss = (profit / total_spent) * 100

        # Return the result
        return pct_gain_loss

    def percent_drawdown(self):
        """
        Calculates the maximum percentage drawdown for a backtesting result

        Parameters:
            self : the instance of the portfolio class

        Returns:
            A float representing the maximum percentage drawdown for the
            backtesting result
        """
        logger.info('Running percent_drawdown()...')

        # find the index of the first non-zero value
        start_index = (self.df['portfolio'] != 0).idxmax()

        # slice off the initial rows containing zeros
        df_mod = self.df[start_index:]

        # calculate the peak value
        peak_value = df_mod['portfolio'].cummax()

        # calculate the drawdown
        drawdown = (df_mod['portfolio'] - peak_value) / peak_value * 100

        # calculate the maximum drawdown
        max_drawdown = drawdown.min()

        # Return the result
        return max_drawdown
