import socket


def main():
    # 创建tcp socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 创建连接
    server_ip = input("请输入要连接的服务器Ip: ")
    server_port = int(input("请输入要连接的服务器的端口号: "))
    server_addr = (server_ip, server_port)
    tcp_socket.connect(server_addr)
    # 发送数据
    send_data = input("请输入要发送的数据: ")
    tcp_socket.send(send_data.encode("gbk"))
    # 关闭连接
    tcp_socket.close()

if __name__ == '__main__':
    main()
