import aiohttp
from typing import Dict, Any


class StockAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    async def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        params['apikey'] = self.api_key
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                return await response.json()

    async def get_stock_info(self, symbol: str) -> str:
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        data = await self._make_request(params)

        if not data or "Error Message" in data:
            return "מידע לא נמצא"

        return (f"מידע על {symbol}:\n"
                f"מחיר נוכחי: ${data.get('Price', 'N/A')}\n"
                f"שיא 52 שבועות: ${data.get('52WeekHigh', 'N/A')}\n"
                f"שפל 52 שבועות: ${data.get('52WeekLow', 'N/A')}")

    async def get_sentiment(self, symbol: str) -> str:
        params = {
            'function': 'NEWS_SENTIMENT',
            'symbol': symbol
        }
        data = await self._make_request(params)

        if "feed" not in data:
            return "לא נמצאו חדשות"

        news = []
        for article in data["feed"][:3]:
            news.append(
                f"כותרת: {article['title']}\n"
                f"סנטימנט: {article['overall_sentiment_label']} "
                f"({article['overall_sentiment_score']})"
            )
        return "\n\n".join(news)

    async def get_holdings(self, symbol: str) -> str:
        # First check if ETF
        etf_params = {
            'function': 'ETF_HOLDINGS',
            'symbol': symbol
        }
        data = await self._make_request(etf_params)

        if "holdings" in data:
            holdings = []
            for holding in data["holdings"][:5]:
                holdings.append(
                    f"מניה: {holding['ticker']} ({holding['name']})\n"
                    f"אחוז מהתיק: {holding['weight']}%"
                )
            return "החזקות הקרן:\n\n" + "\n\n".join(holdings)

        # If not ETF, get institutional holders
        params = {
            'function': 'INSTITUTIONAL_HOLDERS',
            'symbol': symbol
        }
        data = await self._make_request(params)

        if "institutionalHolders" not in data:
            return "לא נמצאו נתוני החזקות"

        holders = []
        for holder in data["institutionalHolders"][:5]:
            holders.append(
                f"שם: {holder['name']}\n"
                f"מניות: {holder['shares']}\n"
                f"אחוז החזקה: {holder['percentage']}%"
            )
        return "מחזיקים מוסדיים:\n\n" + "\n\n".join(holders)

    async def get_earnings(self, symbol: str) -> str:
        params = {
            'function': 'EARNINGS_CALENDAR',
            'symbol': symbol
        }
        data = await self._make_request(params)

        if "earnings" not in data:
            return "לא נמצאו נתוני רווחים"

        earnings = []
        for earning in data["earnings"][:3]:
            earnings.append(
                f"תאריך: {earning['reportDate']}\n"
                f"EPS צפוי: ${earning.get('estimatedEPS', 'N/A')}\n"
                f"EPS בפועל: ${earning.get('reportedEPS', 'N/A')}"
            )
        return "דוחות כספיים:\n\n" + "\n\n".join(earnings)

    async def get_dividend(self, symbol: str) -> str:
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        data = await self._make_request(params)

        if not data or "Error Message" in data:
            return "לא נמצא מידע על דיבידנדים"

        return (f"מידע על דיבידנדים {symbol}:\n"
                f"תשואת דיבידנד: {data.get('DividendYield', 'N/A')}%\n"
                f"תאריך אקס-דיבידנד: {data.get('ExDividendDate', 'N/A')}\n"
                f"תדירות: {data.get('DividendPerShare', 'N/A')} לרבעון")