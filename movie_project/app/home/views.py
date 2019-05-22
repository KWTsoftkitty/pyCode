# -*- coding: utf-8 -*-
# @Date    : 2019-05-22 23:28:09
# @Author  : KangWenTao (285150572@qq.com)
# @Version : python 3.6.8 64bit

from . import home


@home.route("/")
def index():
    return "<h1 style='color:green'>this is home</h1>"
