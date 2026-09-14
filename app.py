import json
import threading
import time
from flask import Flask, render_template, jsonify
from ticker_engine import TickerEngine
from mqtt_publisher import MqttPublisher


with open('config.json') as f:
    config = json.load(f)

engine = TickerEngine(config['watchlist'])
publisher = MqttPublisher(config['mqtt'])
publisher.connect()

state = {'prices': {}, 'alerts': []}
lock = threading.Lock()


def ticker_loop():
    interval = config['refresh_interval_seconds']
    while True:
        try:
            prices, new_alerts = engine.refresh()
        except Exception as e:
            print(f"refresh crashed: {e}")
            time.sleep(interval)
            continue

        with lock:
            state['prices'] = prices
            for alert in new_alerts:
                state['alerts'].insert(0, alert)
            # cap memory so we dont keep alerts forever
            if len(state['alerts']) > 100:
                state['alerts'] = state['alerts'][:100]

        for alert in new_alerts:
            publisher.publish_alert(alert)

        time.sleep(interval)


app = Flask(__name__)


@app.route('/')
def index():
    with lock:
        return render_template(
            'dashboard.html',
            prices=state['prices'],
            alerts=state['alerts'],
            watchlist=config['watchlist'],
            market_open=engine.market_open(),
        )


@app.route('/api/prices')
def api_prices():
    with lock:
        return jsonify({'prices': state['prices'], 'market_open': engine.market_open()})


@app.route('/api/alerts')
def api_alerts():
    with lock:
        return jsonify(state['alerts'])


if __name__ == '__main__':
    t = threading.Thread(target=ticker_loop, daemon=True)
    t.start()
    app.run(host=config['flask']['host'], port=config['flask']['port'])
