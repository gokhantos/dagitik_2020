import socket
import threading
import queue
import time
import datetime

users = {}
rooms = {}
temp_users = []

class irc_server():
    def __init__(self, ip, port):
        self.sock = socket.socket()
        self.sock.bind((ip, port))
        self.sock.listen(5)
        self.users = queue.Queue()
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
        self.thread_queue = thread_queue
        self.log_queue = log_queue
        self.username = "guest"
        self.message = None
        self.threads = threads
        self.to_user = None
        self.my_timer = None
        self.session_started = False
        self.pin_code = None
        self.to_room = None
        self.deleted_room = None
    def run(self):
        global temp_users
        if self.thread_type == "readThread":
            while True:
                data = self.conn.recv(1024)
                command = self.parser(data)
                if "BYE" in command:
                    self.thread_queue.put(command)
                    if ":" not in command:
                        break
                elif command == "OKG":
                    users_list = rooms[self.to_room]
                    for user in users_list:
                        users[user][0].put(self.to_room + ":" + self.username+":"+self.message)
                    self.thread_queue.put("OKG")
                elif "OKL" in command:
                    users_list = rooms[self.to_room]
                    for user in users_list:
                        users[user][0].put("OKL " + self.to_room + ":" + self.username)
                    self.thread_queue.put("OKL")
                elif "OKD" in command:
                    for user in temp_users:
                        users[user][0].put("OKD " + self.deleted_room)
                    temp_users = []
                    self.thread_queue.put("OKD")
                elif "OKB" in command:
                    users[self.to_user][0].put("OKB " + self.deleted_room + ":" + self.to_user)
                    self.thread_queue.put("OKB")
                elif "OKK" in command:
                    users[self.to_user][0].put("OKK " + self.deleted_room + ":" + self.to_user)
                    self.thread_queue.put("OKK")
                elif "OKE" in command:
                    users_list = rooms[self.to_room]
                    for user in users_list:
                        users[user][0].put("OKE " + self.to_room + ":" + self.username)
                    self.thread_queue.put("OKE")
                elif command == "OKP":
                    users[self.to_user][0].put(self.username + ":" + self.message)
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
                    if ":" not in data:
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
        global users
        global rooms
        global temp_users
        data_str = data.decode().strip()
        splitstr = data_str.split()
        command = splitstr[0]
        if self.session_started == False and (command!="NIC" and command!="PIN" and command!="QUI" and command!="REG"):
            self.logger(self.username, "server", command, None)
            self.logger("server", self.username, "LRR", None)
            return "LRR"
        if command == "REG":
            self.logger(self.username, "server", command, None)
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            try:
                username_pin = splitstr[1].split(":")
                username = username_pin[0]
                pin_code = username_pin[1]
            except:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            try:
                self.pin_code = int(pin_code)
            except:
                self.logger("server", self.username, "REJ", None)
                return "REJ " + pin_code
            if self.session_started == True:
                changed_user = [self.thread_queue, self.pin_code, users[username][2], users[username][3]]
                del users[username]
                users.update({username: changed_user})
                self.logger("server", self.username, "ACC", None)
                return "ACC " + str(self.pin_code)
            if username in users:
                self.logger("server", self.username, "REJ", None)
                return "REJ " + username
            else:
                self.username = username
                users.update({username: [self.thread_queue, self.pin_code, [], []]})
                self.logger("server", self.username, "WEL", None)
                return "WEL " + self.username
        if command == "NIC":
            self.logger(self.username, "server", command, None)
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            if self.session_started == True:
                return "ALI " + self.username
            try:
                username_pin = splitstr[1].split(":")
                username = username_pin[0]
                pin_code = username_pin[1]
                self.username = username
            except:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            try:
                pin_code = int(pin_code)
                self.pin_code = pin_code
            except:
                self.logger("server", self.username, "WPC", None)
                return "WPC " + self.pin_code

            if username in users:
                if pin_code == users[username][1]:
                    self.my_timer = self.timer_thread(self.thread_queue, self.log_queue, self.username)
                    self.my_timer.start()
                    self.session_started = True
                    self.logger("server", self.username, "WEL", None)
                    return "WEL " + self.username
                else:
                    self.logger("server", self.username, "WPC", None)
                    return "WPC " + str(self.pin_code)
            else:
                self.logger("server", self.username, "NOP", None)
                return "NOP " + self.username

        if command == "OPN":
            self.logger(self.username, "server", command, None)
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"

            room_name = splitstr[1]
            if room_name in rooms:
                self.logger("server", self.username, "REJ", None)
                return "REJ " + room_name
            else:
                auth = "Administrator"
                users.setdefault(self.username, [])[2].append(room_name + ":" + auth)
                rooms.setdefault(room_name, []).append(self.username)
                self.logger("server", self.username, "ACC", None)
                return "ACC " + room_name

        if command == "LOG":
            self.logger(self.username, "server", command, None)
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            
            room_name = splitstr[1]
            self.to_room = room_name
            if room_name not in rooms:
                return "NOP " + room_name
            elif users[self.username][3]:
                banned_rooms = users[self.username][3]
                if room_name in banned_rooms:
                    self.logger("server", self.username, "REJ", None)
                    return "REJ " + self.to_room + ":" +self.username
            else:
                logged_rooms_list = users[self.username][2]
                rooms_dict = {}
                if not logged_rooms_list:
                    pass
                else:
                    list_str = ':'.join(map(str, logged_rooms_list))
                    logged_rooms_list = list_str.split(":")
                    rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                

                if room_name not in rooms_dict:
                    auth = "Guest"
                    users.setdefault(self.username, [])[2].append(room_name + ":" + auth)
                    rooms.setdefault(room_name, []).append(self.username)
                    self.logger("server", self.username, "OKL", None)
                    return "OKL " + room_name + ":"+ self.username
        if command == "GNL":
            self.logger(self.username, "server", command, None)
            room_message = splitstr[1].split(":")
            room_name = room_message[0]
            room_message.remove(room_name)
            splitstr.remove(splitstr[0])
            splitstr.remove(splitstr[0])
            message =  room_message + splitstr
            self.to_room = room_name 
            if room_name not in rooms_dict:
                self.logger("server", self.username, "NOP", None)
                return "NOP " + self.to_room
            self.message = ' '.join(message)
            self.to_room = room_name
            self.logger("server", self.username, "OKG", None)
            return "OKG"
        if command == "WRN":
            self.logger(self.username, "server", "WRN", self.message)
            message = splitstr[1-len(splitstr):]
            self.message = ' '.join(message)
            self.logger("server", self.username, "OKW", None)
            return "OKW"
        if command == "PRV":
            self.logger(self.username, "server", command, None)
            mystr = splitstr[1].split(':')
            if mystr[0] in users:
                self.to_user = mystr[0]
                message = data_str.split(':')
                self.message = message[1]
                self.logger("server", self.username, "OKP", None)
                return "OKP"
            else:
                self.to_user = mystr[0]
                self.logger(self.username, self.to_user, "PRV", self.message)
                self.logger("server", self.username, "NOP", self.to_user)
                return "NOP " + self.to_user
        
        if command== "LSO":
            self.logger(self.username, "server", command, None)
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            
            room_name = splitstr[1]

            if room_name not in rooms:
                return "NOP " + room_name
            else:
                users_list = rooms[room_name]
                in_rooms = []
                for user in users_list:
                    logged_rooms_list = users[user][2]
                    rooms_dict = {}
                    if not logged_rooms_list:
                        pass
                    else:
                        list_str = ''.join(map(str, logged_rooms_list))
                        logged_rooms_list = list_str.split(":")
                        rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                        in_rooms.append(user+ ":" +rooms_dict[room_name])
                list_str = ';'.join(map(str, in_rooms))
                return "LST " + list_str
        
        if command == "EXT":
            self.logger(self.username, "server", command, None)
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            room_name = splitstr[1]
            self.to_room = room_name
            if room_name not in rooms:
                return "NOP " + room_name
            else:
                logged_rooms_list = users[self.username][2]
                rooms_dict = {}
                if not logged_rooms_list:
                    pass
                else:
                    list_str = ''.join(map(str, logged_rooms_list))
                    logged_rooms_list = list_str.split(":")
                    rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                    users.setdefault(self.username, [])[2].remove(room_name + ":" + rooms_dict[room_name])
                    rooms.setdefault(room_name, []).remove(self.username)
                    return "BYE "  + room_name+ ":" + self.username
        
        if command == "KCK":
            self.logger(self.username, "server", command, None)
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            room_user = splitstr[1].split(":")
            room_name = room_user[0]
            username = room_user[1]

            if room_name not in rooms:
                return "NOP " + room_name
            elif username not in users:
                return "NOP " + username
            elif (room_name not in rooms) and (username not in rooms[room_name]):
                return "NOP " + room_name + ":" + username
            else:
                logged_rooms_list = users[self.username][2]
                rooms_dict = {}
                if not logged_rooms_list:
                    pass
                else:
                    list_str = ''.join(map(str, logged_rooms_list))
                    logged_rooms_list = list_str.split(":")
                    rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                    if rooms_dict[room_name] == "Administrator":
                        logged_rooms_list = users[username][2]
                        rooms_dict = {}
                        if not logged_rooms_list:
                            pass
                        else:
                            list_str = ''.join(map(str, logged_rooms_list))
                            logged_rooms_list = list_str.split(":")
                            rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                            users.setdefault(username, [])[2].remove(room_name + ":" + rooms_dict[room_name])
                            rooms.setdefault(room_name, []).remove(username)
                            self.deleted_room = room_name
                            self.to_user = username
                            return "OKK " + username
                    else:
                        return "PRR"
        if command == "BAN":
            self.logger(self.username, "server", command, None)
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            room_user = splitstr[1].split(":")
            room_name = room_user[0]
            username = room_user[1]
            self.to_user = username
            self.deleted_room = room_name
            if room_name not in rooms:
                return "NOP " + room_name
            elif username not in users:
                return "NOP " + username
            elif (room_name not in rooms) and (username not in rooms[room_name]):
                return "NOP " + room_name + ":" + username
            else:
                logged_rooms_list = users[self.username][2]
                rooms_dict = {}
                if not logged_rooms_list:
                    pass
                else:
                    list_str = ''.join(map(str, logged_rooms_list))
                    logged_rooms_list = list_str.split(":")
                    rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                    if rooms_dict[room_name] == "Administrator":
                        logged_rooms_list = users[username][2]
                        rooms_dict = {}
                        if not logged_rooms_list:
                            pass
                        else:
                            list_str = ''.join(map(str, logged_rooms_list))
                            logged_rooms_list = list_str.split(":")
                            rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                            users.setdefault(username, [])[3].append(room_name)
                            users.setdefault(username, [])[2].remove(room_name + ":" + rooms_dict[room_name])
                            rooms.setdefault(room_name, []).remove(username)
                            return "OKB " + username
                    else:
                        return "PRR"
        if command == "DEL":
            self.logger(self.username, "server", command, None)
            if len(splitstr)>2:
                self.logger("server", self.username, "ERR", None)
                return "ERR"
            room_name = splitstr[1]
            self.deleted_room = room_name
            if room_name not in rooms:
                return "NOP " + room_name
            else:
                logged_rooms_list = users[self.username][2]
                rooms_dict = {}
                if not logged_rooms_list:
                    pass
                else:
                    list_str = ''.join(map(str, logged_rooms_list))
                    logged_rooms_list = list_str.split(":")
                    rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                    if rooms_dict[room_name] == "Administrator":
                        for user in users.keys():
                            temp_users.append(user)
                            logged_rooms_list = users[user][2]
                            rooms_dict = {}
                            if not logged_rooms_list:
                                pass
                            else:
                                list_str = ''.join(map(str, logged_rooms_list))
                                logged_rooms_list = list_str.split(":")
                                rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                                users.setdefault(user, [])[2].remove(room_name + ":" + rooms_dict[room_name])
                        del rooms[room_name]
                        return "OKD " + room_name
                    else:
                        return "PRR"
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
            dict_list = list(users.keys())
            dict_str = ':'.join(map(str, dict_list))
            self.logger(self.username, "server", "GLS", None)
            self.logger("server", self.username, "LST", dict_str)
            return "LST " + dict_str
        elif data_str == "LSR":
            dict_list = list(rooms.keys())
            dict_str = ':'.join(map(str, dict_list))
            return "LST " + dict_str
        elif data_str == "LSU":
            dict_list = list(users.keys())
            dict_str = ':'.join(map(str, dict_list))
            return "LST " + dict_str
        elif data_str == "LSI":
            logged_rooms_list = users[self.username][2]
            rooms_dict = {}
            if not logged_rooms_list:
                return "LST empty"
            else:
                list_str = ':'.join(map(str, logged_rooms_list))
                logged_rooms_list = list_str.split(":")
                rooms_dict = {logged_rooms_list[i]: logged_rooms_list[i+1] for i in range(0, len(logged_rooms_list), 2)}
                in_rooms = rooms_dict.keys()
                list_str = ':'.join(map(str, in_rooms))
                return "LST " + list_str
        elif data_str == "QUI":
            if self.session_started == True:
                self.my_timer.stop()
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
