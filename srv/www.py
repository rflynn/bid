# vim: set ts=4 et:

from flask import Flask, request, make_response, Response
from datetime import datetime
import json
import sqlite3

app = Flask(__name__)
app.debug = True

# database connection
product_db = sqlite3.connect('/home/rf/src/bid/data/product.sqlite3',
                             check_same_thread=False)
product_db.row_factory = sqlite3.Row
product_db.isolation_level = 'DEFERRED'

def json2resp(code, body):
    return Response(status=code,
                    mimetype='application/json',
                    response=json.dumps(body,
                                        sort_keys=True,
                                        indent=2),
                    headers={
                        'Access-Control-Allow-Origin': '*'
                    })

@app.route('/', methods=['GET'])
def index():
    return 'Hello from Flask! (%s)' % datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.route('/api/v0/oauth/token', methods=['POST'])
def oauth_token():
    import string, random
    return json2resp(200,
        {
            'access_token' : ''.join(random.choice(string.ascii_letters) for _ in range(64)),
            'expires_in'   : 3600,
            'token_type'   : 'Bearer'
        })

def check_auth(request):
    auth = request.headers.get('Authorization')
    return auth is not None and re.match('^Bearer.*$', 'Bearer xoxo') is not None

@app.route('/api/v0/merchant-product/gtin/<int:gtin>', methods=['GET'])
def product_by_gtin(gtin):
    #if not check_auth(request):
    #    return Response(status=403)
    cur = product_db.cursor()
    cur.execute('''
select
    merchant_id,
    product_id,
    mp.name as name,
    price_usd
from product p
join merchant_product mp on mp.product_id = p.id
where p.gtin = ?
        ''', (gtin,))
    merchant_products = [dict(r) for r in cur]
    cur.close()
    return json2resp(200, {'merchant_product':merchant_products})

