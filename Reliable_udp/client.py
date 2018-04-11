import multiprocessing
import socket
import time
from math import ceil
from multiprocessing import Manager

import utils
from utils import States

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
MSS = 12  # maximum segment size
# TIME_OUT = 2

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

TIME_OUT = 5
sock.settimeout(TIME_OUT)


def send_udp(message):
    sock.sendto(message, (UDP_IP, UDP_PORT))


def recv_msg():
    try:
        data, addr = sock.recvfrom(1024)
        header = utils.bits_to_header(data)
        body = utils.get_body_from_data(data)
        return (header, body, addr)
    except socket.timeout:
        return (None, None, None)


class Client:
    def __init__(self):
        self.client_state = States.CLOSED
        self.last_received_ack = 0
        self.last_received_seq = 0
        self.last_seq = 0
        self.fin = 0
        self.handshake()

    def handshake(self):
        if self.client_state == States.CLOSED:
            # Step1: Generate a random sequence number. Send syn message to the server
            # to initiate a connection.
            seq_num = utils.rand_int()
            syn_header = utils.Header(seq_num, 0, syn=1, )
            # for this case we send only header;
            # if you need to send data you will need to append it
            send_udp(syn_header.bits())
            self.update_state(States.SYN_SENT)
            self.last_seq = seq_num
            self.handshake()
        elif self.client_state == States.SYN_SENT:
            # Step2: Rceive ack from server with syn = 1, ack = 1.
            header, body, addr = recv_msg()
            if header is None:
                print("Handshake failed.")
                self.update_state(States.CLOSED)
            elif header.ack == 1:
                seq_num = header.ack_num
                ack_num = header.seq_num + 1
                syn_header = utils.Header(seq_num, ack_num, ack=1)
                send_udp(syn_header.bits())

                self.last_seq = seq_num
                self.last_received_seq = header.seq_num
                self.last_received_ack = header.ack_num + 1
                self.update_state(States.ESTABLISHED)

    def terminate(self):
        if self.client_state == States.ESTABLISHED:
            # Step1: Client send fin message.
            seq_num = self.last_received_ack
            ack_num = self.last_received_seq + 1
            fin_header = utils.Header(seq_num, ack_num, ack = 1, fin=1)
            send_udp(fin_header.bits())
            self.last_seq = seq_num
            self.update_state(States.FIN_WAIT_1)
            self.terminate()
        elif self.client_state == States.FIN_WAIT_1:
            header, body, addr = recv_msg()
            if header.ack == 1 and header.ack_num == self.last_seq + 1:
                # Step2: Recieve ack from the server and do nothing but continue waiting.
                # self.last_received_ack = -1
                self.update_state(States.FIN_WAIT_2)
                self.terminate()
            else:
                self.update_state(States.ESTABLISHED)
                self.terminate()
        elif self.client_state == States.FIN_WAIT_2:
            # Step3: Receive fin message from server and send the last ack.
            # self.receive_acks()
            header, body, addr = recv_msg()
            if (header.fin == 1):
                seq_num = header.ack_num
                ack_num = header.seq_num + 1
                fin_header = utils.Header(seq_num, ack_num, ack=1)
                send_udp(fin_header.bits())
                self.last_received_seq = header.seq_num
                self.last_received_ack = header.ack_num
                self.update_state(States.TIME_WAIT)
                self.terminate()
        elif self.client_state == States.TIME_WAIT:
            # Step4: Wait for TIME_OUT seconds and tear down the connection.
            time.sleep(TIME_OUT)
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
        send_byte = message.encode()
        pacek_total_num = int(ceil(len(send_byte) / MSS))
        sent_packet_id = 0
        timeout_cnt = 0
        while sent_packet_id < pacek_total_num:
            if timeout_cnt > 2:
                break

            _this_data = send_byte[sent_packet_id * MSS: (sent_packet_id+1)*MSS]
            seq_num = self.last_received_ack
            ack_num = self.last_received_seq + 1
            self.last_seq = seq_num
            data_header = utils.Header(seq_num, ack_num)
            send_udp(data_header.bits()+_this_data)

            header, body, addr = recv_msg()
            if header is None:
                timeout_cnt += 1
                continue

            if header.ack == 1 and header.ack_num == self.last_seq + len(_this_data):
                self.last_received_ack = header.ack_num
                self.last_received_seq = header.seq_num
                sent_packet_id += 1
                timeout_cnt = 0


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
client.send_reliable_message("(This message is to be received in pieces)\n"
                            "   Say not in grief that she is no more\n"
                            "   but say in thankfulness that she was\n"
                            "   A death is not the extinguishing of a light,\n"
                            "   but the putting out of the lamp\n"
                            "   because the dawn has come.\n"
                             "                       - Rabindranath Tagore\n"
                             "  \(^__^)/")
# we terminate the connection
client.terminate()
