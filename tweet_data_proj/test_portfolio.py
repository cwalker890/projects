import unittest
import portfolio
import pandas as pd
import datetime
import math
import os
import shutil


class TestPortfolio(unittest.TestCase):
    """
    TestPortfolio - unit tests for Portfolio class

    """
    STOCKS_FILE = './src_data/yf_stock_data.csv'
    TWEETS_FILE = './src_data/all_tweets.csv'

    def test_init(self):
        print(' TestPortfolio.test_init')
        test_portfolio = portfolio.Portfolio()
        # Test that DataFrame attribute was created and is empty
        self.assertIsNotNone(test_portfolio.df)
        self.assertEqual(test_portfolio.df.size, 0)

    def test_create_dataframe(self):
        print(' TestPortfolio.test_create_dataframe')
        test_portfolio = portfolio.Portfolio()

        # Test invalid stocks file
        with self.assertRaises(FileNotFoundError):
            df = test_portfolio.create_dataframe('./wrong_stock_file.csv',
                                                 TestPortfolio.TWEETS_FILE)
        # Test invalid twitter file
        with self.assertRaises(FileNotFoundError):
            df = test_portfolio.create_dataframe(TestPortfolio.STOCKS_FILE,
                                                 'wrong_tweets_file')
        # Create DataFrame with valid files
        df = test_portfolio.create_dataframe(TestPortfolio.STOCKS_FILE,
                                             TestPortfolio.TWEETS_FILE)

        # Test that DataFrame was created and contains data
        self.assertIsNotNone(df)
        self.assertNotEqual(df.size, 0)

        # Test that no data is empty
        self.assertFalse(df.isna().any().any())

        # Test that the date range in DataFrame is what we expect
        min_date = df['date'].min()
        self.assertEqual(pd.Timestamp(min_date), pd.to_datetime('1/4/2021'))
        max_date = df['date'].max()
        self.assertEqual(pd.Timestamp(max_date), pd.to_datetime('8/30/2021'))

        # Test that the DataFrame contains 10 unique companies
        num_unique_companies = df['company'].nunique()
        self.assertEqual(num_unique_companies, 10)

    def test_run_backtest(self):
        print(' TestPortfolio.test_run_backtest')
        test_portfolio = portfolio.Portfolio()
        test_portfolio.run_backtest(TestPortfolio.STOCKS_FILE,
                                    TestPortfolio.TWEETS_FILE)
        # Test resulting DataFrame size (1660 rows x 6 col = 9960 cells)
        self.assertEqual(test_portfolio.df.size, 9960)
        # Test that results file was created
        self.assertTrue(os.path.isfile(portfolio.Portfolio.RESULTS_FILE))

    def test_total_value(self):
        print(' TestPortfolio.test_total_value')
        test_portfolio = portfolio.Portfolio()
        test_portfolio.run_backtest(TestPortfolio.STOCKS_FILE,
                                    TestPortfolio.TWEETS_FILE)
        # Test that the total value of certain rows is what we expect
        value = test_portfolio.total_value(datetime.date(2021, 1, 4))
        self.assertEqual(value, 0)
        value = test_portfolio.total_value(datetime.date(2021, 8, 30))
        self.assertTrue(math.isclose(value, 68559.62, rel_tol=1e-2))

    def test_net_gain_or_loss(self):
        print(' TestPortfolio.test_net_gain_or_loss')
        test_portfolio = portfolio.Portfolio()
        test_portfolio.run_backtest(TestPortfolio.STOCKS_FILE,
                                    TestPortfolio.TWEETS_FILE)
        # No way to modify input, so just test that value is what we expect
        net_gain_or_loss = test_portfolio.net_gain_or_loss()
        self.assertTrue(math.isclose(net_gain_or_loss, 10.47, rel_tol=1e-2))

    def test_percent_drawdown(self):
        print(' TestPortfolio.test_percent_drawdown')
        test_portfolio = portfolio.Portfolio()
        test_portfolio.run_backtest(TestPortfolio.STOCKS_FILE,
                                    TestPortfolio.TWEETS_FILE)
        # No way to modify input, so just test that value is what we expect
        drawdown = test_portfolio.percent_drawdown()
        self.assertTrue(math.isclose(drawdown, -85.78, rel_tol=1e-2))


if __name__ == '__main__':
    unittest.main()
