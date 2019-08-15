def test1(k, b):
    """测试闭包"""
    def create_y(x):
        print(k*x + b)
    return create_y

line_1 = test1(1, 2)
line_1(1)
line_1(2)
line_1(3)
line_1(11)
line_1(22)
line_1(33)
