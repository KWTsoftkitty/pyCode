from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FDFSStorage(Storage):
    '''自定义文件存储类'''
    def __init__(self, client_conf=None, base_url=None):
        '''初始化client.conf和nginx服务器ip:port'''
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf
        if base_url is None:
            base_url = settings.NGINX_BASE_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        '''打开文件时使用:不涉及'''
        pass

    def _save(self, name, content):
        '''上传文件时使用'''
        client = Fdfs_client(self.client_conf)
        # 按文件内容上传文件
        res = client.upload_by_buffer(content.read())
        # res:
        # return dict {
        #     'Group name'      : group_name,
        #     'Remote file_id'  : remote_file_id,
        #     'Status'          : 'Upload successed.',
        #     'Local file name' : '',
        #     'Uploaded size'   : upload_size,
        #     'Storage IP'      : storage_ip
        # } if success else None
        # 判断上传结果
        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('文件上传到fastdfs失败')
        # 上传成功，返回如：group1/M00/00/00/wKgAZ11dGjSAcWZSAAAX1PFRdzg646
        filename = res.get('Remote file_id')
        return filename

    def exists(self, name):
        '''django判断上传的文件是否已存在,不存在返回False, 存在返回True：不涉及'''
        return False

    def url(self, name):
        '''返回已上传文件的url链接，可直接通过浏览器访问到文件'''
        return self.base_url + name


