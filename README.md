# iot finance ticker

built as a cs437 (internet of things) final project. a raspberry pi pulls live
prices via yfinance and evaluates thresholds locally. flask serves a dashboard
sized for a phone. alerts ship to aws iot core, which logs them in dynamodb.

## setup

drop the aws iot certs into `certs/`:
- root-CA.crt
- device.pem.crt
- device.pem.key

copy `config.example.json` to `config.json` and edit the tickers, thresholds,
and the aws iot endpoint. `config.json` and `certs/` are gitignored.

install deps in a venv:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## run

```
python app.py
```

then open `http://<pi-ip>:5001` from a phone on the same wifi. the port is set
in `config.json`.

if `certs/` is empty the app skips the mqtt step and the dashboard runs
without the aws side.

## files

- `app.py` flask server + background ticker thread
- `ticker_engine.py` yfinance polling, threshold logic, market hours
- `mqtt_publisher.py` paho-mqtt over tls, does nothing if no certs
- `templates/dashboard.html` the mobile dashboard page
- `static/style.css` dark theme, mobile friendly
- `lambda/alert_logger.py` aws lambda that writes alerts to dynamodb
- `config.example.json` watchlist, thresholds, mqtt and flask config

## aws side (one time)

1. create a thing named `pi-finance-ticker`
2. download the certs
3. policy: allow `iot:Publish` on `finance/alerts` and `iot:Connect`
4. iot rule: `SELECT * FROM 'finance/alerts'` to invoke the lambda
5. lambda from `lambda/alert_logger.py`, give it dynamodb write
6. dynamodb table `FinanceAlerts`, partition key `ticker` (string),
   sort key `timestamp` (string)
