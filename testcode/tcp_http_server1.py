import socket
import re


def service_client(new_socket, request):
    """处理客户端的请求"""
    # 处理请求数据
    request_lines = request.splitlines()
    # 获取客户端请求的文件名
    file_name = ""
    ret = re.match(r'[^/]+(/[^ ]*)', request_lines[0])

    if ret:
        file_name = ret.group(1)
        if file_name == "/":
            file_name = "/index.html"

    # 读取文件内容，返回给客户端
    try:
        f = open("html" + file_name, 'rb')
    except Exception as ret:
        # 文件不存在，返回404
        response = "HTTP/1.1 404 NOT FOUND\r\n"
        response += "\r\n"
        response += "------file not found------"
        new_socket.send(response.encode("utf-8"))
    else:
        # 文件存在，返回文件内容
        html_content = f.read()
        f.close()

        response_header = "HTTP/1.1 200 OK\r\n"
        response_header += "Content-Length:%d\r\n" % len(html_content)
        response_header += "\r\n"
        response_body = html_content

        response = response_header.encode("utf-8") + response_body

        new_socket.send(response)


def main():
    """单进程、单线程、非阻塞的长链接"""
    # 1. 创建套接字
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 2. 绑定端口
    tcp_server_socket.bind(("", 7788))
    # 3. 设置被动监听
    tcp_server_socket.listen(128)
    tcp_server_socket.setblocking(False)  # 将套接字设置为非阻塞

    tcp_socket_list = list()
    while True:
        # 4. 等待客户端的连接
        try:
            new_socket, client_addr = tcp_server_socket.accept()
        except Exception as ret:
            pass
        else:
            new_socket.setblocking(False)
            tcp_socket_list.append(new_socket)

        for client_socket in tcp_socket_list:
            try:
                recv_data = client_socket.recv(1024).decode("utf-8")
            except Exception as ret:
                pass
            else:
                if recv_data:
                    service_client(client_socket, recv_data)
                else:
                    client_socket.close()
                    tcp_socket_list.remove(client_socket)

    # 6. 关闭套接字
    tcp_server_socket.close()


if __name__ == "__main__":
    main()
