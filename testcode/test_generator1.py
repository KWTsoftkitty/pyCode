def fib(num):
    '''
    生成器实现斐波那契数列
    '''
    a, b = 0, 1
    current_num = 0
    
    while current_num < num:
        yield a
        a, b = b, a+b
        current_num += 1
        
obj = fib(100)

for num in obj:
    print(num)