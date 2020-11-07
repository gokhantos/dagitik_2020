import threading
import sys
import queue

alphabet = "abcdefghijklmnopqrstuvwxyz"

class my_thread(threading.Thread):
    def __init__(self, thread_id, shift_number, block_length, words_queue, crypted_queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.shift_number = shift_number
        self.words_queue = words_queue
        self.block_length = block_length
        self.crypted_queue = crypted_queue
    def run(self):
        process_data(self.words_queue, self.crypted_queue, self.block_length, self.shift_number)

def process_data(words_queue,crypted_queue,block_length, shift_number):
    while True:
        global stop_threads
        if stop_threads == True:
            break
        queue_lock.acquire()
        if not words_queue.empty():
            data = words_queue.get()
            data = encrypt(data, shift_number)
            crypted_queue_lock.acquire()
            crypted_queue.put(data)
            crypted_queue_lock.release()
            queue_lock.release()
        else:
            queue_lock.release()

def read_data(block_length):
    with open('input.txt', 'r') as f:
        text = f.read()
        text = [text[i: i+block_length] for i in range(0, len(text), block_length)]
        return text

def encrypt(text, shift_number):
    result = ""
    text = text.lower()
    for char in text:
        if char not in alphabet:
            result += char
        else:
            new_index = (alphabet.index(char) - shift_number) % len(alphabet)
            result += alphabet[new_index]
    return result

def decrypt(text, shift_number):
    return encrypt(text, (shift_number * -1))

def save_text(text, shift_number, thread_number, block_length):
    file_name = "crypted_thread_" + str(shift_number) + "_" + str(thread_number) + "_" + str(block_length) +".txt"
    with open(file_name, "w") as f:
        f.write(text)

shift_number = int(sys.argv[1])
thread_number = int(sys.argv[2])
block_length = int(sys.argv[3])
words_list = read_data(block_length)
queue_lock = threading.Lock()
crypted_queue_lock = threading.Lock()
threads = []
words_queue = queue.Queue()
crypted_words_queue = queue.Queue()
stop_threads = False

for thread_id in range(thread_number):
    thread = my_thread(thread_id, shift_number, block_length, words_queue, crypted_words_queue)
    thread.start()
    threads.append(thread)

#Filling the queue with words in text
queue_lock.acquire()
for words in words_list:
    words_queue.put(words)
queue_lock.release()

while not words_queue.empty():
    pass

stop_threads = True

for tr in threads:
    tr.join()

crypted_text = []
while not crypted_words_queue.empty():
    crypted_text.append(crypted_words_queue.get())

crypted_text = ''.join([str(elem) for elem in crypted_text]) 
save_text(crypted_text, shift_number, thread_number, block_length)