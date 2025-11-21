
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header
from icalendar import Calendar
from datetime import date, datetime
import pytz

# ==================== ⚙️ 配置中心 ====================
# 【1. 邮件发送配置】
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")     # 也就是你的机器人QQ
SENDER_PASS = os.environ.get("SENDER_PASS")       # 你的授权码
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL") # 你的收件人

# 【2. 数据源配置】
ICS_URL = os.environ.get("ICS_URL")               # 日历链接
OWM_API_KEY = os.environ.get("OWM_API_KEY")       # 天气Key
# 你的位置 (香港)
LAT = "22.3193"
LON = "114.1694"
CITY_NAME = "Hong Kong"

# ==================== 🛠️ 核心逻辑层 ====================

def calculate_clothing(temp):
    """根据温度计算穿衣建议"""
    if temp >= 30:
        return "🥵 酷热：建议穿短裤短袖，注意防暑降温。"
    elif temp >= 25:
        return "👕 暖和：建议穿短袖T恤，透气舒适为主。"
    elif temp >= 20:
        return "👔 舒适：单层薄衫、长袖T恤或衬衫。"
    elif temp >= 15:
        return "🧥 稍凉：建议穿风衣、休闲夹克或薄毛衣。"
    elif temp >= 10:
        return "🧶 天冷：毛衣加外套，或者穿厚一点的风衣。"
    elif temp >= 5:
        return "🧣 寒冷：羽绒服、厚毛衣、围巾走起。"
    else:
        return "🥶 严寒：把最厚的衣服都穿上，注意保暖！"

def get_weather():
    """获取天气数据，返回字典"""
    print("🌤️ 正在查询天气...")
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric&lang=zh_cn"
    try:
        res = requests.get(url, timeout=10).json()
        
        # 提取数据
        current_temp = int(res['main']['temp'])
        high_temp = int(res['main']['temp_max'])
        low_temp = int(res['main']['temp_min'])
        
        # 生成穿衣建议
        clothing_advice = calculate_clothing(current_temp)

        # 获取 OWM 的图标代码 (例如 "01d")
        # 获取 OWM 的图标代码 (例如 "01d")
        icon_code = res['weather'][0]['icon']
        icon_url = f"https://raw.githubusercontent.com/jinwh5/ScheduledEmail-Tasks/main/weather-icons/{icon_code}.png"
        
        return {
            "temp": current_temp,
            "high": high_temp,
            "low": low_temp,
            "desc": res['weather'][0]['description'],
            ##"icon": f"https://openweathermap.org/img/wn/{res['weather'][0]['icon']}@2x.png",
            # "icon": icon_url,
            "icon": f"https://raw.githubusercontent.com/yuvraaaj/openweathermap-weather-icons/master/icons/{res['weather'][0]['icon']}.png",
            "humidity": res['main']['humidity'],
            "advice": clothing_advice  # 新增的字段
        }
    except Exception as e:
        print(f"天气获取失败: {e}")
        return None

def get_calendar():
    """
    万能适配版：支持 Google/iCloud 日历
    自动将 UTC 时间转换为 'Asia/Shanghai'
    """
    print("📅 正在解析日历 (Google/Apple通用版)...")
    events = []
    
    # 定义你的本地时区
    local_tz = pytz.timezone('Asia/Shanghai')
    
    try:
        res = requests.get(ICS_URL, timeout=15)
        res.raise_for_status() # 检查 404 等错误
        cal = Calendar.from_ical(res.content)
        
        # 获取脚本运行时的“今天”
        today = datetime.now(local_tz).date()
        
        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get('summary'))
                dtstart = component.get('dtstart').dt
                
                # --- 时区标准化处理 ---
                if isinstance(dtstart, datetime):
                    # 1. 如果是 datetime 对象 (非全天)
                    if dtstart.tzinfo is None:
                        # 如果是 naive (无时区)，假设它是本地时间
                        start_local = local_tz.localize(dtstart)
                    else:
                        # 如果是 aware (有时区，比如 Google 的 UTC)，转为本地时间
                        start_local = dtstart.astimezone(local_tz)
                    
                    check_date = start_local.date()
                    time_str = start_local.strftime("%H:%M")
                    
                elif isinstance(dtstart, date):
                    # 2. 如果是 date 对象 (全天事件)
                    check_date = dtstart
                    time_str = "全天"
                
                # --- 匹配今天 ---
                if check_date == today:
                    events.append({"time": time_str, "title": summary})
        
        # 按时间排序
        events.sort(key=lambda x: x['time'])
        return events

    except Exception as e:
        print(f"日历获取失败: {e}")
        # 返回一个空列表，避免程序崩溃
        return []

