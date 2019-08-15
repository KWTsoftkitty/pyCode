import time


class Classmate(object):
    """迭代器和可迭代对象"""
    def __init__(self):
        self.names = list()
        self.current_num = 0
        
    def add(self, name):
        self.names.append(name)
        
    def __iter__(self):
        """可迭代对象"""
        return self
    
    def __next__(self):
        """迭代器"""
        if self.current_num < len(self.names):
            ret = self.names[self.current_num]
            self.current_num += 1
            return ret
        else:
            raise StopIteration
        

classmate = Classmate()
classmate.add("sally")
classmate.add("lucy")
classmate.add("lily")
classmate.add("allen")
classmate.add("tom")

for name in classmate:
    print(name)
    time.sleep(1)

