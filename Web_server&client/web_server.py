from multiprocessing import Process
import sys, re
import socket
import time
import os.path

DEFAULT_HTML_PATH = "./www"
DEFAULT_PORT = 8080
VALID_METHOD = {"GET","HEAD"}

class WebServer(object):
    def __init__(self, port=DEFAULT_PORT, r_path=DEFAULT_HTML_PATH, host=""):
        '''
        WebServer Constructor
        :param host: Server host
        :param port: Server Port
        :param r_path: Default file's path
        '''
        self._host = host
        self._port = int(port)
        self._html_path = r_path
        print("%s:%d" % (self._host, self._port), self._html_path)

        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self._host, self._port))   # bind the socket to a public host, and a well-known port
        except socket.error:
            print("Server socket init failed")
            self._server_socket.close()

    def start(self):
        '''
        WebServer Launcher
        Using multiprocessing to deal with more clients
        '''
        self._server_socket.listen(128)
        while True:
            client_socket, client_addr = self._server_socket.accept()   #new socket to send and receive data
            print("(%s, %d) user connected" % client_addr)
            # handle_client_process = Process(target=self.handler, args=(client_socket,))
            # handle_client_process.start()
            self.handler(client_socket)
            client_socket.close()

    def handler(self, client_socket):
        '''
        Reply messages in terms of various client's requests
        :param client_socket: Ref of client sockets
        :return: 
        '''
        request_data = client_socket.recv(1024)   #The maximum amount of data to be received at once.

        request_lines = request_data.splitlines()
        request_first_line = request_lines[0].decode()
        # First line: method, file name, Protocol information
        method = request_first_line.split(" ")[0]
        #file_name = re.match(r"\w+ +(/[^ ]*) ", request_first_line).group(1)
        file_name = request_first_line.split(" ")[1]

        response_head_line = str(time.ctime((time.time()))) + "\r\n"
        response_head_line += "Server: RW-server\r\n"
        if (method not in VALID_METHOD):
            response_first_line = "HTTP/1.1 501 Error\r\n"
            response_body = "Method not implemented."
            response_head_line += "Content-Length: %d\r\n" % len(response_body)
            response_head_line += "Connection: close\r\n"
            response_head_line += "Content-Type: text/html;charset=UTF-8\r\n"
            response = response_first_line + response_head_line + "\r\n" + response_body
        else:
            if(os.path.isfile(DEFAULT_HTML_PATH + file_name)):
                file = open(DEFAULT_HTML_PATH + file_name, "rb")
                file_data = file.read()
                file.close()
                response_first_line = "HTTP/1.1 200 OK\r\n"
                response_body = file_data.decode("utf-8")
                response_head_line += "Content-Length: %d\r\n" % len(response_body)
                response_head_line += "Connection: close\r\n"
                response_head_line += "Content-Type:text/html;charset=UTF-8\r\n"
                if method == "GET":
                    response = response_first_line + response_head_line + "\r\n" + response_body
                    #Todo: what does head mean?
                elif method == "HEAD":
                    response = response_first_line + response_head_line

            else:
                # msg code 404
                response_first_line = "HTTP/1.1 404 Error\r\n"
                response_body = "Not Found."
                response_head_line += "Content-Length: %d\r\n" % len(response_body)
                response_head_line += "Connection: close\r\n"
                response_head_line += "Content-Type:text/html;charset=UTF-8\r\n"
                response = response_first_line + response_head_line + "\r\n" + response_body

        client_socket.sendall(response)
        client_socket.close()


if __name__ == '__main__':
    if len(sys.argv) == 3:
        port, path = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 2:
        port, path = sys.argv[1], DEFAULT_HTML_PATH
    else:
        print("Argv is invalid.")
        sys.exit()

    ws = WebServer(port, path)
    ws.start()