# 元类
class ModelMetaClass(type):

    def __new__(cls, name, bases, attr):
        mappings = {}
        for k, v in attr.items():
            if isinstance(v, tuple):
                print("Found mapping %s ==> %s" % (k, v))
                mappings[k] = v

        for k in mappings.keys():
            attr.pop(k)

        attr["__mappings__"] = mappings
        attr["__table__"] = name

        return type.__new__(cls, name, bases, attr)

# 模板父类
class Model(object, metaclass=ModelMetaClass):
    
    def __init__(self, **kwargs):
        # 初始化实例对象
        for name, value in kwargs.items():
            setattr(self, name, value)

    def save(self):
        # 实例方法---数据库插入
        fields = []
        args = []
        for k, v in self.__mappings__.items():
            fields.append(v[0])
            args.append(getattr(self, k, None))

        args_temp = []
        for arg in args:
            if isinstance(arg, int):
                args_temp.append(str(arg))
            elif isinstance(arg, str):
                args_temp.append("""'%s'""" % arg)

        sql = "insert into %s (%s) values (%s)" % (self.__table__, ','.join(fields), ','.join(args_temp))
        print("SQL: %s" % sql)


# User类
class User(Model):
    
    uid = ("uid", "int unsigned")
    name = ("username", "varchar(30)")
    email = ("email", "varchar(30)")
    password = ("password", "varchar(30)")


user = User(uid=12345, name="sally", email="sally@123.com", password=123456)
user.save()


