# Semantic Kernel HandoffOrchestration 多模態檔案上傳範例

這是一個基於 Microsoft Semantic Kernel 的 Multi-Agent 協調系統，展示如何使用 `HandoffOrchestration` 實現智能化的 Agent 轉移，並支援圖片、JSON、CSV 等多種檔案類型的上傳與分析。

## 📋 專案簡介

本專案實作了一個客戶服務場景的 Multi-Agent 系統，包含：

- **Multi-Agent 協調**：根據任務類型自動路由到專業 Agent
- **檔案上傳支援**：支援圖片、JSON、CSV 等多種檔案格式
- **視覺分析**：使用 Azure OpenAI Vision 功能分析架構圖和圖片
- **智能轉移**：基於 `HandoffOrchestration` 的自動 Agent 切換

## 🏗️ 專案結構

```text
sk-handoffOrchestration/
├── handoffOrchestration_uploadFile.py  # 主程式：Multi-Agent 協調與檔案上傳實作
├── pyproject.toml                      # 專案配置與依賴管理
├── uv.lock                             # UV 套件管理器鎖定檔案
├── architecture.png                    # 測試用 Azure 架構圖範例
├── sample_data.json                    # 測試用 JSON 配置檔案
├── sample_orders.csv                   # 測試用訂單 CSV 資料
├── .venv/                              # Python 虛擬環境（自動生成）
└── README.md                           # 專案說明文件
```

## 🤖 Agent 架構

### Agent 類型

1. **`SupportAgent`（支援 Agent）**
   - 角色：初始客戶請求處理器
   - 功能：接收用戶請求並路由到專業 Agent

2. **`RefundAgent`（退款 Agent）**
   - 角色：退款請求處理專家
   - 功能：處理退款查詢和相關問題

3. **`OrderStatusAgent`（訂單狀態 Agent）**
   - 角色：訂單狀態查詢專家
   - 功能：檢查和回報訂單狀態

4. **`ImageAnalysisAgent`（圖片分析 Agent）**
   - 角色：視覺內容分析專家
   - 功能：分析圖片、架構圖、流程圖等視覺內容

5. **`FileAnalysisAgent`（檔案分析 Agent）**
   - 角色：檔案內容分析專家
   - 功能：分析 JSON、CSV、文字檔等結構化資料

### Handoff 規則

```text
SupportAgent → RefundAgent (退款相關)
SupportAgent → OrderStatusAgent (訂單狀態相關)
SupportAgent → ImageAnalysisAgent (圖片分析)
SupportAgent → FileAnalysisAgent (檔案分析)

RefundAgent → SupportAgent (非退款問題)
ImageAnalysisAgent → SupportAgent (分析完成)
FileAnalysisAgent → SupportAgent (分析完成)
```

## 🚀 快速開始

### 環境需求

- Python 3.10 或更高版本
- UV 套件管理器
- Azure OpenAI API 金鑰

### 安裝步驟

1. **複製專案**
   ```bash
   cd sk-handoffOrchestration
   ```

2. **配置環境變數**

   複製 `.env.example` 並建立 `.env` 檔案：
   ```bash
   cp .env.example .env
   ```

   編輯 `.env` 檔案，填入您的 Azure OpenAI 設定：
   ```bash
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_DEPLOYMENT=gpt-5
   ```

   ⚠️ **安全性提醒**：請勿將 `.env` 檔案提交至版本控制系統！

3. **使用 UV 安裝依賴**
   ```bash
   uv sync --link-mode=copy
   ```

4. **執行程式**
   ```bash
   uv run python handoffOrchestration_uploadFile.py
   ```

## 💡 使用範例

### 範例 1：文字查詢

```python
contract_task = "A customer wants to know about their refund status."
orchestration_result = await handoff_orchestration.invoke(
    task=contract_task,
    runtime=runtime,
)
```

### 範例 2：圖片分析

```python
image_task = load_image_for_analysis("architecture.png")
image_result = await handoff_orchestration.invoke(
    task=image_task,
    runtime=runtime,
)
```

### 範例 3：JSON 檔案分析

```python
json_task = load_file_for_analysis(
    "sample_data.json",
    "Please analyze this JSON configuration file."
)
json_result = await handoff_orchestration.invoke(
    task=json_task,
    runtime=runtime,
)
```

### 範例 4：CSV 資料分析

```python
csv_task = load_file_for_analysis(
    "sample_orders.csv",
    "Please analyze this CSV order data."
)
csv_result = await handoff_orchestration.invoke(
    task=csv_task,
    runtime=runtime,
)
```

