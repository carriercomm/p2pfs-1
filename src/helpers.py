from twisted.protocols.basic import FileSender
from tempfile import NamedTemporaryFile
from twisted.internet import threads
from Crypto.Cipher import AES
import struct
import random
import os
import hashlib

ENCRYPT_KEY = 'testtesttesttest'

def sha_hash(name):
  h = hashlib.sha1()
  h.update(name)
  return h.digest()

  
def upload_file_with_encryption(filename, transport):
  infile = open(filename, 'r')
  tmpfile = NamedTemporaryFile(delete=False)
  d = threads.deferToThread(encrypt_file, infile, tmpfile, ENCRYPT_KEY)
  d.addCallback(lambda tmpfile: upload_file(open(tmpfile, 'r'), transport))
  return d

def upload_file(file, transport):
  sender = FileSender()
  sender.CHUNK_SIZE = 2 ** 16

  d = sender.beginFileTransfer(file, transport, lambda data: data)
  return d

# Encryption/decryption based on:
# http://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto/ 

def encrypt_file(file_in, file_out, key):
  chunk_size = 24*1024

  iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
  encryptor = AES.new(key, AES.MODE_CBC, iv)

  file_size = os.path.getsize(file_in.name)

  file_out.write(struct.pack('<Q', file_size))
  file_out.write(iv)

  chunk = file_in.read(chunk_size)

  while len(chunk) > 0:
    if len(chunk) % 16 != 0:
      chunk += ' ' * (16 - len(chunk) % 16)
    file_out.write(encryptor.encrypt(chunk))
    chunk = file_in.read(chunk_size)
  file_in.close()
  file_out.close()
  return file_out.name

def decrypt_file(file_in, file_out, key):
  chunk_size = 64*1024

  orig_size = struct.unpack('<Q', file_in.read(struct.calcsize('Q')))[0]

  iv = file_in.read(16)
  decryptor = AES.new(key, AES.MODE_CBC, iv)

  chunk = file_in.read(chunk_size)

  while len(chunk) > 0:
    file_out.write(decryptor.decrypt(chunk))
    chunk = file_in.read(chunk_size)

  file_out.truncate(orig_size)
  file_in.close()
  file_out.close()
  return file_out.name
    
    
def save_buffer(buffer, destination):
  real_file_path = os.path.dirname(destination)
  if not os.path.exists(real_file_path):
    os.makedirs(real_file_path)
  f = open(destination, 'w')
  f.write(buffer)
  f.close()
 
