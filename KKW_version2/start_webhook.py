#!/usr/bin/env python
# coding=utf-8
localhost = '0.0.0.0'
from wsgiref.simple_server import make_server
from webhook import application
port = 80
httpd = make_server(localhost,port, application)
print('Serving HTTP on port %d.'%port)
httpd.serve_forever()
