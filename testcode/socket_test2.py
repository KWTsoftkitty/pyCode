# -*- coding: utf-8 -*-
# @Date    : 2019-06-08 19:14:56
# @Author  : KangWenTao (285150572@qq.com)
# @Version : python 3.6.8 64bit


import socket


def main():

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    localaddr = ("", 7788)
    udp_socket.bind(localaddr)
    while True:
        recv_data = udp_socket.recvfrom(1024)
        recv_msg = recv_data[0]
        recv_src = recv_data[1]
        print("%s: %s" % (str(recv_src), recv_msg.decode("gbk")))

    udp_socket.close()


if __name__ == "__main__":
    main()
