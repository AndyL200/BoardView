import socket
import requests
from threading import Thread, Lock
from DrawBoard import DrawingBoard
from concurrent.futures import ThreadPoolExecutor
from PyQt6 import QtCore as Qtc
import pickle
#P2P Network
NAMEPOOL = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo", "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "X-ray", "Yankee", "Zulu"]
API_ENDPOINT = "http://127.0.0.1:8000"

class Game:
    _multiplayer_thread : Thread
    
    Board : DrawingBoard
    board_set = False
    _host = False
    board_buffer : bytes = []
    def __init__(self):
        multiplayer = MultiPlayerP2P(self.board_buffer, 1024)
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
        
        
    def set_board(self, board : DrawingBoard):
        self.Board = board
        self.board_set = True
    def update_board(self):
        if not self.board_set or self.multiplayer.is_locked():
            return
        self.multiplayer.shared_lock.acquire()
        self.Board.draw_from_buffer(self.board_buffer)
        self.multiplayer.shared_lock.release()
    def send_board_data(self, data):
        if not self.board_set or self.multiplayer.is_locked():
            return
        self.multiplayer.shared_lock.acquire()
        def broadcast_board_data(self):
            self.multiplayer.broadcast_board_buffer()

        def send_board_data_client(self):
            self.multiplayer.send(data)

        if self._host:
            broadcast_board_data(self)
        else:
            send_board_data_client(self)
        self.multiplayer.shared_lock.release()
    def stop_game(self):
        self.multiplayer.shared_lock.acquire()
        self.multiplayer.shutdown()
        self._multiplayer_thread.join()
        self.Board.deleteLater()
        self.board_set = False
class MultiPlayerP2P:
    shared_lock : Lock = Lock()
    _buffer : list
    _buffer_size : int
    _user_hostname : str = socket.gethostname()
    _user_ip : str = socket.gethostbyname(_user_hostname)
    def __init__(self, buffer, buffer_size=1024):
        self._buffer = buffer
        self._buffer_size = buffer_size
        pass
    def find_servers(self):
        try:
            res = requests.get(API_ENDPOINT + "/api/servers") #placeholder
            json_data = res.json()
            server = json_data['server'] if json_data['server'] else None
        except:
            server = None
        if server:
            return MultiPlayerP2P_Client(server)
        return MultiPlayerP2P_Server()
    def is_locked(self):
        return self.shared_lock.locked()
    def shutdown(self):
        #virtual
        pass
class MultiPlayerP2P_Client(MultiPlayerP2P):
    _client : socket.socket
    _nickname : str | None = None
    def __init__(self, server):
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client.connect((server[0], server[1]))
        print(server)
        pass
    def send(self, data):
        self._client.send(self._nickname.encode('ascii') + "NICK".encode('ascii') + data + "DRAW".encode('ascii'))
    def receive(self):
        while True:
            try:
                self.shared_lock.acquire()
                message = self._client.recv(1024)
                if message and not message.startswith(self._nickname.encode('ascii')) and message.endswith("DRAW".encode('ascii')):
                    nickname_end = message.find("NICK".encode('ascii'))
                    message = message[nickname_end + 4:-4]
                    self._buffer.append(message)
                    print(message)
                elif message and message.startswith("NICK".encode('ascii')):
                    self._nickname = message[4:].decode('ascii')
                    print(f"Assigned nickname: {self._nickname}")
                else:
                    continue
                self.shared_lock.release()
            except:
                print("Error occurred.")
                self._client.close()
                break
    def shutdown(self):
        self._client.close()
class MultiPlayerP2P_Server(MultiPlayerP2P):
    _server : socket.socket
    _server_thread = None
    _client_pool : ThreadPoolExecutor
    _clients = []
    _nicknames = []
    _full = False
    def __init__(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server = server
        res = requests.post(API_ENDPOINT + "/api/server/add", json={"host": self._user_ip, "port": 14800}) #placeholder
        pass        
    def start_listening(self):
        self._server.bind((self._user_ip , 14800)) #placeholder
        print("Server started, listening for connections...")
        self._server.listen(5) #allow up to 5 connections
        self._client_pool = ThreadPoolExecutor(max_workers=5)
        self.receive_connection()
    def shutdown(self):
        self._server.close()
        self._client_pool.shutdown(wait=True)
        if self._server_thread:
            self._server_thread.join()
        res = requests.post(API_ENDPOINT + "/api/server/remove", json={"host": self._user_ip, "port": 14800}) #placeholder

    def handle(self, client):
        while True:
            try:
                self.shared_lock.acquire()
                message = client.recv(1024)
                # if len(self._buffer) == 5:
                #     self.broadcast(self._buffer)
                #     self._buffer.clear()
                if message:
                    
                    nickname_end = message.find("NICK".encode('ascii'))
                    draw_end = message.find("DRAW".encode('ascii'))
                    if nickname_end != -1 and draw_end != -1:
                        message = message[nickname_end + 4:draw_end]
                        self._buffer.append(message) #should be a QPoint
                    self.broadcast(message)
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
    def broadcast_board_buffer(self):
        for message in self._buffer:
            self.broadcast(message)
        self._buffer.clear()

    def receive_connection(self):
        
        while True:
            try:
                if len(self._clients) >= 5:  # Move inside loop
                    print("Server full, rejecting new connections")
                    client, address = self._server.accept()
                    client.send(b"Server full")
                    client.close()
                    if not self._full:
                        self._full = True
                        res = requests.post(API_ENDPOINT + "/api/server/full", json={"host": self._user_ip, "port": 14800}) #placeholder
                    continue

                client, address = self._server.accept()
                print(f"Connected with {str(address)}")

                self._clients.append(client)
                self._nicknames.append(NAMEPOOL[len(self._nicknames) % len(NAMEPOOL)])

                print(f"Nickname is {self._nicknames[-1]}")
                self.broadcast(f"{self._nicknames[-1]} joined!".encode('ascii'))
                client.send("Connected to server!".encode('ascii'))
                client.send("NICK".encode('ascii') + self._nicknames[-1].encode('ascii'))

                self._client_pool.submit(self.handle, client)
            except:
                print("Reception stopped")
                break
