URL_ROUTE_DICK = dict()

def route(url):
    def set_func(func):
        URL_ROUTE_DICK[url] = func
        def call_func(*args, **kwargs):
            return func(*args, **kwargs)
        return call_func
    return set_func


@route("/center.py")
def center():
    with open("./templates/center.html", encoding="utf-8") as f:
        return f.read()


@route("/index.py")
def index():
    with open("./templates/index.html", encoding="utf-8") as f:
        return f.read()


def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html;charset=utf-8')])

    file_name = env["PATH_INFO"]

    # if file_name == "/index.py":
    #     return index()
    # elif file_name == "/center.py":
    #     return center()
    # else:
    #     return "Hello World! 我爱你中国......"
    try:
        return URL_ROUTE_DICK[file_name]()
    except Exception as e:
        return "产生异常: %s" % str(e)
