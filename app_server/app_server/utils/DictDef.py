import random
import uuid
from datetime import datetime
from typing import List

from flask import jsonify
from user_agents import parse


# 字典定义
DbToDictExclude = ["password", "salt", 'create_by_id', 'update_by_id', 'del_flag', 'tenant_id']
