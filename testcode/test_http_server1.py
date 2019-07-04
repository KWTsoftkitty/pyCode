import socket


def service_client(new_socket):
    """处理客户端请求"""
    # 1. 接收客户端的数据
    request = new_socket.recv(1024)
    print(request)
    # 2. 准备响应给客户端的数据
    response = "HTTP/1.1 200 OK\r\n"
    response += "\r\n"
    response += "<h1 style='color:red'>hahahaha</h1>"
    # 响应数据给客户端
    new_socket.send(response.encode(encoding='utf_8'))
    # 关闭套接字
    new_socket.close()


def main():
    """简单的返回固定页面的http服务器"""
    # 1. 创建套接字
    tcp_socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 2. 绑定
    tcp_socket_server.bind(("", 7788))
    # 3. 设置被动监听
    tcp_socket_server.listen(128)
    # 4. 等待客户端的连接
    while True:
        new_socket, client_address = tcp_socket_server.accept()
        # 5. 处理客户端的请求
        service_client(new_socket)
    # 6. 关闭套接字
    tcp_socket_server.close()


if __name__ == "__main__":
    main()