from flask import Flask, request, jsonify
import json
from os import path
import os
import boto3
import mysql.connector

app = Flask(__name__)

AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
AWS_SQS_QUEUE_URL = os.getenv('AWS_SQS_QUEUE_URL')
DB_PASSWORD = os.getenv('MM_CONFIG_db_password')
DB_USERNAME = os.getenv('MM_CONFIG_db_username')
MYSQL_DB_HOST = os.getenv('MYSQL_DB_HOST')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')

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
    
    sqs_send(order)
    sqs_receive()
    mysql_write(order)
    mysql_read()

    orders = load_orders()
    orders.append(order)

    with open(orders_file, 'w') as json_file:
        json.dump(orders, json_file,indent=4,separators=(',',': '))

    s3_save(orders)
    
    return jsonify({'message': 'Order created successfully'}), 201


@app.route('/', methods=['GET'])
def get_orders():
    orders = load_orders()

    print("OS Environments: ")
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))

    return jsonify({'orders': orders}), 201

def s3_save(orders):
    s3_client = boto3.client("s3")

    response = s3_client.put_object(
        Bucket=AWS_S3_BUCKET, Key="orders.json", Body=json.dumps(orders)
    )

    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    if status == 200:
        print(f"Successful S3 put_object response. Status - {status}")
    else:
        print(f"Unsuccessful S3 put_object response. Status - {status}")


def sqs_send(order):
    sqs_client = boto3.client("sqs")

    response = sqs_client.send_message(
        QueueUrl=AWS_SQS_QUEUE_URL,
        DelaySeconds=0,
        MessageAttributes={
            'OrderDate': {
                'DataType': 'String',
                'StringValue': '2023-12-06'
            }
        },
        MessageBody=json.dumps(order)
    )

    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    if status == 200:
        print(f"Successful SQS send_message response. Status - {status}")
    else:
        print(f"Unsuccessful SQS send_message response. Status - {status}")
    
def sqs_receive():
    sqs_client = boto3.client("sqs")

    response = sqs_client.receive_message(
        QueueUrl=AWS_SQS_QUEUE_URL,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )

    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    if status == 200:
        print(f"Successful SQS receive_message response. Status - {status}")
    else:
        print(f"Unsuccessful SQS receive_message response. Status - {status}")

    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']

    sqs_client.delete_message(
        QueueUrl=AWS_SQS_QUEUE_URL,
        ReceiptHandle=receipt_handle
    )

    print('Received and deleted message: %s' % message)

def mysql_read():
    mydb = mysql.connector.connect(
        host=MYSQL_DB_HOST,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        database=MYSQL_DATABASE
    )

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM orders")
    
    result = mycursor.fetchall()
    print('Read MYSQL Orders:')
    for line in result:
        print(line)

def mysql_write(order):
    mydb = mysql.connector.connect(
        host=MYSQL_DB_HOST,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        database=MYSQL_DATABASE
    )

    mycursor = mydb.cursor()

    mycursor.execute("CREATE TABLE IF NOT EXISTS orders (id INT AUTO_INCREMENT PRIMARY KEY, order_data JSON)")

    order_json = json.dumps(order)
    mycursor.execute("INSERT INTO orders (order_data) VALUES (%s)", (order_json,))

    mydb.commit()

@app.route('/health', methods=['GET'])
def check_health():
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
