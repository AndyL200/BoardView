import socket
import requests
from threading import Thread, Lock
import time
from DrawBoard import DrawingBoard
from concurrent.futures import ThreadPoolExecutor
from PyQt6 import QtCore as Qtc
import json
import struct

#P2P Network
NAMEPOOL = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo", "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "X-ray", "Yankee", "Zulu"]
API_ENDPOINT = "http://127.0.0.1:8000"

HEADER_LENGTH = 4
PAYLOAD_LENGTH = 4096 - HEADER_LENGTH
PACKET_SIZE = HEADER_LENGTH + PAYLOAD_LENGTH


class Game(Qtc.QObject):
    _multiplayer_thread : Thread
    _draw_signal = Qtc.pyqtSignal(list, name="draw_from_buffer_signal")
    _update_thread : Thread
    Board : DrawingBoard
    board_set = False
    _host = False
    _game_end = False
    recv_buffer : list = []
    def __init__(self):
        super().__init__()
        multiplayer = MultiPlayerP2P(self.recv_buffer, PAYLOAD_LENGTH)
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
        self._draw_signal.connect(self.Board.draw_from_buffer, Qtc.Qt.ConnectionType.QueuedConnection)
        self._update_thread = Thread(target=self.update_board)
        self._update_thread.start()
    def update_board(self):
        while not self._game_end:
            with self.multiplayer.shared_lock:
                if len(self.recv_buffer) == 0:
                    time.sleep(1/30)  # Update at ~30 FPS
                    continue
            if self._host:
                self.multiplayer.broadcast_board_buffer()

            with self.multiplayer.shared_lock:
                buffer_copy = self.recv_buffer.copy()
                self.recv_buffer.clear() #clear after drawing

            self._draw_signal.emit(buffer_copy)
            
            time.sleep(1/30)  # Update at ~30 FPS

    #new_drawing signal handler
    def send_board_data(self, data):
        if not self.board_set:
            return
        self.multiplayer.send_buffer.extend(data)
        print("send_board_data called, buffer size:", len(self.multiplayer.send_buffer))
        if not self._host:
            self.multiplayer.send()
        
    def stop_game(self):
        self._game_end = True
        self.multiplayer._game_end = True
        if self._update_thread.is_alive():
            self._update_thread.join()
        if self.multiplayer.is_locked():
            self.multiplayer.shared_lock.release()
        self.multiplayer.shutdown()
        if self._multiplayer_thread.is_alive():
            self._multiplayer_thread.join()
        
        self.Board.deleteLater()
        self.board_set = False
class MultiPlayerP2P:
    
   
    def __init__(self, recv_buffer, buffer_size):
        self.shared_lock : Lock = Lock()
        self._recv_buffer = recv_buffer
        self._buffer_size = buffer_size
        self.send_buffer : list = []
        self._buffer_size : int
        self._user_hostname : str = socket.gethostname()
        self._user_ip : str = socket.gethostbyname(self._user_hostname)
        self._game_end : bool = False
        pass
    def find_servers(self):
        try:
            res = requests.get(API_ENDPOINT + "/api/servers") #placeholder
            json_data = res.json()
            server = json_data['server'] if json_data['server'] else None
        except:
            server = None
        if server:
            return MultiPlayerP2P_Client(server, self._recv_buffer, self._buffer_size)
        return MultiPlayerP2P_Server(self._recv_buffer, self._buffer_size)
    def is_locked(self):
        return self.shared_lock.locked()
    def shutdown(self):
        #virtual
        pass
    def recv_exact(self, sock, n):
        #Receive exactly n bytes from the socket
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data
    def send_message(self, sock, message):
        #Prefix messages with length header
        
        if not isinstance(message, bytes):
            message = json.dumps(message).encode('utf-8')
        
        header = struct.pack("!I", len(message))
        sock.sendall(header + message)
    def recv_message(self, sock):
        #Receive message with length header
        header = self.recv_exact(sock, HEADER_LENGTH)
        if not header:
            return None
        message_length = struct.unpack("!I", header)[0]
        message = self.recv_exact(sock, message_length)
        return message
