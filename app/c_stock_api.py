from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.alphaintelligence import AlphaIntelligence


class StockAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ts = TimeSeries(key=api_key, output_format='json')
        self.fd = FundamentalData(key=api_key, output_format='json')
        self.ai = AlphaIntelligence(key=api_key, output_format='json')

    def get_stock_info(self, symbol):
        """
        Retrieves general stock information, including price, volume, etc.
        """
        try:
            data, _ = self.ts.get_quote_endpoint(symbol)
            return data
        except Exception as e:
            return {"error": str(e)}

    def get_sentiment(self, symbol):
        """
        Retrieves news sentiment (limited to the latest fundamental news from Alpha Vantage).
        """
        try:
            news_data, _ = self.ai.get_news_sentiment(symbol)
            return news_data.get("LatestQuarter", "No sentiment data available.")
        except Exception as e:
            return {"error": str(e)}

    def get_top_gainers(self):
        """
        Retrieves the top gainers for the day.
        """
        try:
            data, _ = self.ai.get_top_gainers()
            top_10_df = data.head(10)

            formatted_response = "\n".join(
                [
                    (
                        f"Ticker: {row['ticker']}\n"
                        f"Price: {row['price']}\n"
                        f"Change Amount: {row['change_amount']}\n"
                        f"Change Percentage: {row['change_percentage']}%\n"
                        f"Volume: {row['volume']}\n"
                        "-----------------------------"
                    )
                    for _, row in top_10_df.iterrows()
                ]
            )

            return formatted_response
        except Exception as e:
            return {"error": str(e)}

    def get_top_losers(self):
        """
        Retrieves the top losers for the day.
        """
        try:
            data, _ = self.ai.get_top_losers()
            return data
        except Exception as e:
            return {"error": str(e)}
    def get_holdings(self, symbol):
        """
        Retrieves ETF holdings or equity holders.
        """
        try:
            if symbol.startswith("ETF"):  # Convention for ETF symbols (update if needed)
                data, _ = self.fd.get_etf_sector_performance()
                return data
            else:
                data, _ = self.fd.get_company_overview(symbol)
                return data.get("InstitutionalHolders", "Institutional holders not available.")
        except Exception as e:
            return {"error": str(e)}

    def get_earnings(self, symbol):
        """
        Retrieves earnings data for a stock.
        """
        try:
            data, _ = self.fd.get_earnings(symbol)
            return data
        except Exception as e:
            return {"error": str(e)}

    def get_dividend(self, symbol):
        """
        Retrieves dividend data for a stock.
        """
        try:
            data, _ = self.fd.get_company_overview(symbol)
            return {
                "DividendPerShare": data.get("DividendPerShare", "No dividend data available."),
                "DividendYield": data.get("DividendYield", "No dividend yield available."),
                "ExDividendDate": data.get("ExDividendDate", "No ex-dividend date available."),
                "DividendDate": data.get("DividendDate", "No dividend date available."),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_52week(self, symbol):
        """
        Retrieves the 52-week high and low for a stock.
        """
        try:
            data, _ = self.ts.get_quote_endpoint(symbol)
            return {
                "52_Week_High": data.get("52WeekHigh", "Data not available"),
                "52_Week_Low": data.get("52WeekLow", "Data not available"),
            }
        except Exception as e:
            return {"error": str(e)}


# Example Usage
if __name__ == "__main__":
    api_key = "YOUR_ALPHA_VANTAGE_API_KEY"
    symbol = "AAPL"  # Example: Replace with your stock symbol

    stock_api = StockAPI(api_key)

    print("Stock Info:")
    print(stock_api.get_stock_info(symbol))

    print("\nNews Sentiment:")
    print(stock_api.get_sentiment(symbol))

    print("\nHoldings:")
    print(stock_api.get_holdings(symbol))

    print("\nEarnings:")
    print(stock_api.get_earnings(symbol))

    print("\nDividend Info:")
    print(stock_api.get_dividend(symbol))

    print("\n52-Week High/Low:")
    print(stock_api.get_52week(symbol))
