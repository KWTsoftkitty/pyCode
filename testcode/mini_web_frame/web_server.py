import socket
import multiprocessing
import re
import sys


class WSGIServer(object):
    """服务器类"""

    def __init__(self, port, app, static_path):
        """初始化"""
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.tcp_server_socket.bind(("", port))

        self.tcp_server_socket.listen(128)

        self.application = app
        self.static_path = static_path

    def run_forever(self):
        """循环处理客户端请求"""
        while True:
            new_socket, client_addr = self.tcp_server_socket.accept()

            # 多进程方式处理客户端请求
            p = multiprocessing.Process(target=self.service_client, args=(new_socket,))
            p.start()

            # 关闭子进程的一个引用
            new_socket.close()

    def service_client(self, new_socket):
        """处理客户端请求并响应数据"""
        request = new_socket.recv(1024).decode("utf-8")
        request_lines = request.splitlines()

        # 正则获取客户端请求的数据
        file_name = ""
        ret = re.match(r'[^/]+(/[^ ]*)', request_lines[0])
        if ret:
            file_name = ret.group(1)
            if file_name == "/":
                file_name = "/index.html"

        # 返回http数据给客户端浏览器
        if not file_name.endswith(".py"):
            # 请求静态资源
            try:
                f = open(self.static_path + file_name, "rb")
            except:
                response = "HTTP/1.1 404 NOT FOUND\r\n"
                response += "\r\n"
                response += "------file not found------"
                new_socket.send(response.encode("utf-8"))
            else:
                html_content = f.read()
                f.close()
                response = "HTTP/1.1 200 OK\r\n"
                response += "\r\n"
                new_socket.send(response.encode("utf-8"))
                new_socket.send(html_content)
        else:
            # 请求以.py结尾的动态资源
            env = dict()
            env["PATH_INFO"] = file_name
            body = self.application(env, self.set_response_header)

            header = "HTTP/1.1 %s\r\n" % self.status

            for temp in self.headers:
                header += "%s:%s\r\n" % (temp[0], temp[1])

            header += "\r\n"
            response = header + body
            new_socket.send(response.encode("utf-8"))

        new_socket.close()

    def set_response_header(self, status, headers):
        """WSGI获取响应头"""
        self.status = status
        self.headers = [("server", "mini web v1.0")]
        self.headers += headers


def main():
    """入口函数"""
    # 获取运行时参数
    if len(sys.argv) == 3:
        try:
            port = int(sys.argv[1])
            frame_app_name = sys.argv[2]
        except Exception as e:
            print("端口输入错误......")
            return
    else:
        print("请按照以下方式运行:")
        print("python3 xxxx.py 7890 mini_frame:application")
        return

    # 获取框架名称
    ret = re.match(r"([^:]+):(.*)", frame_app_name)
    if ret:
        frame_name = ret.group(1)
        app_name = ret.group(2)
    else:
        print("请按照以下方式运行:")
        print("python3 xxxx.py 7890 mini_frame:application")
        return

    # 读取conf配置文件中的相关配置
    with open("./web_server.conf") as f:
        conf_info = eval(f.read())

    # import导入框架
    sys.path.append(conf_info["dynamic_path"])
    frame = __import__(frame_name)
    app = getattr(frame, app_name)

    web_server = WSGIServer(port, app, conf_info["static_path"])
    web_server.run_forever()


if __name__ == '__main__':
    main()
