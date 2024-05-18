import json
from flask import Flask, jsonify, redirect, request
import requests
import square.client

app = Flask(__name__)

# Exemple : Temporaire
bills = [
    {"id": "1", "amount": 100.0, "due_date": "2024-04-30", "number": "BILL-001"},
    {"id": "2", "amount": 150.0, "due_date": "2024-05-15", "number": "BILL-002"},
    {"id": "3", "amount": 200.0, "due_date": "2024-05-31", "number": "BILL-003"},
]

# On server 5001
@app.route('/bills', methods=['GET'])
def get_bills():
    return jsonify(bills), 200

@app.route('/approve_payment_request', methods=['POST'])
def approve_payment_request():
    data = request.json
    bill_id = data.get('id')
    amount = data.get('amount')
    print(bill_id, amount)
    return jsonify(bill_id, amount)

# Initialize Square client with your sandbox credentials
client = square.client.Client(
    access_token='EAAAlxaYAJkkymNBRmzz7xfSSkk6MUw3Ksb3Q9M24QDhzJ-McqoTLEQM46HbMfqA',
    environment='sandbox'
)

@app.route('/payment', methods=['GET', 'POST'])
def process_payment():
    if request.method == 'GET':
        bill_id = request.args.get('bill_id')
        payment_id = request.args.get('payment_id')
        if payment_id:
            result = client.payments.get_payment(payment_id)
            if result.is_success():
                payment_details = result.body
                notify_api_gateway(payment_details)
                return redirect('https://biller-api.onrender.com/make_payment?bill_id={}&payment_id={}'.format(bill_id, payment_id))
            elif result.is_error():
                return jsonify({"error": "Failed to retrieve payment details: " + str(result.errors)}), 400
        else:
            return jsonify({"error": "Payment ID not provided"}), 400
    elif request.method == 'POST':
        data = request.json
        bill_id = data.get('bill_id')
        payment_id = data.get('payment_id')
        if payment_id:
            result = client.payments.get_payment(payment_id)
            if result.is_success():
                payment_details = result.body
                return redirect('https://biller-api.onrender.com/make_payment?bill_id={}&payment_id={}'.format(bill_id, payment_id))
            elif result.is_error():
                return jsonify({"error": "Failed to retrieve payment details: " + str(result.errors)}), 400
        else:
            return jsonify({"error": "Payment ID not provided"}), 400

def notify_api_gateway(payment_info):
    api_gateway_url = 'https://payment-gateway-api.onrender.com/merchant_approval'
    notification_data = {
        'payment_id': payment_info['payment']['id'],
        'amount': payment_info['payment']['amount_money']['amount'],
        'created_at': payment_info['payment']['created_at'],
    }
    try:
        response = requests.post(api_gateway_url, json=notification_data)
        if response.status_code == 200:
            print("Notification sent successfully to API gateway")
        else:
            print("Failed to send notification to API gateway:", response.text)
    except Exception as e:
        print("Failed to send notification to API gateway:", str(e))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
