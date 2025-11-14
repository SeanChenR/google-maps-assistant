# Google Maps MCP Agent

基於 Google Cloud Vertex AI 的 AI 代理程式，使用 Google ADK (Agent Development Kit) 和 MCP (Model Context Protocol) 提供 Google Maps 功能，包括地點搜尋、路線規劃、地理編碼和附近景點查詢。

## 功能特色

- **地點搜尋**: 使用 Google Maps 搜尋地點和位置
- **路線規劃**: 取得兩地之間的詳細導航指示
- **地理編碼**: 地址與座標之間的相互轉換
- **附近搜尋**: 尋找特定位置附近的興趣點
- **Gemini Enterprise 整合**: 部署至 Google Cloud Gemini Enterprise 取得網頁介面存取
- **串流回應**: 即時的代理程式查詢回應串流

## 架構

本專案整合了多項 Google Cloud 技術:

- **Google ADK**: Agent Development Kit，用於建構 AI 代理程式
- **MCP Protocol**: Model Context Protocol，用於工具整合
- **Vertex AI Agent Engines**: 可擴展的部署平台
- **Google Maps API**: 核心地圖與定位服務
- **Gemini Enterprise**: 網頁式代理程式介面(原 AgentSpace)

```
google-maps-assistant/
├── google_maps_mcp_agent/
│   ├── __init__.py
│   └── agent.py              # 主要代理程式定義
├── installation_scripts/
│   └── install_npx.sh        # Node.js 安裝腳本
├── deploy_agent.py           # 代理程式部署腳本
├── agentspace_manager.py     # Gemini Enterprise 管理 CLI
├── query_agent_engine.py     # 代理程式測試腳本
├── .env.example              # 環境變數範本
├── pyproject.toml            # Python 相依套件
└── README.md                 # 本檔案
```

## 前置需求

- Python 3.12 或更高版本
- 已啟用計費的 Google Cloud 專案
- Google Maps API 金鑰
- Node.js 20.x (部署時會透過內建腳本自動安裝)

## 使用方式

### 部署代理程式

將代理程式部署至 Vertex AI Agent Engines:

```bash
python deploy_agent.py
```

此指令會:
- 在部署環境中安裝 Node.js 20.x
- 打包代理程式和 MCP 工具集
- 部署至 Vertex AI Agent Engines
- 輸出 `AGENT_ENGINE_RESOURCE_NAME`

將回傳的資源名稱更新至 `.env` 檔案:

```bash
AGENT_ENGINE_RESOURCE_NAME=projects/PROJECT_NUMBER/locations/LOCATION/reasoningEngines/RESOURCE_ID
```

### 測試代理程式

透過程式測試已部署在 Agent Engine 的代理程式:

```bash
python query_agent_engine.py
```

### 連結至 Gemini Enterprise

將已部署的代理程式連結至 Gemini Enterprise 以取得網頁介面存取:

```bash
# 連結代理程式
python gemini_enterprise_manager.py link

# 驗證連線
python gemini_enterprise_manager.py verify

# 取得 Gemini Enterprise UI 網址
python gemini_enterprise_manager.py url
```

## 核心元件

### 代理程式定義 (google_maps_mcp_agent/agent.py)

定義 Google Maps 代理程式與 MCP 工具集整合:

```python
root_agent = Agent(
    model="gemini-2.5-flash",
    name="maps_assistant_agent",
    description="Google Maps assistant with MCP toolset",
    tools=[google_maps_tools]
)
```

### 部署腳本 (deploy_agent.py)

處理代理程式部署至 Vertex AI，包含:
- 固定相依套件版本以確保穩定性
- 包含 NPX 安裝腳本
- 環境變數設定
- 可選的測試與刪除功能

### Gemini Enterprise 管理器 (gemini_enterprise_manager.py)

用於管理 Gemini Enterprise 整合的 CLI 工具:
- 連結/取消連結代理程式
- 驗證設定
- 顯示 UI 網址
- 更新環境變數

## 查詢範例

部署完成後，您可以向代理程式提出以下類型的問題:

- "幫我找台北101附近的咖啡廳"
- "台北車站的地址是什麼?"
- "我要拜訪客戶xx公司，我是xx地出發，客戶是在xx地址"

## 設定選項

### Gemini Enterprise 客製化

自訂代理程式外觀:

```bash
AGENT_DISPLAY_NAME=我的自訂地圖代理程式
AGENT_DESCRIPTION=我的代理程式的自訂描述
AGENT_TOOL_DESCRIPTION=自訂工具描述
```
