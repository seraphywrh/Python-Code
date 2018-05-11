import socket
import time

import utils
from utils import States

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# initial server_state
server_state = States.CLOSED

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

sock.bind((UDP_IP, UDP_PORT))  # wait for connection

# Set the value of TIMEOUT, during this time recv is blocked.
TIME_OUT = 10
sock.settimeout(TIME_OUT)

address = ()
# record last receive time
heartbeat_time = None
msg_box = []

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
    try:
        data, addr = sock.recvfrom(1024)
        header = utils.bits_to_header(data)
        body = utils.get_body_from_data(data)
        return (header, body, addr)
    # if timeout, return none.
    except socket.timeout:
        return (None, None, None)

# the server runs in an infinite loop and takes
# action based on current state and updates its state
# accordingly
# You will need to add more states, please update the possible
# states in utils.py file
while True:
    if server_state == States.CLOSED:
        update_server_state(States.LISTEN)        # we already started listening, just update the state

    elif server_state == States.LISTEN:
        header, body, addr = recv_msg()             # waiting for a message
        if header is None:
            continue
        address = addr
        # Step1: if received message is a syn message (syn = 1, ack = 0, fin = 0),
        # it's a connection initiation
        if header.syn == 1:
            seq_number = utils.rand_int()        # randomly pick a sequence number
            ack_number = header.seq_num + 1         # ack number is received sequence plus one
            # Step2: send ack message to client.
            ack_header = utils.Header(seq_number, ack_number, syn=1, ack=1)
            if utils.DEBUG:
                print("Send:")
            sock.sendto(ack_header.bits(), addr)
            update_server_state(States.SYN_RECEIVED)

    elif server_state == States.SYN_RECEIVED:
        header, body, addr = recv_msg()    # waiting for the ack message
        # if didn't receive ack in time, stop the handshake process and go back.
        if header is None:
            update_server_state(States.CLOSE_WAIT)
        # Step3: if received message is the ack message from client,
        # we can establish the connect.
        if header.ack == 1:
            heartbeat_time = time.time()
            update_server_state(States.ESTABLISHED)

    elif server_state == States.ESTABLISHED:
        current_time = time.time()
        # if haven't heard from the client for a long time, something bad happens in the net, have to close the connection.
        if current_time - heartbeat_time > TIME_OUT * 1.5:
            heartbeat_time = current_time
            update_server_state(States.CLOSE_WAIT)

        header, body, addr = recv_msg()
        # if time out only once, the client may resent the lost package, so continue receiving.
        if header is None:
            continue
        # Step1: received message is a fin message,
        # it's a connection termination.
        if header.fin == 1:
            heartbeat_time = time.time()
            seq_number = header.ack_num
            ack_number = header.seq_num + 1
            fin_ack_header = utils.Header(seq_number, ack_number, ack=1, fin=0)
            sock.sendto(fin_ack_header.bits(), addr)
            address = addr
            print("Receive message: ", "".join(msg_box))        # combine received package.
            msg_box = []
            update_server_state(States.CLOSE_WAIT)

        # Normal data transforming
        else:
            msg_box.append(body)
            heartbeat_time = time.time()
            seq_number = header.ack_num
            ack_number = header.seq_num + len(body)
            fin_ack_header = utils.Header(seq_number, ack_number, ack=1, fin=0)
            sock.sendto(fin_ack_header.bits(), addr)
    elif server_state == States.CLOSE_WAIT:
        # Step3: Server close and send fin to client.
        # Need some time to close.
        time.sleep(.5)
        seq_number = seq_number + 1
        fin_header = utils.Header(seq_number, ack_number, syn=0, ack=1, fin=1)
        sock.sendto(fin_header.bits(), address)
        update_server_state(States.LAST_ACK)

    elif server_state == States.LAST_ACK:
        # Step4: Wait for the last ack and send nothing.
        header, body, addr = recv_msg()
        if header.ack == 1 and header.ack_num == seq_number + 1:
            # Update the state to CLOSED,
            # so that the server can listen to the next connection again.
            update_server_state(States.CLOSED)
        else:
            update_server_state(States.CLOSE_WAIT)
    else:
        pass
