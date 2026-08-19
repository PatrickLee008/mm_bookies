# MM Bookies 代码架构文档

## 项目架构总览

```
┌─────────────────────────────────────────────────────┐
│                   MM Bookies 系统架构                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────────────────┐    ┌───────────────────────┐ │
│  │   前端 (UniApp)    │    │    后端 (Flask)      │ │
│  │                   │    │                       │ │
│  │  ┌─────────────┐  │    │  ┌─────────────────┐  │ │
│  │  │   页面层     │  │    │  │    控制器层      │  │ │
│  │  │   Pages     │  │◄───│──│    Controllers  │  │ │
│  │  └─────────────┘  │    │  └────────┬────────┘  │ │
│  │  ┌─────────────┐  │    │  ┌────────▼────────┐  │ │
│  │  │   组件层     │  │    │  │    服务层       │  │ │
│  │  │  Components │  │    │  │    Services     │  │ │
│  │  └─────────────┘  │    │  └────────┬────────┘  │ │
│  │  ┌─────────────┐  │    │  ┌────────▼────────┐  │ │
│  │  │   状态层     │  │    │  │    模型层       │  │ │
│  │  │   Vuex      │  │    │  │    Models       │  │ │
│  │  └─────────────┘  │    │  └─────────────────┘  │ │
│  └───────────────────┘    └───────────────────────┘ │
│              │                       │               │
│              │     ┌─────────────────┤               │
│              │     │                 │               │
│              ▼     ▼                 ▼               │
│  ┌───────────────┐ ┌───────────────────────────────┐ │
│  │   WebSocket   │ │         MySQL / Redis        │ │
│  │   实时通信     │ │         数据库 / 缓存         │ │
│  └───────────────┘ └───────────────────────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 后端架构详解

### 1. 项目结构

```
app_server/
├── app_server/
│   ├── __init__.py          # 应用初始化
│   ├── app.py               # 路由注册（从父目录导入）
│   ├── config.py            # 配置管理
│   ├── setting.py           # 环境配置
│   ├── logger.py            # 日志配置
│   │
│   ├── controller/          # 控制器层
│   │   ├── AppUserController.py      # 用户管理
│   │   ├── MatchController.py        # 赛事管理
│   │   ├── OrderController.py        # 订单管理
│   │   ├── ChargeController.py       # 充值管理
│   │   ├── WithDrawController.py    # 提现管理
│   │   ├── BankCardController.py    # 银行卡管理
│   │   ├── AWCGameController.py     # AWC游戏
│   │   ├── CouponController.py      # 优惠券
│   │   ├── PromotionController.py # 促销活动
│   │   ├── MessageController.py     # 消息管理
│   │   └── ...                      # 其他控制器
│   │
│   ├── model/               # 数据模型层
│   │   ├── AppMemberModel.py        # 用户模型
│   │   ├── MatchModel.py            # 赛事模型
│   │   ├── OrderModel.py           # 订单模型
│   │   ├── AwcGameModel.py         # AWC游戏模型
│   │   └── ...                      # 其他模型
│   │
│   ├── service/             # 业务逻辑层
│   │   ├── AWCApiService.py        # AWC API服务
│   │   ├── PayOrderService.py      # 支付服务
│   │   ├── RiskManagementService.py # 风险管理
│   │   └── ...                      # 其他服务
│   │
│   ├── utils/               # 工具类
│   │   ├── Kits.py                  # 通用工具
│   │   ├── DataVo.py               # 数据响应
│   │   ├── BaseSaasModel.py        # 模型基类
│   │   ├── OrmUttil.py             # ORM工具
│   │   ├── MessageHelper.py        # 消息帮助类
│   │   └── snowflake.py           # ID生成器
│   │
│   └── static/              # 静态文件
│       └── img/            # 图片资源
│
├── requirements.txt         # Python依赖
├── app.py                   # 应用入口
└── uwsgi_conf.ini          # uWSGI配置
```

### 2. 请求处理流程

```
HTTP请求流程:

