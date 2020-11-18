import socket
import random
import threading
import sys

class connThread(threading.Thread):
    def __init__(self, conn, conn_addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.conn_addr = conn_addr
    
    def run(self):
        conn = self.conn
        conn.send('Sayi bulmaca oyununa hosgeldiniz!\n'.encode())
        while True:
            data = conn.recv(1024)
            data_str = data.decode().strip()
            if data_str == "TIC":
                conn.send(b'TOC\n')
            elif data_str == "TRY":
                conn.send(b'GRR\n')
            elif data_str == 'QUI':
                conn.send(b'BYE\n')
                conn.close()
            elif data_str == "STA":
                self.game()
            else:
                conn.send(b'ERR\n')
    def game(self):
        conn = self.conn
        n = random.randint(0,99)
        conn.send(b'RDY\n')
        while True:
            number_data = conn.recv(1024)
            try:
                my_str = number_data.decode().strip()
                try_str = my_str.split(' ')
                commands_list = ['TIC', 'STA', 'QUI', 'TRY']
                if len(try_str) == 2:
                    my_str = try_str[0]
                    number = int(try_str[1])
                if my_str not in commands_list:
                    conn.send(b'ERR\n')
                if my_str == 'STA':
                        self.game()
                elif my_str == 'TIC':
                    conn.send(b'TOC\n')
                    continue
                elif my_str == 'QUI':
                    conn.send(b'BYE\n')
                    conn.close()
            except:
                conn.send(b'PRR\n')
            #print(number, n, command)
            if number > n and command == 'TRY':
                conn.send(b'GTH\n')
            elif number < n and command== 'TRY':
                conn.send(b'LTH\n')
            elif number == n and command == 'TRY':
                conn.send(b'WIN\n')
                break
s = socket.socket()
ip = "0.0.0.0"
port = int(sys.argv[1])

s.bind((ip, port))
s.listen(5)

counter = 0
threads = []
while True:
    conn, addr = s.accept()
    t = connThread(conn, addr)
    threads.append(t)
    t.start()