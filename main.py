from threading import Thread

from picture_encryption_socket import PictureEncryptionSocket
def send(a: PictureEncryptionSocket):
    while True:
        message= input()
        a.send(message.encode())

def receive(a: PictureEncryptionSocket):
    while True:
        print(a.receive().decode())

if __name__ == '__main__':
    a= PictureEncryptionSocket('127.0.0.1')
    a.connect()

    send_thread= Thread(target=send,args=(a,))
    receive_thread= Thread(target=receive,args=(a,))

    send_thread.start()
    receive_thread.start()

    send_thread.join()
    receive_thread.join()

