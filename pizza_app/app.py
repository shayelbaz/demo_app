from flask import Flask, request, jsonify
import json
from os import path
import os
import boto3

app = Flask(__name__)



AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')

# dataPath = os.getenv('DATA_PATH')
# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')

# orders_file = dataPath + "/orders.json"
orders_file = "orders.json"


def load_orders():
    if path.isfile(orders_file) is False:
        print("File not found, Creating...")
        orders = []
        with open(orders_file, 'w') as json_file:
            json.dump(orders, json_file)

    with open(orders_file) as f:
        orders = json.load(f)
    
    return orders


def validate_order(data):
    pizza_type = data['pizza-type']
    size = data['size']
    amount = data['amount']

    available_pizza_type = ['margherita', 'pugliese', 'marinara']
    available_size = ['personal', 'family']

    if pizza_type is None or pizza_type not in available_pizza_type:
        available_values = ', '.join(available_pizza_type)
        return False, jsonify({'error': f'Invalid pizza type {pizza_type}. Please choose the above: {available_values}'}), 400

    if size is None or size not in available_size:
        available_values = ', '.join(available_size)
        return False, jsonify({'error': f'Invalid pizza size {size}. Please choose the above: {available_values}'}), 400

    if amount is None or not isinstance(amount, int):
        return False, jsonify({'error': f'Invalid pizza amount {amount}. must be an integer'}), 400

    return True, None, None


@app.route('/order', methods=['POST'])
def create_order():
    data = request.json

    isValide, responce, statusCode = validate_order(data)
    if not isValide:
        return responce, statusCode

    pizza_type = data['pizza-type']
    size = data['size']
    amount = data['amount']

    order = {
        'pizza-type': pizza_type,
        'size': size,
        'amount': amount
    }

    orders = load_orders()
    orders.append(order)

    with open(orders_file, 'w') as json_file:
        json.dump(orders, json_file,indent=4,separators=(',',': '))

    s3_save(orders)

    return jsonify({'message': 'Order created successfully'}), 201


@app.route('/', methods=['GET'])
def get_orders():
    orders = load_orders()
    return jsonify({'orders': orders}), 201

def s3_save(orders):
    s3_client = boto3.client(
        "s3"
    )

    response = s3_client.put_object(
        Bucket=AWS_S3_BUCKET, Key="orders.json", Body=json.dumps(orders)
    )

    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    if status == 200:
        print(f"Successful S3 put_object response. Status - {status}")
    else:
        print(f"Unsuccessful S3 put_object response. Status - {status}")

@app.route('/health', methods=['GET'])
def check_health():
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