## 📁 檔案上傳功能

### 支援的檔案類型

| 檔案類型 | MIME Type | 處理方式 |
|---------|-----------|---------|
| 圖片 | image/* | `ImageContent` - 視覺分析 |
| JSON | application/json | 文字嵌入 - 結構化分析 |
| CSV | text/csv | 文字嵌入 - 表格資料分析 |
| 文字檔 | text/plain | 文字嵌入 - 內容分析 |
| Markdown | text/markdown | 文字嵌入 - 文件分析 |

### 檔案載入函數

#### `load_image_for_analysis(image_path: str)`

載入圖片檔案（本地或 URI）並建立 `ChatMessageContent`。

**參數：**

- `image_path`: 圖片檔案路徑或 URL

**回傳：**

- `ChatMessageContent` 包含圖片和提示文字

#### `load_file_for_analysis(file_path: str, description: str = None)`

載入各種文字檔案並建立 `ChatMessageContent`。

**參數：**

- `file_path`: 檔案路徑
- `description`: 可選的檔案描述

**回傳：**

- `ChatMessageContent` 包含檔案內容和提示文字

## 🔧 技術堆疊

- **[Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/)** - Microsoft 的 AI 編排框架
- **[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)** - GPT-4 與 Vision 功能
- **[Python 3.10+](https://www.python.org/)** - 程式語言
- **[UV](https://github.com/astral-sh/uv)** - 快速的 Python 套件管理器
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** - 環境變數管理

## 📦 主要依賴

```toml
[project]
dependencies = [
    "semantic-kernel>=1.14.0",
    "python-dotenv>=1.0.0",
]
```

## 🎯 核心概念

### `HandoffOrchestration`

`HandoffOrchestration` 是 Semantic Kernel 中的 Multi-Agent 協調機制，允許：

- 定義 Agent 之間的轉移規則
- 基於上下文自動路由任務
- 支援複雜的對話流程

### `ChatMessageContent`

統一的訊息內容格式，支援：

- 文字內容 (`TextContent`)
- 圖片內容 (`ImageContent`)
- 多模態組合 (`items` 列表)

### `InProcessRuntime`

本地運行時環境，管理：

- Agent 生命週期
- 訊息傳遞
- 執行狀態

## 🔍 執行結果範例

```text
================================================================================
範例 1: 客戶退款查詢
================================================================================
SupportAgent: [轉交到 RefundAgent]
RefundAgent: [提供退款查詢流程和所需資訊]

最終結果: Task is completed with summary: [完成狀態]
================================================================================
範例 2: 架構圖分析
================================================================================
SupportAgent: [轉交到 ImageAnalysisAgent]
ImageAnalysisAgent: [詳細分析 Azure 架構圖...]

圖片分析結果: [架構圖詳細描述]
```

## 🛠️ 開發說明

### 新增自訂 Agent

1. 定義新的 Agent：

   ```python
   custom_agent = ChatCompletionAgent(
       kernel=kernel,
       name="CustomAgent",
       instructions="Your agent instructions here.",
   )
   ```

2. 加入 Agent 列表：

   ```python
   tool_agent = [..., custom_agent]
   ```

3. 設定 Handoff 規則：

   ```python
   handoffs = (
       OrchestrationHandoffs()
       .add(
           source_agent=support_agent.name,
           target_agent=custom_agent.name,
           description="Transfer condition"
       )
   )
   ```

### 擴展檔案類型支援

在 `load_file_for_analysis()` 函數中新增 MIME 類型處理：

```python
if mime_type == 'your/mime-type':
    # 自訂處理邏輯
    pass
```

## 📝 注意事項

1. **API 金鑰安全**：請勿將 API 金鑰提交到版本控制系統
2. **檔案大小限制**：大型檔案會自動截斷至 10,000 字元
3. **OneDrive 同步**：建議使用 `--link-mode=copy` 避免硬連結問題
4. **Token 限制**：注意 Azure OpenAI 的 Token 使用量

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

本專案僅供學習和參考使用。

## 📚 相關資源

- [Semantic Kernel 官方文件](https://learn.microsoft.com/en-us/semantic-kernel/)
- [Azure OpenAI 服務](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [HandoffOrchestration 指南](https://learn.microsoft.com/en-us/semantic-kernel/agents/)
- [UV 套件管理器](https://docs.astral.sh/uv/)

## 📧 聯絡資訊

如有問題或建議，請透過 Issue 回報。

---

**版本：** 0.1.0  
**最後更新：** 2025-11-22
