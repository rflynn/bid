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

def auction(bidders):
    # launch bidding
    for i,b in bidders.items():
        print 'engine bid request to %s' % b.port
        b.send('bid!')
    # gather bids up to deadline
    notseen = copy.deepcopy(bidders)
    bids = dict()
    start = time.time()
    end = start + 0.5
    print 'bid start', start
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
    winner_id = winner.split(' ')[1]
    return winner_id

if __name__ == '__main__':

    bidder_cnt = 3
    pool = Pool(bidder_cnt)
    bidders = {i: BidderClient(i, '127.0.0.1', 5000+i)
                for i in range(bidder_cnt)}

    # launch bidders
    pool.map_async(bidder_server, [(i, b.port) for i,b in bidders.items()])
    time.sleep(0.2) # wait for init

    winner_id = auction(bidders)
    print winner_id

    pool.terminate()