class MultiPlayerP2P_Client(MultiPlayerP2P):
    _client : socket.socket
    _nickname = None
    def __init__(self, server, recv_buffer, buffer_size):
        super().__init__(recv_buffer, buffer_size)
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client.connect((server[0], server[1]))
        print(server)
        pass
    def send(self):
        if self._nickname:
            if len(self.send_buffer) > 0:
                data = self.send_buffer.copy()
                self.send_buffer.clear()
                #  print("Client Sends", data)
                message = {"NICK": self._nickname, "DRAW":data}
                self.send_message(self._client, message)

    def receive(self):
        while not self._game_end:
            try:
                raw = self.recv_message(self._client)
                if not raw:
                    print("Connection closed by server.")
                    self._client.close()
                    break
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    print("Received non-JSON message", raw)
                    continue

                if not msg:
                    continue

                if "ASSIGN" in msg and msg["ASSIGN"]:
                    self._nickname = msg["NICK"]
                    print(f"Assigned nickname: {self._nickname}")
                    ACK = {"NICK": self._nickname, "ACK": True}
                    self.send_message(self._client, ACK)
                    continue

                if self._nickname:
                    if "NICK" in msg and msg["NICK"] == "SERVER" and "DRAW" in msg:
                        #Server broadcast
                        draw_data = msg["DRAW"]
                        with self.shared_lock:
                            self._recv_buffer.extend(draw_data) #should be PEN, BRUSH, LOG
                        print("Client Receives", len(draw_data), "points from server")
                        continue
                    
            except Exception as e:
                print(f"Error occurred: {e}")
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
    def __init__(self, buffer, buffer_size):
        super().__init__(buffer, buffer_size)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server = server
        try:
            res = requests.post(API_ENDPOINT + "/api/server/add", json={"host": self._user_ip, "port": 14800}) #placeholder
        except:
            pass
    def start_listening(self):
        self._server.bind((self._user_ip , 14800)) #placeholder
        print("Server started, listening for connections...")
        self._server.listen(5) #allow up to 5 connections
        self._client_pool = ThreadPoolExecutor(max_workers=5)
        self.receive_connection()
    def shutdown(self):
        if self._server_thread:
            self._server_thread.join()
        self._client_pool.shutdown(wait=False)
        self._server.close()
        res = requests.post(API_ENDPOINT + "/api/server/remove", json={"host": self._user_ip, "port": 14800}) #placeholder
        

    def handle(self, client):
        while not self._game_end:
            try:
                raw = self.recv_message(client)
                # if len(self._recv_buffer) == 5:
                #     self.broadcast(self._recv_buffer)
                #     self._recv_buffer.clear()
                if not raw:
                    raise Exception("Client disconnected.")
                msg = json.loads(raw)
                if not msg:
                    continue
                if isinstance(msg, dict):
                    if "NICK" in msg and "DRAW" in msg:
                        draw_data = msg["DRAW"]
                        with self.shared_lock:
                            self._recv_buffer.extend(draw_data) #use lock to prevent race conditions
                        if "LOG" in draw_data[0]:
                            print("Server Receives", len(draw_data[0]["LOG"]), "points from", msg["NICK"])
                    if "NICK" in msg and "ACK" in msg and msg["ACK"]:
                        nickname = msg["NICK"]
                        print(f"{nickname} acknowledged connection.")
                        self.broadcast({"msg": f"{nickname} joined!"})
                        continue
            #if len(buffer) >= buffer_size: broadcast and clear??
                
            except Exception as e:
                try:
                    index = self._clients.index(client)
                    self._clients.remove(client)
                    client.close()
                    nickname = self._nicknames[index]
                    self.broadcast({"msg": f"{nickname} left!"})
                    self._nicknames.remove(nickname)
                except:
                    pass
        return
    def broadcast(self, message):
        for client in self._clients:
            self.send_message(client, message)
    def broadcast_board_buffer(self):
        with self.shared_lock:
            self.send_buffer.extend(self._recv_buffer)
            broadcast_data = self.send_buffer.copy()
        self.send_buffer.clear()
        
        #HAVE TO RELEASE BEFORE BROADCASTING TO AVOID DEADLOCK
        message = {"NICK": "SERVER", "DRAW": broadcast_data}
        self.broadcast(message)

    def receive_connection(self):
        
        while True:
            try:
                if len(self._clients) >= 5:  # Move inside loop
                    print("Server full, rejecting new connections")
                    client, address = self._server.accept()
                    self.send_message(client, {"msg": "Server full"})
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
                # self.broadcast(f"{self._nicknames[-1]} joined!") premature
                self.send_message(client, {"msg": "Connected to server!"})
                msg = {"NICK": self._nicknames[-1], "ASSIGN": True}
                self.send_message(client, msg)

                self._client_pool.submit(self.handle, client)
            except:
                print("Reception stopped")
                break
