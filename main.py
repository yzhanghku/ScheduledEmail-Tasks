
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

def get_weather():
    """获取天气数据，返回字典"""
    print("🌤️ 正在查询天气...")
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric&lang=zh_cn"
    try:
        res = requests.get(url, timeout=10).json()
        return {
            "temp": int(res['main']['temp']),
            "desc": res['weather'][0]['description'],
            "icon": f"http://openweathermap.org/img/wn/{res['weather'][0]['icon']}@2x.png",
            "high": int(res['main']['temp_max']),
            "low": int(res['main']['temp_min']),
            "humidity": res['main']['humidity']
        }
    except Exception as e:
        print(f"天气获取失败: {e}")
        return None

def get_calendar():
    """获取今日行程，返回列表 [{'time': '10:00', 'title': '开会'}, ...]"""
    print("📅 正在解析日历...")
    events = []
    try:
        res = requests.get(ICS_URL, timeout=15)
        cal = Calendar.from_ical(res.content)
        today = date.today()
        
        for component in cal.walk():
            if component.name == "VEVENT":
                start = component.get('dtstart').dt
                summary = str(component.get('summary'))
                
                # 简单的日期过滤
                if isinstance(start, datetime):
                    check_date = start.date()
                    time_str = start.strftime("%H:%M")
                else:
                    check_date = start
                    time_str = "全天" # All day event
                
                if check_date == today:
                    events.append({"time": time_str, "title": summary})
        
        # 按时间排序
        events.sort(key=lambda x: x['time'])
        return events
    except Exception as e:
        print(f"日历获取失败: {e}")
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
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 36px; font-weight: bold; color: #1c1c1e;">{weather['temp']}°</div>
                <div style="color: #3a3a3c; font-size: 14px;">{weather['desc']} | 💧{weather['humidity']}%</div>
            </div>
            <img src="{weather['icon']}" style="width: 60px; height: 60px;">
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