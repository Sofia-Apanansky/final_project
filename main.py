from threading import Thread

from user_receive import start_user_receive
from user_send import start_user_send


def start(peer_ip: str):
    sender_thread = Thread(target=start_user_send, args=(peer_ip,))
    receiver_thread = Thread(target=start_user_receive, args=(peer_ip,))

    sender_thread.start()
    receiver_thread.start()

    sender_thread.join()
    receiver_thread.join()


def main():
    start('127.0.0.1')


if __name__ == '__main__':
    main()
