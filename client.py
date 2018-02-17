from ws import make_handshake_response


class Client:
    # need status (in connecting, after handshake, online ...)
    def __init__(self, client_socket):
        self.handshake = False
        self.cs = client_socket

    def disconnect(self):
        self.cs.close()

    def shake_hands(self, key):
        """Shake hands with client by websocket rules.

        :param key: websocket key
        """
        # TODO: make redesign of usage ws module (uwse ws module only in
        # server module, and not in client)
        r = make_handshake_response(key)
        self.cs.send(r)
        self.handshake = True

    def recv(self):
        return self.cs.recv(1024)

    def send(self, data):
        self.cs.send(data)

