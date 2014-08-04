# ex: set ts=4 et:

"""
bid_process via WSGI

python -i
import redis
r = redis.Redis('localhost')
>>> r.lrange('bidx', 0, -1)
[]
>>> r.lpush('bid-abc123', 'vendor1:bid1')
1L
>>> r.lpush('bid-abc123', 'vendor2:bid2')
2L
>>> r.lpush('bid-abc123', 'vendor3:bid3')
3L
>>> r.lrange('bid-abc123', 0, -1)
['vendor3:bid3', 'vendor2:bid2', 'vendor1:bid1']
>>> r.expire('bid-abc123', 0)
True
>>> r.lrange('bid-abc123', 0, -1)
[]
>>> r.lrange('bid-def456', 0, -1)
[]
>>> r.pexpire('bid-abc123', 0)
0L

"""

import multiprocessing
import time
import random
import socket
import copy
import json
import urllib2
import errno
import struct
from cgi import parse_qs, escape

def pack(bid_id, bidder_id, bid):
    # struct.unpack('<QQL', struct.pack('<QQL', 0, random.randint(0,0xffffffffL), 5))
    return struct.pack('<QQL', bid_id, bidder_id, bid)

def unpack(data):
    try:
        return struct.unpack('<QQL', data)
    except:
        return (None, None, None)

class BidderClient:
    def __init__(self, id, vendor, host, port):
        self.id = id
        self.vendor = vendor
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(0)
    def send(self, data):
        self.socket.sendto(data, (self.host, self.port))
    def recv(self):
        data = None
        try:
            data, addr = self.socket.recvfrom(1024)
            return data
        except socket.error as e:
            if e.errno != errno.EWOULDBLOCK:
                print e
        return data

def bidder_server(args):
    id, port, vendor = args
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', port))
    print 'port %s bidder %s' % (port, vendor)
    try:
        while True:
            data, addr = s.recvfrom(1024)
            print 'bidder %s received: %s' % (vendor, data)
            time.sleep(0.01 * random.randint(1,10)) # simulate delay, may exceed deadline
            # TODO: use binary format via struct.pack
            msg = 'bidder %s bids %.3f' % (vendor, round(random.random() / 10, 3))
            s.sendto(msg, addr)
    except KeyboardInterrupt:
        print('shutting down bidder %s' % vendor)

def auction(bidders, max_sec):
    # launch bidding
    print 'auction start'
    end = time.time() + max_sec
    print 'deadline', end
    for i,b in bidders.items():
        print 'engine bid request to %s' % b.port
        b.send('bid!')
    # gather bids up to deadline
    notseen = copy.copy(bidders)
    bids = dict()
    while notseen and time.time() < end:
        # try non-blocking read from any bidders we haven't heard from...
        for i,b in notseen.items():
            bid = b.recv()
            if bid:
                print bid
                bids[i] = bid
                del notseen[i]
        time.sleep(0.02) # tick
    print 'bid finished', time.time()
    print len(bids), 'bids received', bids
    # NOTE: doesn't handle ties
    winner = sorted(bids.values(),
                    key=lambda s:float(s.split(' ')[-1]),
                    reverse=True)[0] if bids else None
    print 'the winner is', winner
    winner_id = winner.split(' ')[1] if winner else None
    winner_price = float(winner.split(' ')[-1]) if winner else None
    return winner_id, winner_price

pool = None
bidders = None

def bidders_init(vendors):
    global pool, bidders
    pool = multiprocessing.Pool(len(vendors))
    bidders = {i: BidderClient(i, v, '127.0.0.1', 5000+i)
                for i,v in enumerate(vendors)}
    # launch bidders
    pool.map_async(bidder_server,
        [(i, b.port, b.vendor)
            for i,b in bidders.items()])
    time.sleep(0.2) # wait for init
    return pool, bidders

def bidders_get(merchant_ids):
    global bidders
    merchants = {}
    for i,b in bidders.items():
        if i in merchant_ids:
            b.recv() # non-blocking read to throw away pending data
            merchants[i] = b
    return merchants

vendors = [
    'brownsfashion.com'
    ,'lagarconne.com'
    ,'maccosmetics.com'
    ,'stevenalan.com'
    ,'nordstrom.com'
    ,'barneys.com'
]

bidders_init(vendors) # run init code!

# choose a single ad
def application(environ, start_response):

    try:
        params = parse_qs(environ.get('QUERY_STRING', ''))
        print 'params:', params
        price = int(params.get('price',[None])[0])
        gtin = int(params.get('gtin',[None])[0])
    except:
        start_response('400 Bad Request',
            [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*')
            ])
        return []

    start_response('200 OK',
        [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*')
        ])

    merchant_ids = [mp['merchant_id']
        for mp in json.loads(urllib2.urlopen('http://bidx.co/api/v0/merchant-product/gtin/' + str(gtin)).read())['merchant_product']]
    bidders = bidders_get(merchant_ids)
    winner_id, winner_price = auction(bidders, 0.1)

    resp = {
        'id': winner_id,
        # FIXME: price json encoding should be rounded to 2 decimal places... json module is stupid...
        'price': price * (1+(random.random()/10))
    }
    return [json.dumps(resp)]

if __name__ == '__main__':

    from wsgiref.simple_server import make_server, WSGIServer
    from SocketServer import ThreadingMixIn

    class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        pass

    bidders_init(vendors)
    httpd = make_server('127.0.0.1', 3031, application, ThreadingWSGIServer)
    print 'Listening on port 3031....'
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('shutting down main server')

