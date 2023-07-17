from flask import Flask, redirect, request, jsonify,render_template
import json
import stripe
import psycopg2

app = Flask(__name__,
            static_url_path='',
            static_folder='public')
            
YOUR_DOMAIN = 'http://localhost:4242'
#complte this part with informations
user = "postgres"
password = "???"
stripe.api_key = '????'
product_id = "???"
product_name = "???"
price_amount = 1200
price_id = "???"
cus_id = "?????"
wh_sec = '????'


def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='flask_db',
                            user=user,
                            password=password)
    return conn


def save_subscription(subscription,customer):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE subscriptions (id serial PRIMARY KEY,
                                 sub_id varchar (150) NOT NULL,
                                 customer_id varchar (150) NOT NULL);"""
                                 )
    
    cur.execute('INSERT INTO subscriptions (sub_id, customer_id)'
            'VALUES (%s, %s)',
            (subscription,
             customer,)
            )
    conn.commit()
    cur.close()
    conn.close()


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html',name=product_name, price=price_amount)


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price':  price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
        )
    except Exception as e:
        return str(e)
    return redirect(checkout_session.url, code=303)


@app.route('/webhook', methods=['POST'])
def webhook_received():
    webhook_secret = wh_sec
    request_data = json.loads(request.data)
    if webhook_secret:
        signature = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret)
            data = event['data']
        except Exception as e:
            return e
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']

    data_object = data['object']

    if event_type == 'checkout.session.completed':
        event_subscription_id = event['data']['object']['subscription']
        event_customer_id = event['data']['object']['customer']
        save_subscription(event_subscription_id,event_customer_id)
        return  jsonify({'status': 'success'})
    
    else:
        return jsonify({'status': 400 })


@app.route('/success')
def success_page():
    return "success"

@app.route('/cancel')
def cancle_page():
    return "cancel"

if __name__ == '__main__':
    app.run(debug=True,port=4242)
