# -*- coding: utf-8 -*-
# @Date    : 2019-06-08 17:44:57
# @Author  : KangWenTao (285150572@qq.com)
# @Version : python 3.6.8 64bit

import socket


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        send_data = input("请输入要发送的数据： ")
        if send_data == "exit":
            break
        s.sendto(send_data.encode('gbk'), ("192.168.0.100", 8080))

    s.close()


if __name__ == "__main__":
    main()
