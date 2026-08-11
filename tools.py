tools = [{
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": "搜索桂林旅游知识库，适用于景点详情、历史文化、交通住宿等开放性问题",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }
},
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询实时天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_food",
            "description": "推荐当地美食",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_travel",
            "description": "推荐旅游景点",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        }
    },
{
    "type": "function",
    "function": {
        "name": "get_hotel",
        "description": "查询指定城市的酒店推荐。当用户询问任何关于住宿、酒店、旅馆的问题时，必须调用此函数。不要自行编造酒店信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "需要查询酒店的城市名"}
            },
            "required": ["city"]
        }
    }
}
]