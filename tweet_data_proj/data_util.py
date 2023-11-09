import pandas as pd
import logging
import logging.config
import datetime


class DataUtil(object):
    """
    DataUtil - Utility class used to process and manipulate source data
    """
    DEFAULT_STOCKS = ['TSLA', 'AMZN', 'GOOGL', 'META', 'MSFT', 'WMT', 'MCD',
                      'DIS', 'NFLX', 'SBUX']
    DATA_DIR = './src_data/'
    STOCK_DATA_FILE = DATA_DIR + 'yf_stock_data.csv'
    TWEETS_FILE = DATA_DIR + 'all_tweets.csv'
    TWEETS_PER_DAY = 10

    @classmethod
    def build_twitter_data(self, stock_list):
        """
        From the twitter data files for each company and the stock data file
        obtained from Yahoo Finance, constructs and saves a single twitter
        file containing tweet info for all companies within the specified
        date range.

        Parameters:
            self : the instance of the DataUtil class

        Returns:
            N/A
        """
        # create dictionary for maintaining a DataFrame for each company
        dataframes = {}

        # Read stock price data from Yahoo Finance. Leave off header.
        fin_data = pd.read_csv(DataUtil.STOCK_DATA_FILE, header=1)
        # Get the number of rows in the financial data
        fin_data_rows = fin_data.shape[0] - 1
        # Multiply by 10 to set the number of tweets for each company
        max_rows = fin_data_rows * DataUtil.TWEETS_PER_DAY

        # Get rid of columns we don't need
        fin_data_mod = fin_data.iloc[1:, :11]
        # Set the header name of the 'Date' column (since it really wasn't a
        # header in the data received from Yahoo)
        fin_data_mod.rename(columns={fin_data_mod.columns[0]: 'date'},
                            inplace=True)

        # Loop through stock symbols
        for stock in stock_list:
            # Read the file containing the twitter data for the company into a
            # DataFrame
            filename = DataUtil.DATA_DIR + stock + '.csv'
            dataframes[stock] = pd.read_csv(filename)

            # Get the number of rows in the twitter data
            size = dataframes[stock].shape[0] - 1
            # Determine how many duplicates of the data we need to make
            dups = int(max_rows/size)
            if max_rows % size != 0:
                dups += 1

            # Duplicate the data received until we reach the number of
            # target rows
            dataframes[stock] = pd.concat([dataframes[stock]]*dups,
                                          ignore_index=True)
            # Truncate the extra rows
            dataframes[stock] = dataframes[stock][:max_rows]

        # Now set the dates for each tweet using the dates from the Yahoo
        # Finance data.
        # First, iterate through the yahoo data in reverse (since that's the
        # same way the data is received from Twitter.
        index = 0
        for i in range(len(fin_data_mod)-1, -1, -1):
            # Get the current row
            row = fin_data_mod.iloc[i]
            # Get the date from the current row
            date = row['date']
            # After getting the date, loop through the company/stock
            # DataFrames
            for stock in stock_list:
                twitter_df = dataframes[stock]
                # Set the date for the stock (set the date from the number of
                # rows specified by TWEETS_PER_DAY
                twitter_df.loc[index:index+DataUtil.TWEETS_PER_DAY,
                               'created_at'] = date
            # Jump to the next set
            index += DataUtil.TWEETS_PER_DAY

        # Now define a final DataFrame that the data from all companies will
        # be appended to
        all_twitter_data = pd.DataFrame()
        # Loop through the companies and append the data to the DataFrame
        for stock in stock_list:
            all_twitter_data = pd.concat([all_twitter_data,
                                          dataframes[stock]])

        # Write the data for all companies out to single file. The dates for
        # each tweet should now be in period Jan 1, 2021 - August 31, 2021.
        # Since the Yahoo Finance data does not include weekends or holidays,
        # we don't have to worry about handling that.
        all_twitter_data.to_csv(DataUtil.TWEETS_FILE, index=False)

DataUtil.build_twitter_data(DataUtil.DEFAULT_STOCKS)