┌──────────┐    ┌──────────┐    ┌───────────┐    ┌───────────┐
│  Client  │───▶│  Nginx   │───▶│  uWSGI    │───▶│  Flask    │
│  (前端)   │    │  (反向代理) │   │  (应用服务器)│   │  (应用)    │
└──────────┘    └──────────┘    └───────────┘    └─────┬─────┘
                                                       │
                                                       ▼
                                             ┌─────────────────┐
                                             │  控制器 Controller │
                                             │                   │
                                             │  @auth.login_req │
                                             └────────┬─────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │  服务层 Service   │
                                             │                   │
                                             └────────┬─────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │  模型层 Model     │
                                             │                   │
                                             └────────┬─────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │   MySQL/Redis    │
                                             │                   │
                                             └─────────────────┘
```

### 3. 控制器层设计

#### 3.1 用户控制器 (AppUserController)

**职责**: 用户认证、注册、信息管理

```python
@app_user.route('/login', methods=['POST'])
def login():
    """用户登录 - 处理加密参数解密、密码验证、Token生成"""

@app_user.route('/add', methods=['POST'])
def add_app_user():
    """用户注册 - OTP验证、推荐关系、创建账户"""

@app_user.route('/user_info', methods=['GET'])
@auth.login_required
def get_user_info():
    """获取用户信息 - 需要认证"""

@app_user.route('/edit', methods=['POST'])
@auth.login_required
def edit_app_user():
    """编辑用户信息 - 密码修改、个人信息更新"""
```

**关键特性**:
- 支持OTP验证码
- 推荐人关系建立
- 广告链接追踪
- 登录设备检测
- 行为日志记录

#### 3.2 赛事控制器 (MatchController)

**职责**: 赛事数据、投注处理

```python
@match.route('/list', methods=['GET'])
def get_match_list():
    """获取赛事列表 - 过滤、排序、分页"""

@match.route('/detail/<match_id>', methods=['GET'])
def get_match_detail(match_id):
    """获取赛事详情 - 包含赔率、投注选项"""
```

#### 3.3 AWC游戏控制器 (AWCGameController)

**职责**: AWC游戏集成、会话管理

```python
@awc_game_bp.route('/list', methods=['GET'])
@auth.login_required
def get_game_list():
    """获取游戏列表"""

@awc_game_bp.route('/launch', methods=['POST'])
@auth.login_required
def launch_game():
    """启动游戏 - 余额检查、API调用"""

@awc_game_bp.route('/balance', methods=['GET'])
@auth.login_required
def get_balance():
    """获取AWC余额"""

@awc_game_bp.route('/sync_balance', methods=['POST'])
@auth.login_required
def sync_balance():
    """同步余额 - 后端到AWC"""
```

### 4. 服务层设计

#### 4.1 AWCApiService

**职责**: AWC API统一封装

```python
class AWCApiService:
    @staticmethod
    def launch_game(game_code, wallet_type):
        """启动游戏"""
    
    @staticmethod
    def get_balance(user_id):
        """获取用户AWC余额"""
    
    @staticmethod
    def sync_balance(user_id):
        """同步余额"""
    
    @staticmethod
    def logout_game(session_id):
        """登出游戏"""
```

#### 4.2 PayOrderService

**职责**: 支付订单处理

```python
class PayOrderService:
    @staticmethod
    def create_order(order_data):
        """创建支付订单"""
    
    @staticmethod
    def handle_callback(callback_data):
        """处理支付回调"""
