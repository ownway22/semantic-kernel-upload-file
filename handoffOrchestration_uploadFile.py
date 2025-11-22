# --- Standard Library Imports ---
import os
import asyncio
from dotenv import load_dotenv

# --- Semantic Kernel Agent Framework Imports ---
from semantic_kernel.agents import (
    HandoffOrchestration, 
    OrchestrationHandoffs,
    ChatCompletionAgent
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole, ImageContent, TextContent
from semantic_kernel import Kernel

# 載入環境變數
load_dotenv()

# 設定 Azure OpenAI 服務
kernel = Kernel()
service_id = "agent-service"
chat_service = AzureChatCompletion(
    service_id=service_id,
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5"),
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY", "your-api-key-here"),
)
kernel.add_service(chat_service)

# 定義專門的 agents
support_agent = ChatCompletionAgent(
    kernel=kernel,
    name="SupportAgent",
    instructions="You are a customer support agent. Handle initial customer requests and route to specialists.",
)

refund_agent = ChatCompletionAgent(
    kernel=kernel,
    name="RefundAgent",
    instructions="You handle refund requests.",
)

order_status_agent = ChatCompletionAgent(
    kernel=kernel,
    name="OrderStatusAgent",
    instructions="You check order status.",
)

# 定義圖片分析 agent (支援 Vision/多模態)
image_analysis_agent = ChatCompletionAgent(
    kernel=kernel,
    name="ImageAnalysisAgent",
    instructions="You are an expert at analyzing images and architecture diagrams. Provide detailed descriptions of what you see in images, including structure, components, and relationships.",
)

# 定義檔案分析 agent (處理各種檔案類型)
file_analysis_agent = ChatCompletionAgent(
    kernel=kernel,
    name="FileAnalysisAgent",
    instructions="You are an expert at analyzing various file types including JSON, CSV, text files, and documents. Provide insights, summaries, and identify key information from the file content.",
)

# 定義工具 agents 列表
tool_agent = [support_agent, refund_agent, order_status_agent, image_analysis_agent, file_analysis_agent]

# 定義 handoff 關係 (agents 之間的轉移規則)
handoffs = (
    OrchestrationHandoffs()
    .add_many(
        source_agent=support_agent.name,
        target_agents={
            refund_agent.name: "Transfer to this agent if the issue is refund related",
            order_status_agent.name: "Transfer to this agent if the issue is order status related",
            image_analysis_agent.name: "Transfer to this agent if the user provides an image or asks to analyze architecture/diagrams",
            file_analysis_agent.name: "Transfer to this agent if the user provides a file (JSON, CSV, text) or asks to analyze file content",
        },
    )
    .add(
        source_agent=refund_agent.name,
        target_agent=support_agent.name,
        description="Transfer to this agent if the issue is not refund related",
    )
    .add(
        source_agent=image_analysis_agent.name,
        target_agent=support_agent.name,
        description="Transfer back to support agent after image analysis is complete",
    )
    .add(
        source_agent=file_analysis_agent.name,
        target_agent=support_agent.name,
        description="Transfer back to support agent after file analysis is complete",
    )
)

# 定義回調函數 (可選)
def agent_response_callback(message: ChatMessageContent) -> None:
    """Agent 回應時的回調函數"""
    print(f"{message.name}: {message.content}")

def human_response_function() -> ChatMessageContent:
    """需要人類輸入時的回調函數"""
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)

def load_image_for_analysis(image_path: str) -> ChatMessageContent:
    """
    載入圖片並建立包含圖片的 ChatMessageContent
    
    Args:
        image_path: 圖片檔案路徑 (本地或 URI)
    
    Returns:
        包含圖片和提示文字的 ChatMessageContent
    """
    # 檢查是否為 URI (http/https)
    if image_path.startswith(('http://', 'https://')):
        # 使用 URI 方式載入圖片
        return ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="Please analyze this architecture diagram and provide a detailed description."),
                ImageContent(uri=image_path),
            ]
        )
    else:
        # 從本地檔案載入圖片
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        return ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="Please analyze this architecture diagram and provide a detailed description."),
                ImageContent.from_image_file(path=image_path),
            ]
        )


