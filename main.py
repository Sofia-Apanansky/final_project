from threading import Thread

from user_receive import main_user_receive
from user_send import main_user_send


def main():
    sender_thread = Thread(target=main_user_send)
    receiver_thread = Thread(target=main_user_receive)

    sender_thread.start()
    receiver_thread.start()

    sender_thread.join()
    receiver_thread.join()


if __name__ == '__main__':
    main()
