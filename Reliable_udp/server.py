import socket
import utils
import time
from utils import States

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# initial server_state
server_state = States.CLOSED

sock = socket.socket(socket.AF_INET,    # Internet
                     socket.SOCK_DGRAM) # UDP

sock.bind((UDP_IP, UDP_PORT)) # wait for connection


address = ()
# Some helper functions to keep the code clean and tidy
def update_server_state(new_state):
  global server_state
  if utils.DEBUG:
    print(server_state, '->', new_state)
  server_state = new_state

# Receive a message and return header, body and addr
# addr is used to reply to the client
# this call is blocking
def recv_msg():
  data, addr = sock.recvfrom(1024)
  header = utils.bits_to_header(data)
  body = utils.get_body_from_data(data)
  return (header, body, addr)

# the server runs in an infinite loop and takes
# action based on current state and updates its state
# accordingly
# You will need to add more states, please update the possible
# states in utils.py file
while True:
  if server_state == States.CLOSED:
    # we already started listening, just update the state
    update_server_state(States.LISTEN)
  elif server_state == States.LISTEN:
    if utils.DEBUG:
        print("Server Listening.........")
    # we are waiting for a message
    header, body, addr = recv_msg()
    if utils.DEBUG:
        print("Receive:")
        header.bits()
    # Step1: if received message is a syn message (syn = 1, ack = 0, fin = 0),
    # it's a connection initiation
    if header.syn == 1:
      seq_number = utils.rand_int() # we randomly pick a sequence number
      ack_number = header.seq_num + 1   # ack number is received sequence plus one
      # Step2: send ack message to client.
      ack_header = utils.Header(seq_number, ack_number, syn = 1, ack = 1)
      if utils.DEBUG:
        print("Send:")
      sock.sendto(ack_header.bits(),addr)
      update_server_state(States.SYN_RECEIVED)
  elif server_state == States.SYN_RECEIVED:
    # we are waiting for the ack message
    header, body, addr = recv_msg()
    if utils.DEBUG:
        print("Receive:")
        header.bits()
    # Step3: if received message is the ack message from client,
    # we can establish the connect.
    if header.ack == 1:
      update_server_state(States.ESTABLISHED)
    else:
      update_server_state(States.LISTEN)
  elif server_state == States.ESTABLISHED:
    if utils.DEBUG:
      print("Data transforming........")
      time.sleep(3)
    header, body, addr = recv_msg()
    if utils.DEBUG:
        print("Receive:")
        header.bits()
    # Step1: is received message is a fin message,
    # it's a connection termination.
    if header.fin == 1:
      # TODO: if there is anything else need to be sent to the client
      # If no,do:
      # If so, continue sending
      seq_number = header.ack_num
      ack_number = header.seq_num + 1
      # Step2: Server send ack to client.
      fin_ack_header = utils.Header(seq_number, ack_number, ack = 1, fin = 0)
      if utils.DEBUG:
        print("Send:")
      sock.sendto(fin_ack_header.bits(), addr)
      address = addr
      # global address_client
      # address_client = addr
      update_server_state(States.CLOSE_WAIT)
    else:
      pass
      # TODO: Data transform

  elif server_state == States.CLOSE_WAIT:
      # Step3: Server close and send fin to client.
      # Need to wait for some time.
      time.sleep(2)
      seq_number = utils.rand_int()
      fin_header = utils.Header(seq_number, 0, ack = 0, fin = 1)
      if utils.DEBUG:
        print("Send:")
      sock.sendto(fin_header.bits(), address)
      update_server_state(States.LAST_ACK)
  elif server_state == States.LAST_ACK:
      # Step4: Wait for the last ack and send nothing.
      header, body, addr = recv_msg()
      if utils.DEBUG:
          print("Receive:")
          header.bits()
      if header.ack == 1:
      # sock.close()
      # Update the state to CLOSED,
      # so that the server can listen to the next connection again.
        update_server_state(States.CLOSED)
      else:
          pass  # client may still have some security data to send.
  else:
    pass
