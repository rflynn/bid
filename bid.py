from multiprocessing import Process, Pipe, Pool
import time
import random
import socket
import copy
import pdb

def bidder(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', port))
    print 'bidder waiting on port:', port
    while True:
        data, addr = s.recvfrom(1024)
        print 'bidder %s received: %s' % (port, data)
        time.sleep(0.1 * random.randint(1,5))
        s.sendto('bidder %s bids %d' % (port, random.randint(1,10)), addr)

if __name__ == '__main__':
    bidder_cnt = 3
    ports = [5000+p for p in range(bidder_cnt)]
    pool = Pool(bidder_cnt)
    sockets = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM) for _ in range(bidder_cnt)]
    bidders = set(ports)
    for s in sockets:
        s.setblocking(0)
    try:
        pool.map_async(bidder, ports)
        time.sleep(0.2)
        for i,s in enumerate(sockets):
            print 'engine bid request to %s' % ports[i]
            s.sendto('bid!', ('127.0.0.1', ports[i]))
        bids = dict()
        notseen = dict(zip(ports, sockets))
        start = time.time()
        end = start + 0.5
        print 'bid start', start
        print 'bid end', end
        while notseen and time.time() < end:
            # try non-blocking read from any bidders we haven't heard from...
            for p,s in notseen.items():
                try:
                    data, addr = s.recvfrom(1024)
                    print data
                    bids[p] = data
                    del notseen[p]
                except socket.error as e:
                    if e.errno == 35: # EWOULDBLOCK
                        pass
                    else: # unexpected error...
                        print e
            time.sleep(0.05) # tick
        print 'bid finished', time.time()
        print 'bids received', bids
        # NOTE: doesn't handle ties
        print 'the winner is', sorted(bids.values(), key=lambda s:int(s.split(' ')[-1]), reverse=True)[0]
        pool.terminate()
    except KeyboardInterrupt:
        pass