def get_quote():
    """(可选) 获取每日一句，这里先写死，你可以接金山词霸API"""
    return "Talk is cheap. Show me the code."

# ==================== 🎨 UI 渲染层 ====================

def render_html(weather, events, quote):
    """
    这里是网页设计的核心。
    使用了内联 CSS 以确保兼容性。
    风格：Apple iOS Card Style
    """
    today_date = datetime.now().strftime("%m月%d日 %A")
    
    # 1. 构建行程列表的 HTML
    if not events:
        events_html = """
        <div style="text-align: center; padding: 20px; color: #8e8e93;">
            ☕️ 今天没有安排，享受自由时光吧！
        </div>
        """
    else:
        list_items = ""
        for evt in events:
            # 给列表项加一点样式
            list_items += f"""
            <div style="padding: 12px 0; border-bottom: 1px solid #f2f2f7; display: flex; align-items: center;">
                <span style="background-color: #e5f1fb; color: #007aff; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; margin-right: 12px; min-width: 45px; text-align: center;">
                    {evt['time']}
                </span>
                <span style="color: #1c1c1e; font-size: 16px;">{evt['title']}</span>
            </div>
            """
        events_html = list_items

    # 2. 处理天气显示
    if weather:
        weather_html = f"""
        <div style="display: flex; align-items: flex-start; justify-content: space-between;">
            <div>
                <div style="font-size: 42px; font-weight: 800; color: #1c1c1e; line-height: 1;">
                    {weather['temp']}°
                </div>
                
                <div style="margin-top: 6px; font-size: 15px; color: #3a3a3c; font-weight: 500;">
                    <span style="color: #ff3b30;">H:{weather['high']}°</span> 
                    <span style="color: #d1d1d6; margin: 0 4px;">/</span>
                    <span style="color: #007aff;">L:{weather['low']}°</span>
                    <span style="margin-left: 8px; color: #8e8e93;">{weather['desc']}</span>
                </div>

                <div style="font-size: 13px; color: #8e8e93; margin-top: 4px;">
                    相对湿度: {weather['humidity']}%
                </div>
            </div>
            <img src="{weather['icon']}" style="width: 70px; height: 70px;">
        </div>
        
        <div style="margin-top: 15px; padding: 12px; background-color: #f2f2f7; border-radius: 10px; font-size: 13px; color: #3a3a3c; border-left: 4px solid #34c759;">
            <b>👕 穿衣助手：</b>{weather['advice']}
        </div>
        """
    else:
        weather_html = "<div>天气数据暂时不可用</div>"

    # 3. 组装整体 HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f2f2f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        
        <div style="max-width: 400px; margin: 0 auto; padding: 20px;">
            
            <div style="margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 28px; color: #000;">早安，Alex</h1>
                <p style="margin: 5px 0 0 0; color: #8e8e93; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">{today_date}</p>
            </div>

            <div style="background: #ffffff; border-radius: 18px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                <div style="font-size: 12px; color: #8e8e93; margin-bottom: 10px; font-weight: 600;">📍 {CITY_NAME}</div>
                {weather_html}
            </div>

            <div style="background: #ffffff; border-radius: 18px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                <div style="font-size: 12px; color: #8e8e93; margin-bottom: 15px; font-weight: 600; text-transform: uppercase;">TODAY'S SCHEDULE</div>
                {events_html}
            </div>

            <div style="background: #ffffff; border-radius: 18px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                 <div style="font-size: 12px; color: #8e8e93; margin-bottom: 5px; font-weight: 600;">DAILY QUOTE</div>
                 <div style="font-style: italic; color: #3a3a3c; line-height: 1.5;">“{quote}”</div>
            </div>

            <div style="text-align: center; margin-top: 30px; color: #c7c7cc; font-size: 12px;">
                Python Personal Assistant • 自动化部署
            </div>

        </div>
    </body>
    </html>
    """
    return html

# ==================== 🚀 发送执行层 ====================

def main():
    # 1. 获取数据
    weather_data = get_weather()
    calendar_data = get_calendar()
    quote_data = get_quote()
    
    # 2. 生成漂亮的 HTML
    email_content = render_html(weather_data, calendar_data, quote_data)
    
    # 3. 构建邮件
    msg = MIMEText(email_content, 'html', 'utf-8')
    msg['From'] = formataddr(["Alex's Bot", SENDER_EMAIL])
    msg['To'] = formataddr(["Alex", RECEIVER_EMAIL])
    msg['Subject'] = f"🌞 早安日报 - {date.today().strftime('%m.%d')}"
    
    # 4. 发送
    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        server.quit()
        print("✅ 邮件已发送！快去看手机！")
    except Exception as e:
        print(f"❌ 发送挂了: {e}")

if __name__ == "__main__":
    main()