```

### 5. 模型层设计

#### 5.1 模型基类 (BaseSaasModel)

```python
class BaseSaasModel(db.Model):
    """所有模型的基类，提供公共字段和方法"""
    
    id = Column(String(32), primary_key=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    del_flag = Column(Integer, default=0)  # 软删除标记
    
    def to_dict(self):
        """转换为字典"""
```

#### 5.2 核心模型

| 模型 | 表名 | 说明 |
|------|------|------|
| AppMember | m_app_member | 用户信息 |
| Match | m_match | 赛事信息 |
| Order | m_app_bet_order | 投注订单 |
| ChargeApply | m_charge_apply | 充值申请 |
| WithDraw | m_withdraw | 提现申请 |
| AppMemberBank | m_app_member_bank | 银行卡 |
| AwcGameSession | m_awc_game_session | AWC游戏会话 |

### 6. 认证机制

#### 6.1 JWT Token认证

```python
# Token生成
def generate_auth_token(self, expiration=60 * 60 * 12):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    token = s.dumps({'member_id': self.id})
    Redis.write(f"user_token|{self.id}", token, expiration)
    return token

# Token验证
@auth.verify_token
def verify_token(token):
    user = AppMember.verify_auth_token(token)
    if not user:
        return False
    g.user = user
    return True
```

#### 6.2 认证装饰器

```python
@auth.login_required  # 需要登录认证
def protected_endpoint():
    user = g.user
    # 处理业务逻辑
```

---

## 前端架构详解

### 1. 项目结构

```
mm_bookies_uniapp/
├── pages/                     # 页面文件
│   ├── match/                # 赛事相关
│   │   ├── home.vue         # 赛事首页
│   │   ├── score.vue        # 比分页面
│   │   └── components/       # 赛事组件
│   │       ├── match_detail.vue
│   │       ├── bets_slip.vue
│   │       └── count_down.vue
│   │
│   ├── wallet/              # 钱包相关
│   │   ├── wallet.vue      # 钱包首页
│   │   ├── deposit.vue     # 充值
│   │   ├── withdraw.vue    # 提现
│   │   └── history.vue     # 交易历史
│   │
│   ├── orders/             # 订单相关
│   │   ├── home.vue       # 订单列表
│   │   └── order.js
│   │
│   ├── login/             # 登录注册
│   │   ├── login.vue
│   │   └── register.vue
│   │
│   ├── ucenter/          # 用户中心
│   │   ├── home.vue      # 个人中心
│   │   ├── profile.vue   # 个人信息
│   │   ├── charge.vue    # 充值
│   │   ├── withdraw.vue  # 提现
│   │   ├── invite/       # 邀请功能
│   │   └── message.vue   # 消息
│   │
│   └── payment/          # 支付
│       └── payment.vue   # 支付页面
│
├── components/            # 公共组件
│   ├── common/           # 通用组件
│   │   ├── header.vue   # 顶部导航
│   │   ├── footer.vue   # 底部导航
│   │   ├── login_modal.vue
│   │   └── selector.vue
│   ├── uni-popup/       # 弹窗组件
│   └── tki-qrcode/      # 二维码组件
│
├── utils/               # 工具函数
│   ├── my.js           # HTTP封装
│   ├── http.js         # 请求核心
│   ├── websocket.js    # WebSocket
│   ├── config.js       # 配置
│   ├── language.js     # 语言包
│   └── store/          # Vuex
│
├── store/              # Vuex状态管理
│   ├── index.js        # store入口
│   ├── state.js        # 状态定义
│   ├── mutations.js    # 同步修改
│   └── actions.js      # 异步操作
│
├── locale/            # 国际化
│   ├── cn.json        # 中文
│   ├── en.json        # 英文
│   ├── mm.json        # 缅甸语
│   ├── th.json        # 泰文
│   └── i18n.js        # 国际化配置
│
├── colorui/           # UI组件库
│   ├── main.css
│   ├── icon.css
│   └── components/
│
├── static/           # 静态资源
│   ├── icon/        # 图标
│   ├── image/       # 图片
│   └── font/        # 字体
│
├── App.vue          # 应用入口
├── main.js          # 主入口
├── manifest.json    # 应用配置
└── pages.json       # 页面路由
```

### 2. 页面路由配置

[pages.json](file:///d:\GIT\jiaxu\04-MMBookies\mm_bookies\mm_bookies_uniapp\pages.json):

```json
{
    "pages": [
        {
            "path": "pages/match/home",
            "style": {}
        },
        {
            "path": "pages/wallet/wallet",
            "style": {}
        }
    ],
    "globalStyle": {
        "navigationBarBackgroundColor": "#0081ff",
        "navigationStyle": "custom"
    }
}
```

### 3. 页面生命周期

```javascript
// 页面.vue
export default {
    data() {
        return {
            title: 'Hello'
        }
    },
    
    onLoad() {
        // 页面加载时触发
        this.loadData();
    },
    
    onShow() {
        // 页面显示时触发
        this.refreshData();
    },
    
    onReady() {
        // 页面初次渲染完成
    },
    
    onHide() {
        // 页面隐藏时触发
    },
    
    onUnload() {
        // 页面卸载时触发
    },
    
    methods: {
        loadData() {
            this.$http.get('/api/endpoint', {}, (res) => {
                this.title = res.data.title;
            });
        }
    }
}
```

### 4. 组件通信

#### 4.1 Props传递

```vue
<!-- 父组件 -->
<child-component :title="parentTitle" @event="handleEvent" />

<!-- 子组件 -->
<template>
    <view>{{ title }}</view>
</template>

<script>
export default {
    props: ['title'],
    methods: {
        sendToParent() {
            this.$emit('event', 'data');
        }
    }
}
</script>
```

#### 4.2 Vuex状态管理

```javascript
// state.js
export default {
    userInfo: null,
    token: null
}

// mutations.js
export default {
    SET_USER_INFO(state, userInfo) {
        state.userInfo = userInfo;
    }
}

// actions.js
export default {
    async login({ commit }, credentials) {
        const res = await this.$http.post('/login', credentials);
        commit('SET_USER_INFO', res.data);
    }
}

// 组件中使用
this.$store.commit('SET_USER_INFO', userInfo);
this.$store.dispatch('login', credentials);
```

### 5. HTTP请求封装

[utils/my.js](file:///d:\GIT\jiaxu\04-MMBookies\mm_bookies\mm_bookies_uniapp\utils\my.js):

```javascript
// 配置API地址
http.setBaseUrl(siteinfo.apiUrl);

// GET请求
this.$http.get('/api/endpoint', {}, (res) => {
    if (res.statusCode === 200) {
        console.log(res.data);
    }
});

// POST请求
this.$http.post('/api/endpoint', { data: 'value' }, (res) => {
    console.log(res.data);
});
```

### 6. WebSocket实时通信

[utils/websocket.js](file:///d:\GIT\jiaxu\04-MMBookies\mm_bookies\mm_bookies_uniapp\utils\websocket.js):

```javascript
// 连接WebSocket
this.$websocket.connect(userId, token);

// 监听消息
uni.$on('websocket:message', (message) => {
    // 处理消息
    uni.showToast({
        title: message.title,
        icon: 'none'
    });
});

// 发送消息
this.$websocket.send({
    type: 'heartbeat',
    timestamp: Date.now()
});

// 主动关闭
this.$websocket.close();
```

---

## 数据流设计

### 1. 用户登录流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   前端      │    │   后端API   │    │    数据库    │    │    Redis    │
│  (UniApp)   │    │  (Flask)   │    │   (MySQL)   │    │   (Cache)   │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                   │                   │                   │
       │ 1.输入用户名密码   │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │ 2.查询用户         │                   │
       │                   │──────────────────▶│                   │
       │                   │◀──────────────────│                   │
       │                   │ 3.验证密码         │                   │
       │                   │                   │                   │
       │ 4.返回JWT Token   │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │ 5.存储Token到Redis │                   │
       │                   │───────────────────────────────────────▶│
       │                   │                   │                   │
       │ 6.保存Token       │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │ 7.获取用户信息     │                   │
       │                   │──────────────────▶│                   │
       │                   │◀──────────────────│                   │
       │ 8.返回用户信息     │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
```

### 2. 投注流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   前端      │    │   后端API   │    │    数据库    │    │   业务逻辑  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                   │                   │                   │
       │ 1.选择投注选项     │                   │                   │
       │ 2.输入投注金额     │                   │                   │
       │ 3.提交投注         │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │ 4.验证Token        │                   │
       │                   │                   │                   │
       │                   │ 5.检查余额         │                   │
       │                   │──────────────────▶│                   │
       │                   │◀──────────────────│                   │
       │                   │ 6.余额不足?        │                   │
       │                   │                   │                   │
       │ 7.余额不足提示     │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │                   │ 8.创建订单         │                   │
       │                   │──────────────────▶│                   │
       │                   │◀──────────────────│                   │
       │                   │                   │                   │
       │                   │ 9.扣除余额         │                   │
       │                   │──────────────────▶│                   │
       │                   │◀──────────────────│                   │
       │                   │                   │                   │
       │ 10.返回投注成功    │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
```

---

## 安全机制

### 1. 认证授权

```python
# 请求认证
@auth.login_required
def protected_endpoint():
    user = g.user
    # 处理业务逻辑
```

### 2. 参数验证

```python
# 输入参数验证
def validate_input(data):
    if not data.get('amount') or data['amount'] <= 0:
        return False, "Invalid amount"
    if not data.get('match_id'):
        return False, "Match ID required"
    return True, None
```

### 3. SQL注入防护

```python
# 使用参数化查询
user = AppMember.query.filter_by(username=username).first()

# 避免字符串拼接SQL
query = f"SELECT * FROM users WHERE id = {user_id}"  # 危险！
query = db.session.query(User).filter_by(id=user_id)  # 安全
```

### 4. XSS防护

```javascript
// 前端转义HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
```

---

## 扩展性设计

### 1. 蓝图模式

新增控制器只需：

```python
# 1. 创建控制器文件
# app_server/controller/NewController.py
new_controller = Blueprint('new', __name__)

@new_controller.route('/endpoint', methods=['GET'])
def new_endpoint():
    return jsonify({'message': 'success'})

# 2. 在app.py中注册
from app_server.controller.NewController import new_controller
app.register_blueprint(new_controller, url_prefix='/new')
```

### 2. 服务扩展

```python
# app_server/service/NewService.py
class NewService:
    @staticmethod
    def process(data):
        # 业务逻辑
        pass
```

### 3. 模型扩展

```python
# 新增模型只需继承BaseSaasModel
class NewModel(BaseSaasModel):
    __tablename__ = 'new_table'
    
    id = Column(String(32), primary_key=True)
    name = Column(String(100))
```

### 4. 前端页面扩展

```json
// 1. 在pages.json中添加路由
{
    "pages": [
        {
            "path": "pages/new/page",
            "style": {}
        }
    ]
}

// 2. 创建页面文件
// pages/new/page.vue
<template>
    <view>新页面</view>
</template>
```

---

## 性能优化策略

### 1. 后端优化

- **数据库索引**: 为高频查询字段添加索引
- **缓存策略**: Redis缓存热点数据
- **连接池**: 合理配置数据库连接池
- **异步处理**: 非实时任务使用异步队列

### 2. 前端优化

- **图片优化**: 压缩图片、使用懒加载
- **代码分割**: 按需加载页面组件
- **数据缓存**: 本地Storage缓存数据
- **请求合并**: 批量请求减少网络开销

### 3. 网络优化

- **CDN加速**: 静态资源使用CDN
- **Gzip压缩**: 开启HTTP压缩
- **连接复用**: HTTP keep-alive

---

## 监控与日志

### 1. 日志记录

```python
# 结构化日志
import logging

logger = logging.getLogger(__name__)

logger.info(f"用户 {user_id} 登录成功")
logger.error(f"支付回调处理失败: {error}")
logger.warning(f"余额不足，用户 {user_id}")
```

### 2. 性能监控

```python
import time

@app.route('/api/endpoint')
def endpoint():
    start = time.time()
    # 业务逻辑
    duration = time.time() - start
    logger.info(f"API耗时: {duration}ms")
```

### 3. 异常捕获

```python
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"未处理异常: {str(e)}")
    return jsonify({'message': 'Internal server error'}), 500
```

---

## 相关文档链接

- [开发指导文档](./DEVELOPMENT_GUIDE.md)
- [问题修复指南](./TROUBLESHOOTING_GUIDE.md)
- [UniApp官方文档](https://uniapp.dcloud.io/)
- [Flask官方文档](https://flask.palletsprojects.com/)
- [Vuex官方文档](https://vuex.vuejs.org/)
