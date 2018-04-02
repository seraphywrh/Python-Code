import zmq
import time

context = zmq.Context()
socket1 = context.socket(zmq.PUB)
socket2 = context.socket(zmq.SUB)
socket1.bind("tcp://*:5050")
socket2.bind("tcp://*:5051")
socket2.setsockopt_string(zmq.SUBSCRIBE, '')
i = 0
while True:
    string = socket2.recv_string()
    print("start_signal " + string)
    time.sleep(0.1)
    if string.split()[0] == "id_confirmed":
        i = i + 1
    if i == 2:
        # time.sleep(1)
        socket1.send_string("start")
        print("start")
        break


while True:
    string = socket2.recv_string()
    socket1.send_string(string)
    #print("run " + string)