def load_file_for_analysis(file_path: str, description: str = None) -> ChatMessageContent:
    """
    載入各種類型的檔案並建立 ChatMessageContent
    支援文字檔、JSON、CSV 等格式
    
    Args:
        file_path: 檔案路徑 (本地)
        description: 檔案描述 (可選)
    
    Returns:
        包含檔案內容和提示文字的 ChatMessageContent
    """
    import mimetypes
    
    # 檢查檔案是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # 取得 MIME 類型
    mime_type, _ = mimetypes.guess_type(file_path)
    
    prompt = description or f"Please analyze this file: {os.path.basename(file_path)}"
    
    # 根據檔案類型處理
    if mime_type in ['text/plain', 'text/csv', 'application/json', 'text/markdown']:
        # 文字檔案 - 直接讀取內容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 限制內容長度以避免超過 token 限制
            max_length = 10000
            if len(content) > max_length:
                content = content[:max_length] + f"\n\n[Content truncated, total length: {len(content)} characters]"
            
            return ChatMessageContent(
                role=AuthorRole.USER,
                content=f"{prompt}\n\nFile content:\n```\n{content}\n```"
            )
        except Exception as e:
            return ChatMessageContent(
                role=AuthorRole.USER,
                content=f"{prompt}\n\n[Error reading file: {str(e)}]"
            )
    else:
        # 其他檔案類型 (PDF 等) - 提供檔案資訊
        file_size = os.path.getsize(file_path)
        return ChatMessageContent(
            role=AuthorRole.USER,
            content=f"{prompt}\n\n[File: {os.path.basename(file_path)}, Type: {mime_type or 'unknown'}, Size: {file_size} bytes]\n\nNote: This file type requires specialized processing. For PDF files, consider using Azure Document Intelligence or similar services."
        )


async def main():
    # 範例 1: 文字任務
    print("=" * 80)
    print("範例 1: 客戶退款查詢")
    print("=" * 80)
    
    contract_task = "A customer wants to know about their refund status."
    
    # 建立並啟動運行時
    runtime = InProcessRuntime()
    runtime.start()
    
    # 建立 handoff orchestration
    handoff_orchestration = HandoffOrchestration(
        members=tool_agent,
        handoffs=handoffs,
        agent_response_callback=agent_response_callback,
        # human_response_function=human_response_function  # 如需人工介入,取消註解
    )
    
    # 執行 orchestration
    orchestration_result = await handoff_orchestration.invoke(
        task=contract_task,
        runtime=runtime,
    )
    
    # 取得結果
    value = await orchestration_result.get()
    print(f"\n最終結果: {value}")
    
    # 範例 2: 圖片分析任務
    print("\n" + "=" * 80)
    print("範例 2: 架構圖分析")
    print("=" * 80)
    
    # 指定圖片路徑 - 使用當前目錄的 architecture.png
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "architecture.png")
    
    if os.path.exists(image_path):
        try:
            # 載入圖片並建立分析任務
            image_task = load_image_for_analysis(image_path)
            
            # 執行圖片分析 orchestration
            image_result = await handoff_orchestration.invoke(
                task=image_task,
                runtime=runtime,
            )
            
            # 取得分析結果
            analysis_value = await image_result.get()
            print(f"\n圖片分析結果: {analysis_value}")
            
        except Exception as e:
            print(f"\n處理圖片時發生錯誤: {e}")
    else:
        print(f"圖片檔案不存在: {image_path}")
    
    # 範例 3: JSON 檔案分析任務
    print("\n" + "=" * 80)
    print("範例 3: JSON 檔案分析")
    print("=" * 80)
    
    json_file_path = os.path.join(current_dir, "sample_data.json")
    
    if os.path.exists(json_file_path):
        try:
            # 載入 JSON 檔案並建立分析任務
            json_task = load_file_for_analysis(
                json_file_path,
                "Please analyze this JSON configuration file and summarize its contents."
            )
            
            # 執行檔案分析 orchestration
            json_result = await handoff_orchestration.invoke(
                task=json_task,
                runtime=runtime,
            )
            
            # 取得分析結果
            json_value = await json_result.get()
            print(f"\nJSON 分析結果: {json_value}")
            
        except Exception as e:
            print(f"\n處理 JSON 檔案時發生錯誤: {e}")
    else:
        print(f"JSON 檔案不存在: {json_file_path}")
    
    # 範例 4: CSV 檔案分析任務
    print("\n" + "=" * 80)
    print("範例 4: CSV 檔案分析")
    print("=" * 80)
    
    csv_file_path = os.path.join(current_dir, "sample_orders.csv")
    
    if os.path.exists(csv_file_path):
        try:
            # 載入 CSV 檔案並建立分析任務
            csv_task = load_file_for_analysis(
                csv_file_path,
                "Please analyze this CSV order data and provide insights about the orders."
            )
            
            # 執行檔案分析 orchestration
            csv_result = await handoff_orchestration.invoke(
                task=csv_task,
                runtime=runtime,
            )
            
            # 取得分析結果
            csv_value = await csv_result.get()
            print(f"\nCSV 分析結果: {csv_value}")
            
        except Exception as e:
            print(f"\n處理 CSV 檔案時發生錯誤: {e}")
    else:
        print(f"CSV 檔案不存在: {csv_file_path}")
    
    # 停止 runtime
    await runtime.stop_when_idle()

# 執行主程式
if __name__ == "__main__":
    asyncio.run(main())