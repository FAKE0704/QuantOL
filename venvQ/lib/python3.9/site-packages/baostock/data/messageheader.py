# -*- coding:utf-8 -*-
"""
封装消息头
@author: baostock.com
@group : baostock.com
@contact: baostock@163.com
"""
import baostock.common.contants as cons
import baostock.util.stringutil as strutil


def to_message_header(msg_type, total_msg_length):

    return_str = cons.BAOSTOCK_CLIENT_VERSION + cons.MESSAGE_SPLIT + msg_type \
                 + cons.MESSAGE_SPLIT \
                 + strutil.add_zero_for_string(total_msg_length, 10, True)
    return return_str
