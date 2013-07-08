from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, protocol
from twisted.internet.address import IPv4Address
from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol, ClientFactory, ServerFactory
from twisted.protocols.basic import NetstringReceiver
from twisted.spread import pb
import argparse
import md5
import collections
import math


def Hash(s):
  return int(long(md5.new(s).hexdigest(), 16) % 160)


def HashAddress(address):
  return Hash(str(address.host) + str(address.port))
  

class ChordService(pb.Root):
  
  def __init__(self):
    self.me = None
    self.data = {}
    self.routing_table = {}

  def AddToRoutingTable(self, address):
    h = HashAddress(address)
    self.routing_table[h] = address
    print("Added {} to routing table (hash: {}).".format(address, h))

  def StoreValue(self, key, value):
    self.data[int(key)] = value
    print("Stored key: {}, value: {}.".format(key, value))
    
  def remote_GetValue(self, key):
    return self.GetValue(int(key))

  def GetValue(self, key):
    print('Retrieving value with key: {}.'.format(key))
    # check if value is among the values you hold
    if key in self.data:
      return succeed(self.data[key])

    # if it is not, look at your routing table
    deferred = Deferred()
    #factory = ChordClientFactory(key, deferred)
    factory = pb.PBClientFactory()
    #address_hash = int(math.floor(math.log(int(key), 2)))
    #print("address hash: {}".format(address_hash)
    #address = self.routing_table[address_hash]
    address = self.routing_table[int(key)]
    reactor.connectTCP(address.host, address.port, factory)
    d = factory.getRootObject()
    d.addCallback(lambda object: object.callRemote("GetValue", key))
    return d


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--port')
  parser.add_argument('--store')
  parser.add_argument('--retrieve')
  parser.add_argument('--connect', default=None)

  args = parser.parse_args()
  port = int(args.port)

  service = ChordService()

  if (args.connect):
    dst = args.connect.split(':')
    service.AddToRoutingTable(IPv4Address('TCP', dst[0], int(dst[1])))

  if (args.store):
    key, value = args.store.split(':')
    service.StoreValue(key, value)
    
  if (args.retrieve):
    def EchoValue(value):
      print('Retrieved value: {}.'.format(value))
    d = service.GetValue(args.retrieve)
    d.addCallback(EchoValue)

  f = pb.PBServerFactory(service)
  reactor.listenTCP(port, f)
    
  reactor.run()

if __name__ == '__main__':
  main()

