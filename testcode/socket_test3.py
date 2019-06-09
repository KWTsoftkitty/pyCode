# -*- coding: utf-8 -*-
# @Date    : 2019-06-08 22:18:52
# @Author  : KangWenTao (285150572@qq.com)
# @Version : python 3.6.8 64bit
import socket
import os


def send_msg(udp_socket):
    '''发送消息'''
    dest_ip = input("请输入要发送的ip: ")
    dest_port = int(input("请输入要发送的端口号: "))
    send_msg = input("请输入要发送的数据: ")
    udp_socket.sendto(send_msg.encode("gbk"), (dest_ip, dest_port))


def recv_msg(udp_socket):
    '''接收消息'''
    resv_data = udp_socket.recvfrom(1024)
    print("%s: %s" % (resv_data[1], resv_data[0].decode("gbk")))    


def main():
    # 创建socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 绑定端口
    localaddr = ("", 7788)
    udp_socket.bind(localaddr)
    print("------xxx聊天器------")
    print("1.发送消息")
    print("2.接收消息")
    print("0.退出系统")
    while True:
        op = input("请选择功能: ")
        if op == "1":
            # 发送消息
            send_msg(udp_socket)
        elif op == "2":
            # 等待接收
            recv_msg(udp_socket)
        elif op == "0":
            break
        else:
            print("输入有误, 请重新输入...")
    # 关闭socket
    udp_socket.close()

if __name__ == "__main__":
    main()
