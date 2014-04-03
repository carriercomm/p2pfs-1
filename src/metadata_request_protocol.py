from twisted.internet import defer
from twisted.protocols.basic import LineReceiver
from helpers import *
import binascii
import json

class MetadataRequestProtocol(LineReceiver):
  """Protocol for requesting metadata class"""
  def __init__(self, logger):
    self.l = logger
    self.buffer = ''

  def connectionMade(self):
    ip = self.transport.getPeer().host
    self.l.log('Connection was made (MetadataRequestProtocol) to {}'.format(ip))

  def lineReceived(self, line):
    self.buffer = line

  def request_metadata(self, filename, key, hash):
    contents = json.dumps({'command' : 'tell_metadata', 'path' : filename, 'key' : key, 'hash' : binascii.hexlify(hash)})
    self.sendLine(contents)

    self.l.log('metadata request finished')
    self.df = defer.Deferred()
    return self.df

  def connectionLost(self, reason):
    if len(self.buffer) == 0:
      self.l.log("Metadata request failed! Got nothing.\n")
      return
    self.df.callback(int(self.buffer))

