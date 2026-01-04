import socket
import requests
from threading import Thread, Lock
from DrawBoard import DrawingBoard
#P2P Network
NAMEPOOL = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo", "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "X-ray", "Yankee", "Zulu"]


class Game:
    _multiplayer_thread : Thread
    
    Board : DrawingBoard
    board_set = False
    _host = False
    board_buffer = []
    def __init__(self):
        multiplayer = MultiPlayerP2P(self.board_state_buffer, 1024)
        self.multiplayer = multiplayer.find_servers()
        if isinstance(self.multiplayer, MultiPlayerP2P_Server):
            print("Hosting server...")
            self._host = True
            self._multiplayer_thread = Thread(target=self.multiplayer.start_listening)
        elif isinstance(self.multiplayer, MultiPlayerP2P_Client):
            print("Connected to server as client.")
            self._multiplayer_thread = Thread(target=self.multiplayer.receive)
        else:
            print("No servers found.")
            return
        self._multiplayer_thread.start()
        pass
    def set_board(self, board : DrawingBoard):
        self.Board = board
        self.board_set = True
    def update_board(self):
        if not self.board_set or self.multiplayer.is_locked():
            return
        self.multiplayer.shared_lock.acquire()
        for data in self.board_buffer:
            self.Board.draw(data)
        self.multiplayer.shared_lock.release()
    def send_board_data(self, data):
        if not self.board_set or self.multiplayer.is_locked():
            return
        self.multiplayer.shared_lock.acquire()
        def broadcast_board_data(self, data):
            self.multiplayer.broadcast(data)

        def send_board_data_client(self, data):
            self.multiplayer.send(data)

        if self._host:
            broadcast_board_data(self, data)
        else:
            send_board_data_client(self, data)
        self.multiplayer.shared_lock.release()
class MultiPlayerP2P:
    shared_lock : Lock = Lock()
    _buffer : list
    _buffer_size : int
    def __init__(self, buffer, buffer_size=1024):
        self._buffer = buffer
        self._buffer_size = buffer_size
        pass
    def find_servers(self):
        res = requests.get('https://example.com/servers') #placeholder
        json_data = res.json()
        server = json_data['servers'][0] if json_data['servers'] else None
        if server:
            MultiPlayerP2P_Server()
        return MultiPlayerP2P_Client(server)
    def is_locked(self):
        return self.shared_lock.locked()
class MultiPlayerP2P_Client(MultiPlayerP2P):
    _client : socket.socket
    def __init__(self, server):
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client.connect((server['host'], server['port']))
        pass
    def send(self, data):
        self._client.send(data)
    def receive(self):
        while True:
            try:
                self.shared_lock.acquire()
                message = self._client.recv(1024)
                if message:
                    self._buffer.append(message)
                else:
                    continue
                self.shared_lock.release()
            except:
                print("Error occurred.")
                self._client.close()
                break
class MultiPlayerP2P_Server(MultiPlayerP2P):
    _server : socket.socket
    _server_thread = None
    _clients = []
    _nicknames = []
    def __init__(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server = server
        pass        
    def start_listening(self):
        self._server.bind(('localhost' , 12345)) #placeholder
        self._server.listen(5) #allow up to 5 connections
        self.receive_connection()

    def handle(self, client):
        while True:
            try:
                self.shared_lock.acquire()
                message = client.recv(1024)
                if message:
                    self._buffer.append(message)
                self.shared_lock.release()
            except:
                index = self._clients.index(client)
                self._clients.remove(client)
                client.close()
                nickname = self._nicknames[index]
                self.broadcast(f"{nickname} left!".encode('ascii'))
                self._nicknames.remove(nickname)
                break
        return
    def broadcast(self, message):
        for client in self._clients:
            client.send(message)

    def receive_connection(self):
        while True:
            client, address = self._server.accept()
            print(f"Connected with {str(address)}")

            self._clients.append(client)
            self._nicknames.append(NAMEPOOL[len(self._nicknames) % len(NAMEPOOL)])

            print(f"Nickname is {self._nicknames[-1]}")
            self.broadcast(f"{self._nicknames[-1]} joined!".encode('ascii'))
            client.send("Connected to server!".encode('ascii'))


            thread = Thread(target=self.handle, args=(client,))
            thread.start()
