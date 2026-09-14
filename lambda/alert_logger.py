import json
import boto3


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('FinanceAlerts')


def lambda_handler(event, context):
    try:
        # iot rule sends the payload as event dict
        alert = event if isinstance(event, dict) else json.loads(event)
        item = {
            'ticker': alert['ticker'],
            'timestamp': alert['timestamp'],
            'name': alert.get('name', ''),
            'price': str(alert['price']),
            'threshold': str(alert['threshold']),
            'direction': alert['direction'],
        }
        table.put_item(Item=item)
        return {'status': 'ok'}
    except Exception as e:
        print(f"log failed: {e}")
        return {'status': 'error', 'msg': str(e)}
