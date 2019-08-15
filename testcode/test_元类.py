def upper_class(class_name, parents_name, class_attr):

    new_attr = dict()
    for name,value in class_attr.items():
        if not name.startswith("__"):
            new_attr[name.upper()] = value

    return type(class_name, parents_name, new_attr)


class Foo(object, metaclass=upper_class):

    bar = "zip"


f = Foo()

print(hasattr(Foo, "bar"))
print(hasattr(Foo, "BAR"))

print(f.BAR)
