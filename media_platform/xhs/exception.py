from httpx import RequestError


class DataFetchError(RequestError):
    """something error when fetch"""


class IPBlockError(RequestError):
    """fetch so fast that the server block us ip"""

class UserBlockError(RequestError):
    """fetch too much that the server blocks this user"""
