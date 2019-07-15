from multiprocessing import Process, Value
from mockingbird import mock

if __name__ == '__main__':
    stop = Value('i', 0)
    p = Process(target=mock, args=(stop, ))
    p.start()
    input("")
    stop.value = 1
    p.join()