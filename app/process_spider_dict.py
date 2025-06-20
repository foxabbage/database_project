import json
from typing import Dict, Any

def process_spider_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理爬虫配置字典，转换为指定格式的JSON结构
    
    Args:
        config: 原始配置字典，包含以下键：
            - keyword: 搜索关键词
            - sort: 排序方式(中文)
            - types: 类型列表(中文)
            - tags: 标签列表
            - start_date: 开始日期(YYYY-MM-DD)
            - end_date: 结束日期(YYYY-MM-DD)
            - min_rating: 最小评分
            - max_rating: 最大评分
            - min_rank: 最小排名
            - max_rank: 最大排名
            - limit: 条目上限
    
    Returns:
        处理后的字典，符合指定JSON格式
    """
    # 1. 处理排序方式映射
    sort_mapping = {
        "匹配程度": "match",
        "收藏数": "heat",
        "排名": "rank",
        "评分": "score"
    }
    sort_value = sort_mapping.get(config["sort"], "match")
    
    # 2. 处理类型映射
    type_mapping = {
        "书籍": 1,
        "动画": 2,
        "游戏": 4
    }
    type_values = [type_mapping[t] for t in config["types"] if t in type_mapping]
    
    # 3. 处理日期范围
    date_filters = []
    if config["start_date"]:
        date_filters.append(f">={config['start_date']}")
    if config["end_date"]:
        date_filters.append(f"<={config['end_date']}")
    
    # 4. 处理评分范围
    rating_filters = []
    if "min_rating" in config and config["min_rating"] != 0:
        rating_filters.append(f">={config['min_rating']}")
    if "max_rating" in config and config["max_rating"] != 10:
        rating_filters.append(f"<={config['max_rating']}")
    
    # 5. 处理排名范围
    rank_filters = []
    if "min_rank" in config and config["min_rank"] != 1:
        rank_filters.append(f">={config['min_rank']}")
    if "max_rank" in config and config["max_rank"] is not None:
        rank_filters.append(f"<={config['max_rank']}")
    
    # 构建最终结果字典
    result = {
        "keyword": config["keyword"],
        "sort": sort_value,
        "filter": {
            "type": type_values,
            "tag": config["tags"],
            "air_date": date_filters,
            "rating": rating_filters,
            "rank": rank_filters
        }
    }
    
    # 移除空值或空列表的过滤条件
    result["filter"] = {k: v for k, v in result["filter"].items() if v}
    
    print(result)
    return result

def save_config_to_json(config: Dict[str, Any], filename: str = "spider_config.json"):
    """
    将处理后的配置保存为JSON文件
    
    Args:
        config: 处理后的配置字典
        filename: 要保存的文件名
    """
    processed_config = process_spider_config(config)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(processed_config, f, ensure_ascii=False, indent=2)
    
    print(f"配置已保存到 {filename}")