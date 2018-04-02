import socket
import sys

BUF_SIZE = 4096

class WebClient(object):
    invalidHttpRequest = ("GET", "HEAD")

    def __init__(self, url):
        '''
        WebClient Constructor
        :param url: Request url
        '''
        self._file_path = ""
        self._url = url
        self._host = ""
        self._port = ""
        self._extractUrl(url)
        try:
            self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._client_socket.connect((self._host, int(self._port)))
        except socket.error:
            print("Client socket init failed")
            self._client_socket.close()


    def _extractUrl(self, url):
        '''
        Extract useful information in url
        :param url: url
        '''
        if "http://" in url:
            url = url[len("http://"):]
        if "/" in url:
            host_n_port = url.split("/")[0]
            self._file_path = url[len(host_n_port)+1:]
        else:
            host_n_port = url
        if ":" in host_n_port:
            self._host, self._port = host_n_port.split(":")
        else:
            self._host = host_n_port
            self._port = 80


    def httpRequest(self, method):
        '''
        Once http request, mode: request-reply
        :param method: http request method, "GET", "HEAD", "POST"
        :return: 
        '''

        msg = "%s /%s HTTP/1.1\r\nHost: %s:%s\r\nConnection: close\r\n\r\n" % (method, self._file_path, self._host, self._port)
        #print(msg)
        self._client_socket.sendall(msg.encode())

        recv = self._client_socket.recv(BUF_SIZE)
        while True:
            part = self._client_socket.recv(BUF_SIZE)
            if not part:
                break
            recv += part
        print(recv)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        url, method = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 2:
        url, method = sys.argv[1], "GET"


    ws = WebClient(url)
    ws.httpRequest(method)


