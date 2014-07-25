# ex: set ts=4 et:
import multiprocessing
import time
import random
import socket
import copy
import json
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
    def __init__(self, id, host, port):
        self.id = id
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
    id, port = args
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', port))
    print 'bidder %s waiting on port %s' % (id, port)
    while True:
        data, addr = s.recvfrom(1024)
        print 'bidder %s received: %s' % (id, data)
        time.sleep(0.01 * random.randint(1,8)) # simulate delay, may exceed deadline
        # TODO: use binary format via struct.pack
        msg = 'bidder %s bids %.3f' % (id, random.random() * 1000)
        s.sendto(msg, addr)

def auction(bidders, max_sec):
    # launch bidding
    for i,b in bidders.items():
        print 'engine bid request to %s' % b.port
        b.send('bid!')
    # gather bids up to deadline
    notseen = copy.copy(bidders)
    bids = dict()
    end = time.time() + max_sec
    print 'deadline', end
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
    winner_id = int(winner.split(' ')[1]) if winner else None
    winner_price = float(winner.split(' ')[-1]) if winner else None
    return winner_id, winner_price

pool = None
bidders = None

def bidders_init(bidder_cnt):
    global pool, bidders
    pool = multiprocessing.Pool(bidder_cnt)
    bidders = {i: BidderClient(i, '127.0.0.1', 5000+i)
                for i in range(bidder_cnt)}
    # launch bidders
    pool.map_async(bidder_server, [(i, b.port) for i,b in bidders.items()])
    time.sleep(0.2) # wait for init
    return pool, bidders

def bidders_get():
    global bidders
    for i,b in bidders.items():
        b.recv() # non-blocking read to throw away pending data
    return bidders

def choose_ad(environ, start_response):
    parameters = parse_qs(environ.get('QUERY_STRING', ''))
    print 'parameters:', parameters
    price = int(parameters.get('price','')[0])
    start_response('200 OK',
        [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*')
        ])
    bidders = bidders_get()
    winner_id, winner_price = auction(bidders, 0.1)
    resp = {
        'id': winner_id,
        'price': price * (1+(random.random()/10)) #winner_price
    }
    return [json.dumps(resp)]

if __name__ == '__main__':

    from wsgiref.simple_server import make_server, WSGIServer
    from SocketServer import ThreadingMixIn

    class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        pass

    bidders_init(6)
    httpd = make_server('127.0.0.1', 3031, choose_ad, ThreadingWSGIServer)
    print 'Listening on port 3031....'
    httpd.serve_forever()

