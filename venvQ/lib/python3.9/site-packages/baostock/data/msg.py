# -*- coding:utf-8 -*-
"""
封装消息接口
@author: baostock.com
@group : baostock.com
@contact: baostock@163.com
"""
import baostock.common.contants as cons


class MessageHeader(object):

    def __init__(self, msg_type, total_msg_length):
        self.version = cons.BAOSTOCK_CLIENT_VERSION
        self.msg_type = msg_type
        self.total_msg_length = total_msg_length

    def to_message_header_msg(self):
        return self.version + cons.MESSAGE_SPLIT + self.msg_type \
                + cons.MESSAGE_SPLIT + self.total_msg_length

