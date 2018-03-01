from ws import make_handshake_response


class Connection:
    def __init__(self, client_socket):
        self.__cs = client_socket
        self.handshake = False
        self.last_message = b''

    def disconnect(self):
        self.__cs.close()

    def recv(self):
        return self.__cs.recv(1024)

    def send(self, data):
        self.__cs.send(data)

