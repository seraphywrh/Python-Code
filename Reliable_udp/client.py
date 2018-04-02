from multiprocessing import Value
from threading import Timer
from utils import States
import multiprocessing
import random
import socket
import time
import utils

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
MSS = 12 # maximum segment size
TIME_OUT = 2

sock = socket.socket(socket.AF_INET,    # Internet
                     socket.SOCK_DGRAM) # UDP

def send_udp(message):
  sock.sendto(message, (UDP_IP, UDP_PORT))

class Client:
  def __init__(self):
    self.client_state = States.CLOSED
    self.last_recv_seq = 0
    self.handshake()


  def handshake(self):
    if self.client_state == States.CLOSED:
      # Step1: Generate a random sequence number. Send syn message to the server
      # to initiate a connection.
      seq_num = utils.rand_int()
      syn_header = utils.Header(seq_num, 0, syn = 1,)
      # for this case we send only header;
      # if you need to send data you will need to append it
      if utils.DEBUG:
        print("Send:")
      send_udp(syn_header.bits())
      self.update_state(States.SYN_SENT)
      self.last_recv_seq = seq_num
      self.handshake()
    if self.client_state == States.SYN_SENT:
      # Step2: Rceive ack from server with syn = 1, ack = 1.
      recv_data, addr = sock.recvfrom(1024)
      header = utils.bits_to_header(recv_data)
      if utils.DEBUG:
        print("Receive:")
        header.bits()
      if header.ack == 1 and header.syn == 1 and self.last_recv_seq + 1 == header.ack_num:
        seq_num = header.ack_num
        ack_num = header.seq_num + 1
        syn_header = utils.Header(seq_num, ack_num, ack=1)
        #Step3: Send ack to server to finish handshaking
        if utils.DEBUG:
          print("Send:")
        send_udp(syn_header.bits())
        sock.connect((UDP_IP, UDP_PORT))
        self.last_recv_seq = seq_num
        self.update_state(States.ESTABLISHED)
        self.handshake()
      else:       # if there is something wrong, resend the syn message.
        self.update_state(States.CLOSED)
    elif self.client_state == States.ESTABLISHED:

      # todo: data transmit
      if utils.DEBUG:
        print("Data transforming........")
        time.sleep(3)
      # When all data has been sent:
      self.terminate()
    else:
      pass

  def terminate(self):
    if self.client_state == States.ESTABLISHED:
      # Step1: Client send fin message.
      seq_num = utils.rand_int() + self.last_recv_seq +1
      fin_header = utils.Header(seq_num, 0, fin=1)
      if utils.DEBUG:
        print("Send:")
      sock.sendall(fin_header.bits())
      self.last_recv_seq = seq_num
      self.update_state(States.FIN_WAIT_1)
      self.terminate()     # Call terminate() again to loop.
    elif self.client_state == States.FIN_WAIT_1:
      recv_data, addr = sock.recvfrom(1024)
      header = utils.bits_to_header(recv_data)
      if utils.DEBUG:
        print("Receive:")
        header.bits()
      if self.last_recv_seq + 1 == header.ack_num:
        # Step2: Recieve ack from the server and do nothing but continue waiting.
        self.update_state(States.FIN_WAIT_2)
        self.terminate()
      else:
        self.update_state(States.ESTABLISHED)
        self.terminate()
    elif self.client_state == States.FIN_WAIT_2:
      # Step3: Receive fin message from server and send the last ack.
      recv_data, addr = sock.recvfrom(1024)
      header = utils.bits_to_header(recv_data)
      if utils.DEBUG:
        print("Receive:")
        header.bits()
      if header.fin == 1:
        seq_num = header.ack_num
        ack_num = header.seq_num + 1
        fin_header = utils.Header(seq_num, ack_num, ack=1)
        if utils.DEBUG:
          print("Send:")
        sock.sendall(fin_header.bits())
        self.update_state(States.TIME_WAIT)
        self.terminate()
      else:      # Server may still have something to send.
        self.update_state(States.ESTABLISHED)
        self.handshake()  # continue to receive
    elif self.client_state == States.TIME_WAIT:
      # Step4: Wait for 30 seconds and tear down the connection.
      time.sleep(3)
      sock.close()
      self.update_state(States.CLOSED)
    else:
      pass


  def update_state(self, new_state):
    if utils.DEBUG:
      print(self.client_state, '->', new_state)
    self.client_state = new_state

  def send_reliable_message(self, message):
    # send messages
    # we loop/wait until we receive all ack.
    pass

  # these two methods/function can be used receive messages from
  # server. the reason we need such mechanism is `recv` blocking
  # and we may never recieve a package from a server for multiple
  # reasons.
  # 1. our message is not delivered so server cannot send an ack.
  # 2. server responded with ack but it's not delivered due to
  # a network failure.
  # these functions provide a mechanism to receive messages for
  # 1 second, then the client can decide what to do, like retransmit
  # if not all packets are acked.
  # you are free to implement any mechanism you feel comfortable
  # especially, if you have a better idea ;)
  def receive_acks_sub_process(self, lst_rec_ack_shared):
    while True:
      recv_data, addr = sock.recvfrom(1024)
      header = utils.bits_to_header(recv_data)
      if header.ack_num > lst_rec_ack_shared.value:
        lst_rec_ack_shared.value = header.ack_num

  def receive_acks(self):
    # Start receive_acks_sub_process as a process
    lst_rec_ack_shared = Value('i', self.last_received_ack)
    p = multiprocessing.Process(target=self.receive_acks_sub_process, args=(lst_rec_ack_shared,))
    p.start()
    # Wait for 1 seconds or until process finishes
    p.join(1)
    # If process is still active, we kill it
    if p.is_alive():
      p.terminate()
      p.join()
    # here you can update your client's instance variables.
    self.last_received_ack = lst_rec_ack_shared.value

# we create a client, which establishes a connection
client = Client()
# we send a message
client.send_reliable_message("This message is to be received in pieces")  # not for milestone 1
# we terminate the connection
client.terminate()
