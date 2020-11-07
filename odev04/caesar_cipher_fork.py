import sys
from multiprocessing import Lock, Process, Queue

alphabet = "abcdefghijklmnopqrstuvwxyz"

def worker(words_queue,crypted_queue,stop_signal, block_length, shift_number, queue_lock):
    while True:
        queue_lock.acquire()
        if stop_signal.empty() == False:
            queue_lock.release()
            break
        if not words_queue.empty():
            data = words_queue.get()
            data = encrypt(data, shift_number)
            crypted_queue.put(data)
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

def save_text(text, shift_number, process_number, block_length):
    file_name = "crypted_fork_" + str(shift_number) + "_" + str(process_number) + "_" + str(block_length) +".txt"
    with open(file_name, "w") as f:
        f.write(text)


def main():
    shift_number = int(sys.argv[1])
    process_number = int(sys.argv[2])
    block_length = int(sys.argv[3])
    words_list = read_data(block_length)
    queue_lock = Lock()
    processes = []
    words_queue = Queue()
    crypted_words_queue = Queue()

    #According to multiprocessing.process documentation global variables may not work properly
    #to recieve data from inside of processes that's why a new queue used for stopping processes
    stop_signal = Queue()

    #Forking processes
    for i in range(process_number):
        p = Process(target=worker, args=(words_queue, crypted_words_queue,stop_signal, block_length, shift_number, queue_lock))
        p.start()
        processes.append(p)

    #Filling the queue with words in text
    queue_lock.acquire()
    for words in words_list:
        words_queue.put(words)
    queue_lock.release()

    #Waiting until encrypting finished
    while True:
        queue_lock.acquire()
        if words_queue.empty() == True:
            queue_lock.release()
            break
        else:
            queue_lock.release()

    stop_signal.put("STOP")

    for p in processes:
        p.join()


    crypted_text = []
    while not crypted_words_queue.empty():
        crypted_text.append(crypted_words_queue.get())

    crypted_text = ''.join([str(elem) for elem in crypted_text])
    save_text(crypted_text, shift_number, process_number, block_length)

if __name__ == "__main__":
    main()