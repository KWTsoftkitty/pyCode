def set_level(level):
    def set_func(func):
        def call_func(*args, **kwargs):
            if level == 1:
                print("---权限级别1验证---")
            elif level == 2:
                print("---权限级别2验证---")
            return func()
        return call_func
    return set_func


@set_level(1)
def test1():
    print("---test1---")


@set_level(2)
def test2():
    print("---test2---")


test1()
test2()
