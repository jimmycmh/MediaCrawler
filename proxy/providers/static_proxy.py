# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/4/5 09:43
# @Desc    : 快代理HTTP实现，官方文档：https://www.kuaidaili.com/?ref=ldwkjqipvz6c
import os
import re
from typing import Dict, List

import httpx
from pydantic import BaseModel, Field

from proxy import IpCache, IpInfoModel, ProxyProvider
from proxy.types import ProviderNameEnum
from tools import utils

import config

class StaticProxy(ProxyProvider):
    def __init__(self):
        pass

    async def get_proxies(self, num: int) -> List[IpInfoModel]:
        proxies = config.IP_PROXY_LIST
        ip_infos: List[IpInfoModel] = []
        for proxy in proxies:
            fields = proxy.split(':')
            ip = IpInfoModel(
                    ip=fields[0],
                    port=fields[1],
                    protocol='http://',
                    user=fields[2],
                    password=fields[3],
                    expired_time_ts=utils.get_current_timestamp()+604800000)
            ip_infos.append(ip)

        return ip_infos


def new_static_proxy() -> StaticProxy:
    """
    构造快代理HTTP实例
    Returns:

    """
    return StaticProxy()
