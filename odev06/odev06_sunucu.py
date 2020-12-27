import socket
import threading
import queue
import time
import datetime

class irc_server():
    def __init__(self, ip, port):
        self.sock = socket.socket()
        self.sock.bind((ip, port))
        self.sock.listen(5)
        self.users = {}
        self.threads = {}
        self.run()

    def run(self):
        log_queue = queue.Queue()
        logger_thread = my_thread(None, None, "loggerThread", self.users, None, log_queue, self.threads)
        logger_thread.start()
        while True:
            conn, addr = self.sock.accept()
            thread_queue = queue.Queue()
            write_thread = my_thread(conn, addr, "writeThread", self.users, thread_queue, log_queue, self.threads)
            read_thread = my_thread(conn, addr, "readThread", self.users, thread_queue, log_queue, self.threads)
            self.threads.update({conn: thread_queue})
            write_thread.start()
            read_thread.start()

class my_thread(threading.Thread):
    def __init__(self, conn, addr, thread_type, users, thread_queue, log_queue, threads):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.thread_type = thread_type
        self.users = users
        self.thread_queue = thread_queue
        self.log_queue = log_queue
        self.username = "guest"
        self.message = None
        self.threads = threads
        self.to_user = None
        self.my_timer = None
        self.session_started = False

    def run(self):
        if self.thread_type == "readThread":
            while True:
                data = self.conn.recv(1024)
                command = self.parser(data)
                if "BYE" in command:
                    self.thread_queue.put(command)
                    break
                elif command == "OKG":
                    for queues in self.threads.values():
                        queues.put(self.username+":"+self.message)
                    self.thread_queue.put("OKG")
                elif command == "OKP":
                    self.users[self.to_user].put(self.username + ":" + self.message)
                    self.thread_queue.put("OKP")
                elif command == "OKW":
                    for queues in self.threads.values():
                        queues.put(self.username+ ":" +self.message)
                    self.thread_queue.put("OKW")
                else:
                    self.thread_queue.put(command)
                
        if self.thread_type == "writeThread":
            while True:
                data = self.thread_queue.get()
                if "BYE" in data:
                    data = data + "\n"
                    self.conn.send(data.encode())
                    self.conn.close()
                    break
                data = data + "\n"
                self.conn.send(data.encode())

        if self.thread_type == "loggerThread":
            while True:
                data = self.log_queue.get()
                with open("cikti.txt", "a+") as f:
                    f.write(data + "\n")

    def logger(self,sender,reciever, command, message):
        timestamp = datetime.datetime.now()
        logData = [str(timestamp), sender, reciever, command, message]
        logData = ':'.join(filter(None, logData))
        self.log_queue.put(logData)
        
    def parser(self, data):
        data_str = data.decode().strip()
        splitstr = data_str.split()
        command = splitstr[0]
        if self.session_started == False and (command!="NIC" and command!="PIN" and command!="QUI"):
            self.logger(self.username, "server", command, None)
            self.logger("server", self.username, "LRR", None)
            return "LRR"
        if command == "NIC":
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            my_username = splitstr[1]
            self.logger(self.username, "server", "NIC", my_username)
            if my_username in self.users:
                self.logger("server", self.username, "REJ", None)
                return "REJ " + my_username
            else:
                self.username = splitstr[1]
                self.users.update({self.username: self.thread_queue})
                self.my_timer = self.timer_thread(self.thread_queue, self.log_queue, self.username)
                self.my_timer.start()
                self.session_started = True
                self.logger("server", self.username, "WEL", None)
                return "WEL " + self.username
        if command == "GNL":
            message = splitstr[1-len(splitstr):]
            self.message = ' '.join(message)
            self.logger("server", self.username, "OKG", None)
            self.logger(self.username, "server", "GNL", self.message)
            return "OKG"
        if command == "WRN":
            message = splitstr[1-len(splitstr):]
            self.message = ' '.join(message)
            self.logger("server", self.username, "OKW", None)
            self.logger(self.username, "server", "WRN", self.message)
            return "OKW"
        if command == "PRV":
            mystr = splitstr[1].split(':')
            if mystr[0] in self.users:
                self.to_user = mystr[0]
                message = data_str.split(':')
                self.message = message[1]
                self.logger("server", self.username, "OKP", None)
                self.logger(self.username, self.to_user, "PRV", self.message)
                return "OKP"
            else:
                self.to_user = mystr[0]
                self.logger(self.username, self.to_user, "PRV", self.message)
                self.logger("server", self.username, "NOP", self.to_user)
                return "NOP " + self.to_user
        if data_str == "PIN":
            self.logger(self.username, "server", "PIN", None)
            self.logger("server", self.username, "PON", None)
            return "PON"
        elif data_str == "OKG":
            self.logger(self.username, "server", "OKG", None)
        elif data_str == "OKW":
            self.logger(self.username, "server", "OKW", None)
        elif data_str == "OKP":
            self.logger(self.username, "server", "OKP", None)
        elif data_str == "GLS":
            dict_list = list(self.users.keys())
            dict_str = ':'.join(map(str, dict_list))
            self.logger(self.username, "server", "GLS", None)
            self.logger("server", self.username, "LST", dict_str)
            return "LST " + dict_str
        elif data_str == "QUI":
            if self.session_started == True:
                self.my_timer.stop()
                del self.users[self.username]
            self.logger(self.username, "server", "QUI", None)
            self.logger("server", self.username, "BYE", None)
            return "BYE " + self.username
        else:
            self.logger(self.username, "server", command, None)
            self.logger("server", self.username, "ERR", None)
            return "ERR"
    
    class timer_thread(threading.Thread):
        def __init__(self, thread_queue, log_queue, to_user):
            threading.Thread.__init__(self)
            self.thread_queue = thread_queue
            self._stop = threading.Event()
            self.to_user = to_user
            self.log_queue = log_queue
        def stop(self):
            self._stop.set()
        def stopped(self):
            return self._stop.isSet()
        def run(self):
            while True:
                time.sleep(60)
                if self.stopped():
                    break
                self.thread_queue.put("TIN")
                timestamp = datetime.datetime.now()
                logData = [str(timestamp), "server", self.to_user, "TIN"]
                logData = ':'.join(filter(None, logData))
                self.log_queue.put(logData)
                    
        
my_server = irc_server("0.0.0.0", 8888)