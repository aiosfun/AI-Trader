# AI-Trader 项目指南

## 项目概述

AI-Trader 是一个基于大语言模型的自主交易系统，允许多个AI模型在纳斯达克100、上证50和加密货币市场中进行完全自主的交易决策和竞争。该项目采用MCP（Model Context Protocol）工具链架构，使AI能够通过标准化工具调用完成所有交易操作。

### 核心特性

- 🤖 **完全自主决策**: AI代理100%独立分析、决策、执行，零人工干预
- 🛠️ **纯工具驱动架构**: 基于MCP工具链，AI通过标准化工具调用完成所有交易操作
- 🏆 **多模型竞技场**: 部署多个AI模型（GPT、Claude、Qwen等）进行竞争性交易
- 📊 **实时性能分析**: 完整的交易记录、持仓监控和盈亏分析
- 🔍 **智能市场情报**: 集成Jina搜索，获取实时市场新闻和财务报告
- ⏰ **历史回放功能**: 时间段回放功能，自动过滤未来信息

## 技术栈

- **语言**: Python 3.10+
- **核心框架**: LangChain
- **AI模型**: 支持OpenAI GPT、Anthropic Claude、Google Gemini、DeepSeek、Qwen等
- **数据源**: Alpha Vantage (美股和加密货币)、Tushare (A股)
- **工具链**: MCP (Model Context Protocol)
- **前端**: HTML/CSS/JavaScript (实时交易仪表板)

## 项目结构

```
AI-Trader/
├── main.py                    # 主程序入口
├── agent/                     # AI代理模块
│   ├── base_agent/           # 美股交易代理
│   ├── base_agent_astock/    # A股交易代理
│   └── base_agent_crypto/    # 加密货币交易代理
├── agent_tools/              # MCP工具链
├── configs/                  # 配置文件
├── data/                     # 数据存储
│   ├── agent_data/          # AI交易记录(美股)
│   ├── agent_data_astock/   # AI交易记录(A股)
│   ├── agent_data_crypto/   # AI交易记录(加密货币)
│   ├── A_stock/             # A股市场数据
│   └── crypto/              # 加密货币市场数据
├── prompts/                  # 提示词系统
├── scripts/                  # 便捷启动脚本
└── docs/                     # 前端界面
```

## 构建和运行

### 环境配置

1. **克隆项目**
```bash
git clone https://github.com/HKUDS/AI-Trader.git
cd AI-Trader
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，填入你的API密钥
```

### 必需的API密钥

- **OpenAI API**: 用于AI模型
- **Alpha Vantage API**: 用于美股和加密货币数据
- **Jina AI API**: 用于市场信息搜索
- **Tushare Token**: 用于A股数据(可选)

### 运行方式

#### 使用便捷脚本(推荐)

**美股市场 (NASDAQ 100)**
```bash
# 一键启动(完整工作流)
bash scripts/main.sh

# 或分步运行
bash scripts/main_step1.sh  # 步骤1: 准备数据
bash scripts/main_step2.sh  # 步骤2: 启动MCP服务
bash scripts/main_step3.sh  # 步骤3: 运行交易代理
```

**A股市场 (SSE 50)**
```bash
bash scripts/main_a_stock_step1.sh  # 步骤1: 准备A股数据
bash scripts/main_a_stock_step2.sh  # 步骤2: 启动MCP服务
bash scripts/main_a_stock_step3.sh  # 步骤3: 运行A股交易代理
```

**加密货币市场 (BITWISE10)**
```bash
bash scripts/main_crypto_step1.sh  # 步骤1: 准备加密货币数据
bash scripts/main_crypto_step2.sh  # 步骤2: 启动MCP服务
bash scripts/main_crypto_step3.sh  # 步骤3: 运行加密货币交易代理
```

**Web界面**
```bash
bash scripts/start_ui.sh
# 访问: http://localhost:8888
```

#### 手动运行

**步骤1: 数据准备**
```bash
# 美股数据
cd data
python get_daily_price.py
python merge_jsonl.py

# A股数据
cd data/A_stock
python get_daily_price_tushare.py
python merge_jsonl_tushare.py

# 加密货币数据
cd data/crypto
python get_daily_price_crypto.py
python merge_crypto_jsonl.py
```

**步骤2: 启动MCP服务**
```bash
cd ./agent_tools
python start_mcp_services.py
```

**步骤3: 启动AI交易代理**
```bash
# 美股交易
python main.py configs/default_config.json

# A股交易
python main.py configs/astock_config.json

# 加密货币交易
python main.py configs/default_crypto_config.json
```

## 开发约定

### 代码结构约定

- **代理类**: 继承自BaseAgent，位于`agent/`目录下的相应子目录
- **工具函数**: 位于`agent_tools/`目录，遵循MCP协议
- **配置文件**: JSON格式，位于`configs/`目录
- **数据格式**: 统一使用JSONL格式存储交易记录和市场数据

### 交易规则

- **美股**: T+0交易，最小单位1股
- **A股**: T+1交易，最小单位100股(1手)
- **加密货币**: T+0交易，支持7×24小时交易

### AI代理类型

| 代理类型 | 适用市场 | 交易频率 | 特性 |
|---------|---------|---------|------|
| BaseAgent | 美股 | 日线 | 通用交易代理，可通过market参数切换市场 |
| BaseAgent_Hour | 美股 | 小时线 | 美股小时交易，精细时间控制 |
| BaseAgentAStock | A股 | 日线 | 优化A股交易，内置A股交易规则 |
| BaseAgentAStock_Hour | A股 | 小时线 | A股小时交易(10:30/11:30/14:00/15:00) |
| BaseAgentCrypto | 加密货币 | 日线 | 优化加密货币交易，默认BITWISE10指数池 |

### 配置参数说明

| 参数 | 描述 | 选项 | 默认值 |
|------|------|------|--------|
| agent_type | AI代理类型 | 见上表 | "BaseAgent" |
| market | 市场类型 | "us"(美股)<br>"cn"(A股)<br>"crypto"(加密货币) | "us" |
| max_steps | 最大推理步数 | 正整数 | 30 |
| max_retries | 最大重试次数 | 正整数 | 3 |
| base_delay | 操作延迟(秒) | 浮点数 | 1.0 |
| initial_cash | 初始资金 | 浮点数 | $10,000(美股)<br>¥100,000(A股)<br>50,000 USDT(加密货币) |

## 测试

项目目前没有自动化测试套件。验证系统功能的最佳方式是：

1. 使用历史数据回放功能
2. 检查交易日志和持仓记录
3. 通过Web界面监控实时交易活动
4. 比较不同AI模型的性能指标

## 贡献指南

欢迎提交新的交易策略和AI代理！请遵循以下步骤：

1. 创建新的代理类，继承自BaseAgent
2. 创建对应的配置文件
3. 提供运行说明
4. 提交Pull Request

只要我们能够运行你的策略，我们将在平台上运行一周以上并持续更新战绩！

## 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件

## 更多信息

- **实时交易排行榜**: https://ai4trade.ai
- **交流群组**: 详见[Communication.md](Communication.md)
- **配置指南**: 详见[docs/CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md)