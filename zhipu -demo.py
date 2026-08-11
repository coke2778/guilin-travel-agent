import os
from http.client import responses
from typing import final

from dotenv import  load_dotenv
load_dotenv()
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from tools import tools

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from tenacity import retry,stop_after_attempt,wait_exponential

from openai import OpenAI
import json
import requests
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 初始化客户端
client = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# -------------------- 工具函数 --------------------
def get_weather(city):
    cache = {
        "桂林": {"lat": 25.27, "lon": 110.29},
        "南宁": {"lat": 22.82, "lon": 108.37},
        "柳州": {"lat": 24.32, "lon": 109.41},
        "北京": {"lat": 39.90, "lon": 116.40},
        "上海": {"lat": 31.23, "lon": 121.47}
    }
    if city in cache:
        lat, lon = cache[city]["lat"], cache[city]["lon"]
    else:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=zh&format=json"
        logging.info(f"正在查询{city}的天气...")
        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if data.get("results"):
                lat = data["results"][0]["latitude"]
                lon = data["results"][0]["longitude"]
            else:
                return f"抱歉，无法获取{city}的坐标信息。"
        except:
            return f"抱歉，查询{city}坐标失败。"
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
    logging.info(f"正在查询{city}的天气...")
    try:
        resp = requests.get(weather_url, timeout=5)
        data = resp.json()
        current = data['current_weather']
        temp = current['temperature']
        wind = current['windspeed']
        code = current['weathercode']
        desc = {0:"晴天",1:"多云",2:"多云",3:"多云",51:"小雨",61:"中雨",80:"阵雨"}.get(code, "未知天气")
        return f"{city}当前天气：{desc}，温度{temp}°C，风速{wind}km/h"
    except:
        return f"获取{city}天气信息失败。"

def get_food(city):
    logging.info(f"正在查询{city}的美食...")
    try:
        food_db = {
            "桂林": "螺狮粉1、啤酒鱼、田螺酿",
            "南宁": "老友粉、酸嘢、卷筒粉",
            "柳州": "螺蛳粉、云片糕"
        }
        return food_db.get(city, f"暂无{city}美食推荐")
    except:
        return f"获取{city}美食信息失败。"

def get_travel(city):
    logging.info(f"正在查询{city}的景点...")
    try :
        travel_db = {
            "桂林": "假山公园、人工湖、梦幻迷宫、彩虹桥",
            "南宁": "青秀山、南湖公园",
            "柳州": "龙潭公园、柳侯公园",
            "提瓦特": "风起地、程曦酒庄"
        }
        return travel_db.get(city, f"暂无{city}景点推荐")
    except:
        return f"获取{city}景点信息失败。"

def get_hotel(city):
    logging.info(f"正在查询{city}的酒店...")
    try:
        hotel_db = {
            "桂林": "广西桂林酒店3、广西桂林大酒店2、广西桂林大酒店1",
            "南宁": "广西南宁酒店、广西南宁大酒店、广西南宁大酒店",
            "柳州": "广西柳州酒店、广西柳州大酒店、广西柳州大酒店",
            "提瓦特": "蒙德大酒店、梨月大酒店、到期大酒店"
        }
        return hotel_db.get(city, f"暂无{city}酒店推荐")
    except:
        return f"获取{city}酒店信息失败。"

# -------------------- RAG 模块 --------------------
def load_document(file_path='knowledge.txt', chunk_size=200):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        return []
    sentences = text.split('。')
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) < chunk_size:
            current += s + "。"
        else:
            if current:
                chunks.append(current)
            current = s + "。"
    if current:
        chunks.append(current)
    return chunks

embed_model = None
index = None
chunks = None

def rag_query(query):
    global embed_model, index, chunks

    # 如果还没加载，才加载
    if embed_model is None:
        logging.info("🔍 首次使用RAG，加载模型...")
        embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        chunks = load_document()
        if chunks:
            embeddings = embed_model.encode(chunks, show_progress_bar=False)
            dim = embeddings.shape[1]
            index = faiss.IndexFlatL2(dim)
            index.add(np.array(embeddings).astype('float32'))
        else:
            logging.warning("⚠️ knowledge.txt 未找到，RAG 暂不可用")

    if not chunks or index is None:
        return "知识库未加载。"

    logging.info("正在知识库中查询...")
    query_vec = embed_model.encode([query])
    distances, indices = index.search(np.array(query_vec).astype('float32'), 1)
    docs = [chunks[i] for i in indices[0] if i < len(chunks)]
    if not docs:
        return "未找到相关信息。"
    return "\n".join(docs)

# -------------------- 工具列表 --------------------

# -------------------- 对话历史与主循环 --------------------
if __name__ == '__main__':
    conversation_history = []
    logging.info("🤖 旅游助手已启动（输入 exit 退出）")

    while True:
        user_input = input("\n你：")
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        if user_input.startswith("rag:"):
            query = user_input[4:].strip()
            result = rag_query(query)
            logging.info(f"RAG检索结果: {result}")
            continue

        conversation_history.append({"role": "user", "content": user_input})

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
        def call_model(messages, tools=None, tool_choice="auto"):
            return client.chat.completions.create(
                model="glm-4-flash",
                messages=messages,
                tools=tools,
                tool_choice=tool_choice
            )
        logging.info("正在思考...")
        response = call_model(conversation_history,tools, "auto")
        print(f"长度：{len(conversation_history)}")
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            func_name = tool_call.function.name

            if func_name == "get_weather":
                result = get_weather(args["city"])
            elif func_name == "search_docs":
                result = rag_query(args["query"])
            elif func_name == "get_food":
                result = get_food(args["city"])
            elif func_name == "get_travel":
                result = get_travel(args["city"])
            elif func_name == "get_hotel":
                result = get_hotel(args["city"])
            else:
                result = "未知工具"

            final = call_model(
                messages=[
                    {"role": "user", "content": user_input},
                    response.choices[0].message,
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                ]
            )
            answer = final.choices[0].message.content
        else:
            answer = response.choices[0].message.content

        logging.info(f"AI: {answer}")
        conversation_history.append({"role": "assistant", "content": answer})