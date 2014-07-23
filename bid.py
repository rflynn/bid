# ex: set ts=4 et:
from multiprocessing import Process, Pipe, Pool
import time
import random
import socket
import copy
import pdb

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
        try:
            data, addr = self.socket.recvfrom(1024)
            return data
        except socket.error as e:
            if e.errno != 35: # EWOULDBLOCK
                print e # unexpected error
        return None

def bidder_server(args):
    id, port = args
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', port))
    print 'bidder %s waiting on port %s' % (id, port)
    while True:
        data, addr = s.recvfrom(1024)
        print 'bidder %s received: %s' % (id, data)
        time.sleep(0.1 * random.randint(1,5)) # simulate delay, may exceed deadline
        s.sendto('bidder %s bids %.3f' % (id, random.random()), addr)

def auction(bidders, max_sec):
    # launch bidding
    for i,b in bidders.items():
        print 'engine bid request to %s' % b.port
        b.send('bid!')
    # gather bids up to deadline
    notseen = copy.deepcopy(bidders)
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
        time.sleep(0.05) # tick
    print 'bid finished', time.time()
    print len(bids), 'bids received', bids
    # NOTE: doesn't handle ties
    winner = sorted(bids.values(),
                    key=lambda s:float(s.split(' ')[-1]),
                    reverse=True)[0] if bids else None
    print 'the winner is', winner
    winner_id = int(winner.split(' ')[1]) if winner else None
    return winner_id

pool = None
bidders = None

def bidders_get(bidder_cnt):

    global pool, bidders

    if not pool:
        pool = Pool(bidder_cnt)
        bidders = {i: BidderClient(i, '127.0.0.1', 5000+i)
                    for i in range(bidder_cnt)}
        # launch bidders
        pool.map_async(bidder_server, [(i, b.port) for i,b in bidders.items()])
        time.sleep(0.2) # wait for init

    return pool, bidders


from cgi import parse_qs, escape
import json
def choose_ad(environ, start_response):
    #parameters = parse_qs(environ.get('QUERY_STRING', ''))
    #subject = escape(parameters['subject'][0] if 'subject' in parameters else 'World')

    pool, bidders = bidders_get(3)

    winner_id = auction(bidders, 0.2)
    #print winner_id

    start_response('200 OK',
        [
            ('Content-Type', 'text/html'),
            ('Access-Control-Allow-Origin', '*')
        ])
    resp = {'color':['green','blue','purple'][winner_id] if winner_id else None}
    return [json.dumps(resp)]

if __name__ == '__main__':

    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 3031, choose_ad)
    srv.serve_forever()

    #pool.terminate()



