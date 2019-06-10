import socket

def main():
    '''服务器端循环处理客户端'''
    # 创建socket
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定端口
    tcp_server_socket.bind(("", 7788))
    # 设置为被动监听
    tcp_server_socket.listen(128)
    # 等待客户端访问
    while True:
        print("等待新的客户端到来...")
        new_client_socket, client_addr = tcp_server_socket.accept()
        print("新的客户端到来%s" % str(client_addr))
        # 接收数据
        recv_data = new_client_socket.recv(1024)
        print(recv_data.decode("gbk"))
        # 响应
        new_client_socket.send("hahahaha---ok---".encode("gbk"))
        # 关闭socket
        new_client_socket.close()
        print("当前客户端处理完毕.")
    tcp_server_socket.close()

if __name__ == '__main__':
    main()