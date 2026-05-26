"""
洛克王国世界 · 远行商人数据抓取器
从好游快爆(onebiji.com)远行商人工具页面抓取实时数据
URL: onebiji.com/hykb_tools/comm/lkwgmerchant/preview.php?id=1
数据直接嵌入HTML，按 show_1/2/3/4 分轮次
"""
import requests
import re
import json
import os
# 禁用 SSL 警告（onebiji CDN 可能使用自签名证书）
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, timezone, timedelta

BEIJING_TZ = timezone(timedelta(hours=8))
SOURCE_URL = "https://www.onebiji.com/hykb_tools/comm/lkwgmerchant/preview.php?id=1&immgj=0"
OUTPUT_FILE = "data/merchant.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

ROUND_TIMES = {
    1: {"start": 8, "end": 12, "label": "08:00-12:00"},
    2: {"start": 12, "end": 16, "label": "12:00-16:00"},
    3: {"start": 16, "end": 20, "label": "16:00-20:00"},
    4: {"start": 20, "end": 24, "label": "20:00-24:00"},
}


def get_current_round():
    """根据当前北京时间返回活动轮次(None=非营业时间)"""
    now = datetime.now(BEIJING_TZ)
    hour = now.hour
    if hour < 8:
        return None
    for rnd, info in ROUND_TIMES.items():
        if info["start"] <= hour < info["end"]:
            return rnd
    return None


def fetch_page():
    """获取页面，支持重试"""
    import time as _time
    last_error = None
    for attempt in range(3):
        try:
            session = requests.Session()
            # 禁用 SSL 验证以兼容某些 CDN 环境
            resp = session.get(SOURCE_URL, headers=HEADERS, timeout=30, verify=False)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            return resp.text
        except Exception as e:
            last_error = e
            print(f"  [重试 {attempt+1}/3] 请求失败: {e}")
            if attempt < 2:
                _time.sleep(5)
    raise last_error


def parse_items_from_html(html):
    """
    从HTML中解析所有商品。
    每个<li>包含一个商品，class show_1/2/3/4 表示所属轮次。
    onclick="showShopinfo(...)" 包含: 图片, 名称, 类型, 描述
    """
    items = []

    # 匹配每个 <li> 块（包含完整的开标签以便提取 onclick 属性）
    li_pattern = re.compile(
        r'(<li\s+class="[^"]*\bshow_(\d)\b[^"]*"[^>]*>)'
        r'(.*?)'
        r'</li>',
        re.DOTALL
    )

    for match in li_pattern.finditer(html):
        li_tag = match.group(1)       # 完整的 <li ...> 开标签
        round_num = int(match.group(2))
        li_content = match.group(3)   # li 内部内容

        # 跳过空数据提示
        if 'show_none_tip' in li_content:
            continue

        # 提取 onclick="showShopinfo(...)" 的参数（在 li 开标签中）
        onclick_match = re.search(r"showShopinfo\('([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\)", li_tag)
        if onclick_match:
            image = onclick_match.group(1)
            name = onclick_match.group(2)
            category = onclick_match.group(3)
            description = onclick_match.group(4)
        else:
            # 回退：从HTML标签中提取
            name_match = re.search(r'<em\s+class="shop_name">([^<]+)</em>', li_content)
            name = name_match.group(1).strip() if name_match else None

            img_match = re.search(r'<img\s+src="([^"]+)"', li_content)
            image = img_match.group(1) if img_match else None

            category = ""
            description = ""

        if not name:
            continue

        # 修复图片URL
        if image:
            if image.startswith('//'):
                image = 'https:' + image

        # 提取价格
        price_match = re.search(r'<em\s+class="shop_price">([^<]+)</em>', li_content)
        price_raw = price_match.group(1).strip() if price_match else "?"
        # 清理价格文本
        price = re.sub(r'价格[：:]\s*', '', price_raw)

        # 提取限购
        limit_match = re.search(r'<em>限购(\d+)</em>', li_content)
        limit = limit_match.group(1) if limit_match else "?"

        # 提取 data-time
        time_match = re.search(r'data-time="(\d+)"', match.group(0))
        item_time = int(time_match.group(1)) if time_match else None

        items.append({
            "round": round_num,
            "name": name,
            "price": price,
            "limit": limit,
            "image": image,
            "category": category,
            "description": description,
            "timestamp": item_time,
        })

    return items


def group_by_round(items):
    """将商品按轮次分组"""
    rounds = {"1": [], "2": [], "3": [], "4": []}
    for item in items:
        rnd = str(item.get("round", 1))
        if rnd in rounds:
            # 去掉内部字段
            clean = {k: v for k, v in item.items() if k != "round"}
            rounds[rnd].append(clean)
    return rounds


def main():
    now_beijing = datetime.now(BEIJING_TZ)
    print(f"[{now_beijing.strftime('%Y-%m-%d %H:%M:%S')}] 开始抓取...")
    print(f"数据源: 好游快爆远行商人工具")

    current_round = get_current_round()
    status = "open" if current_round else "closed"

    if current_round:
        round_info = ROUND_TIMES[current_round]
        print(f"北京时间: {now_beijing.strftime('%H:%M')} | 营业中 | 当前第{current_round}轮 ({round_info['label']})")
    else:
        print(f"北京时间: {now_beijing.strftime('%H:%M')} | 非营业时间 (0:00-8:00)")

    try:
        html = fetch_page()
        print(f"页面获取成功: {len(html)} 字符")

        items = parse_items_from_html(html)
        print(f"解析到 {len(items)} 件商品:")

        rounds_data = group_by_round(items)

        for rnd in ["1", "2", "3", "4"]:
            rd_items = rounds_data[rnd]
            marker = ">>" if str(current_round) == rnd else "  "
            if rd_items:
                names = ", ".join(i["name"] for i in rd_items)
                rt = ROUND_TIMES[int(rnd)]
                print(f"  {marker} 第{rnd}轮 [{rt['label']}] ({len(rd_items)}件): {names}")
            else:
                print(f"  {marker} 第{rnd}轮: (无数据)")

        if current_round:
            current_items = rounds_data.get(str(current_round), [])
        else:
            current_items = []

        # 计算下次刷新时间
        round_start_hours = {1: 8, 2: 12, 3: 16, 4: 20, 5: 8}
        if current_round:
            next_round_hour = round_start_hours[current_round + 1]
        else:
            next_round_hour = 8

        if next_round_hour == 8 and current_round != 3:
            next_refresh = now_beijing.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:
            next_refresh = now_beijing.replace(hour=next_round_hour, minute=0, second=0, microsecond=0)

        result = {
            "sourceUrl": SOURCE_URL,
            "sourceName": "好游快爆远行商人工具",
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "timezone": "Asia/Shanghai",
            "status": status,
            "round": current_round,
            "roundLabel": ROUND_TIMES[current_round]["label"] if current_round else "休市中",
            "nextRefreshBeijing": next_refresh.strftime("%Y-%m-%d %H:%M:%S"),
            "rounds": rounds_data,
            "items": current_items,
        }

        os.makedirs(os.path.dirname(OUTPUT_FILE) if os.path.dirname(OUTPUT_FILE) else "data", exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n已保存 {OUTPUT_FILE}")
        print(f"当前: {'第' + str(current_round) + '轮' if current_round else '休市'} | {len(current_items)} 件商品")

    except Exception as e:
        print(f"抓取失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
