# -*- coding: utf-8 -*-
# @Date    : 2019-05-22 23:25:06
# @Author  : KangWenTao (285150572@qq.com)
# @Version : python 3.6.8 64bit


from flask import Blueprint


admin = Blueprint("admin", __name__)

import app.admin.views