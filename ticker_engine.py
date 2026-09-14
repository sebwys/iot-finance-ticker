import yfinance as yf
from datetime import datetime, timezone, timedelta


class TickerEngine:

    def __init__(self, watchlist):
        self.watchlist = watchlist
        self.fired = {}
        self.last_price = {}
        for item in watchlist:
            self.fired[item['ticker']] = {'above': False, 'below': False}

    def refresh(self):
        prices = {}
        new_alerts = []
        ts = datetime.now(timezone.utc).isoformat()

        for item in self.watchlist:
            symbol = item['ticker']
            try:
                price = float(yf.Ticker(symbol).fast_info['lastPrice'])
            except Exception as e:
                print(f"fetch failed {symbol}: {e}")
                continue

            prev = self.last_price.get(symbol)
            if prev is None or price == prev:
                direction = 'flat'
            elif price > prev:
                direction = 'up'
            else:
                direction = 'down'
            self.last_price[symbol] = price

            prices[symbol] = {
                'price': price,
                'name': item['name'],
                'alert_above': item['alert_above'],
                'alert_below': item['alert_below'],
                'direction': direction,
            }

            above = item['alert_above']
            below = item['alert_below']

            # only fire on the crossing, not while still above
            if price >= above and not self.fired[symbol]['above']:
                new_alerts.append(self._make_alert(item, price, above, 'above', ts))
                self.fired[symbol]['above'] = True
            elif price < above:
                self.fired[symbol]['above'] = False

            if price <= below and not self.fired[symbol]['below']:
                new_alerts.append(self._make_alert(item, price, below, 'below', ts))
                self.fired[symbol]['below'] = True
            elif price > below:
                self.fired[symbol]['below'] = False

        return prices, new_alerts

    def _make_alert(self, item, price, threshold, direction, ts):
        return {
            'ticker': item['ticker'],
            'name': item['name'],
            'price': price,
            'threshold': threshold,
            'direction': direction,
            'timestamp': ts,
        }

    def market_open(self):
        # us equities mon-fri 9:30 to 16:00 ET
        # rough dst: mar-nov is edt (utc-4), else est (utc-5)
        now = datetime.now(timezone.utc)
        offset = -4 if 3 <= now.month <= 11 else -5
        local = now + timedelta(hours=offset)
        if local.weekday() >= 5:
            return False
        m = local.hour * 60 + local.minute
        return 9 * 60 + 30 <= m < 16 * 60
