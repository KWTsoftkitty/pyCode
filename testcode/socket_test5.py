import socket

def main():
    '''服务器端'''
    # 创建socket
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定端口
    tcp_server_socket.bind(("", 7788))
    # 设置为被动监听
    tcp_server_socket.listen(128)
    # 等待客户端访问
    new_client_socket, client_addr = tcp_server_socket.accept()
    # 接收数据
    recv_data = new_client_socket.recvfrom(1024)
    print(recv_data[0].decode("gbk"))
    # 响应
    new_client_socket.send("hahahaha---ok---".encode("gbk"))
    # 关闭socket
    new_client_socket.close()
    tcp_server_socket.close()

if __name__ == '__main__':
    main()