"""
一鍵式股票投資決策 App
手術室美學——白底、大數字、精準診斷
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from screener import render_stock_screener

st.set_page_config(
    page_title="沅劭帶你賺大錢",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

tw_tz  = pytz.timezone("Asia/Taipei")
now_tw = datetime.now(tw_tz)

# ── 每 30 秒自動刷新（JS 計時器，避免 yfinance 限流）──
st.markdown(
    "<script>setTimeout(function(){window.parent.location.reload();}, 300000);</script>",
    unsafe_allow_html=True,
)

STOCK_NAMES = {
    "TSM":"台積電","NVDA":"輝達","AAPL":"蘋果","MSFT":"微軟",
    "AMZN":"亞馬遜","META":"Meta","GOOGL":"谷歌","AMD":"超微",
    "AVGO":"博通","TSLA":"特斯拉","INTC":"英特爾","QCOM":"高通",
    "2330.TW":"台積電","2317.TW":"鴻海","2454.TW":"聯發科",
    "2308.TW":"台達電","2881.TW":"富邦金","2882.TW":"國泰金",
    "2303.TW":"聯電","3008.TW":"大立光","2412.TW":"中華電",
    "2002.TW":"中鋼","1301.TW":"台塑","2886.TW":"兆豐金",
}

FUNNY_DESCS = {
    "TSM":     "全世界最強晶片代工廠！你手上的iPhone、顯卡、AI伺服器，99%的晶片都是台積電做的。全球科技業都要跪著叫他們「晶圓教主」，沒有台積電，輝達、蘋果通通得跪著求饒。",
    "2330.TW": "全世界最強晶片代工廠！你手上的iPhone、顯卡、AI伺服器，99%的晶片都是台積電做的。全球科技業都要跪著叫他們「晶圓教主」，沒有台積電，輝達、蘋果通通得跪著求饒。",
    "NVDA":    "本來只是做打遊戲用的顯卡，沒想到AI時代來了，老黃（CEO黃仁勳）直接搖身一變成科技界的神。現在每個AI公司都要排隊求他賣GPU，黃仁勳出場穿皮衣比明星還有排場。",
    "AAPL":    "賣手機、電腦、耳機，但重點是他們賣的不是產品，是「生活方式」。一台iPhone賣你三萬，你還覺得自己賺到了——這就是蘋果的邪教魔法，加入了就出不去。",
    "MSFT":    "就是那個讓你天天用的Windows跟Office。現在又大舉投資OpenAI（ChatGPT他爸），準備稱霸AI時代。老牌企業重返巔峰，穩如老狗——比你想得更能打。",
    "AMZN":    "從賣書起家，現在什麼都賣。但賺最多的其實是AWS雲端服務，全球一半的網站都跑在他家伺服器上。貝佐斯能去太空玩，就是靠你每次在Amazon買東西湊出來的火箭錢。",
    "META":    "就是Facebook媽媽公司，旗下還有IG跟WhatsApp。砸幾千億蓋元宇宙蓋到虧爆，但廣告業務照樣賺翻——因為你每次滑IG看到廣告，都是在幫祖克柏還元宇宙的債。",
    "GOOGL":   "你每天查資料、看YouTube、用Gmail——都是他家的。本業是賣廣告，也就是說你每次Google完去點廣告，都是在幫他繳員工薪水。全世界最大的「免費服務」其實你才是產品。",
    "AMD":     "Intel的最強對手，靠著Ryzen和RX顯卡把Intel打得滿地找牙。執行長蘇姿丰（苦媽）帶著工程師默默逆襲，現在也跑去跟輝達搶AI生意。矽谷最勵志的翻身故事。",
    "AVGO":    "不常聽說但超賺的半導體公司，做網路晶片、儲存控制器之類的零件。就是那種你看不到、但沒它資料中心直接停機的「幕後黑手」。悶聲發大財的典範。",
    "TSLA":    "馬斯克的電動車王國，賣車只是表面，他真正的夢想是全自動駕駛AI和機器人。股價波動比雲霄飛車還刺激，粉絲和放空者每天都在互相咒罵——但你不得不承認這傢伙很有戲。",
    "INTC":    "曾經的處理器之神，被AMD打到丟失半壁江山，又沒搭上AI算力浪潮。現在靠「重建晶圓廠」的故事在撐，能否王者歸來？讓我們繼續看這齣落難貴族的復仇劇。",
    "QCOM":    "你手機裡的驍龍晶片十之八九是他家的，加上無線通訊專利，只要有人打電話，他就默默抽錢。悶聲發大財的隱形收費站，每通電話都在幫他賺錢。",
    "2317.TW": "全球最大電子代工廠，幫蘋果組裝iPhone就是他們！廠房超大、員工超多。每次iPhone發表，股價就開始躁動——因為郭台銘的工廠又要日夜趕工了。",
    "2454.TW": "台灣的手機晶片之王！從早年「山寨機晶片」出道，現在已是高端旗艦玩家，三星、小米、OPPO都跟他買晶片。蔡明介靠技術硬實力，把聯發科從山寨洗白成精品。",
    "2308.TW": "電源供應器和散熱風扇做到全球第一。AI資料中心的電費和熱量都是天文數字，台達電就靠這個悶聲數鈔票。本業低調但護城河深，科技業用電量越大他越爽。",
    "2881.TW": "台灣最大金融集團之一，銀行＋保險＋證券一把抓。台灣人不管是存錢、投資還是保命，很多都在跟富邦打交道。老蔡家族的金融帝國——低調但爸爸很有錢。",
    "2882.TW": "台灣壽險龍頭，台灣阿姨大叔買保險，十個有四個選國泰。業務穩健，配息規律，是那種你祖母會推薦你買的股票——而且她通常是對的。",
    "2303.TW": "台積電的老二，同樣做晶圓代工，但主打「成熟製程」。先進製程比不上台積電，但很多產品根本不需要最先進的，聯電就是那個「夠用就好、CP值高」的選擇。",
    "3008.TW": "全球最強手機鏡頭製造商！iPhone能拍那麼好的照片，大立光的鏡頭功不可沒。技術壁壘超高，全球競爭者想追上，先準備個十年再說。",
    "2412.TW": "台灣最大電信商，你的4G/5G信號、網路、電話費，很多都進了中華電的口袋。業務超級穩定、每年配息，是阿公阿嬤最愛的定存股——無聊但讓人安心。",
    "2002.TW": "台灣最大鋼鐵廠，台灣蓋橋、鋪路、建大樓的鋼筋很多都是他家的。景氣好的時候超賺，景氣差的時候靠配息撐著——典型的景氣循環股，要懂得跟著景氣跳舞。",
    "1301.TW": "王永慶老先生創立的石化巨頭！從塑膠袋到汽車零件，生活裡很多「塑膠類」東西都跟他有關係。老牌台灣企業，穩健低調，就是那種默默賺了幾十年的大叔。",
    "2886.TW": "老字號公股銀行，背後有政府撐腰，穩健但成長慢。配息穩定，是保守型投資人的最愛——不求爆發但求長久，適合那種你爸爸幫你買、然後忘記的股票。",
}

def get_funny_desc(ticker, original):
    t = ticker.upper()
    if t in FUNNY_DESCS:
        return FUNNY_DESCS[t]
    if original:
        sentences = original.replace("。", "。|").replace(". ", ". |").split("|")
        short = " ".join(s.strip() for s in sentences[:2] if s.strip())
        return short if short else original[:200]
    return ""

def get_cn_name(ticker):
    return STOCK_NAMES.get(ticker.upper(), "")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; background:#F7F8FA; color:#111; }
.stApp { background:#F7F8FA; }
.block-container { padding:1.25rem 1.25rem 4rem; max-width:960px; }
#MainMenu,footer,header { visibility:hidden; }
.stDeployButton { display:none; }
section[data-testid="stSidebar"] { display:none; }

/* 隱藏 Manage App 工具列 */
[data-testid="stToolbar"] { display:none !important; }
[data-testid="manage-app-button"] { display:none !important; }
iframe[title="streamlit_toolbar"] { display:none !important; }
.stAppToolbar { display:none !important; }
div[class*="Toolbar"] { display:none !important; }

/* 重新整理按鈕特殊樣式 */
.refresh-btn > button {
    background: #F0FDF4 !important;
    color: #166534 !important;
    border: 1.5px solid #00A86B !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
}

/* 搜尋框 */
.stTextInput>div>div>input {
    background:#fff !important; border:2px solid #E0E3E8 !important;
    border-radius:12px !important; color:#111 !important;
    font-size:1rem !important; font-family:'DM Mono',monospace !important;
    padding:0.75rem 1rem !important;
}
.stTextInput>div>div>input:focus { border-color:#0A66C2 !important; box-shadow:0 0 0 3px rgba(10,102,194,0.12) !important; }
.stTextInput>label { display:none !important; }

/* 按鈕 */
.stButton>button {
    background:#111 !important; color:#fff !important; border:none !important;
    border-radius:10px !important; font-weight:600 !important;
    font-size:0.88rem !important; padding:0.55rem 1rem !important;
    width:100% !important; font-family:'DM Sans',sans-serif !important;
}
.stButton>button:hover { background:#333 !important; }

/* Selectbox */
.stSelectbox>div>div { background:#fff !important; border:1.5px solid #E0E3E8 !important; border-radius:10px !important; color:#111 !important; }
.stSelectbox>label { font-size:0.75rem !important; color:#9CA3AF !important; font-weight:600 !important; letter-spacing:0.06em !important; }

/* Number input */
.stNumberInput>div>div>input { background:#fff !important; border:1.5px solid #E0E3E8 !important; border-radius:10px !important; color:#111 !important; font-family:'DM Mono',monospace !important; }
.stNumberInput>label { font-size:0.75rem !important; color:#9CA3AF !important; font-weight:600 !important; letter-spacing:0.06em !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background:#EEEFF2; border-radius:12px; padding:5px; gap:4px; border:none; }
.stTabs [data-baseweb="tab"] { background:transparent; color:#6B7280; border-radius:9px; font-weight:500; font-size:0.9rem; padding:0.5rem 1.2rem !important; }
.stTabs [aria-selected="true"] { background:#fff !important; color:#111 !important; box-shadow:0 1px 4px rgba(0,0,0,0.10) !important; }

/* 卡片 */
.card { background:#fff; border:1px solid #E8EAED; border-radius:14px; padding:1.25rem 1.5rem; }
.card-sm { background:#fff; border:1px solid #E8EAED; border-radius:12px; padding:0.9rem 1rem; }

/* 大數字 */
.verdict-number { font-family:'DM Mono',monospace; font-size:4rem; font-weight:500; line-height:1; letter-spacing:-0.03em; }
.verdict-win  { color:#00A86B; }
.verdict-loss { color:#E53935; }
.verdict-label { font-size:0.68rem; font-weight:700; letter-spacing:0.10em; text-transform:uppercase; color:#9CA3AF; margin-bottom:0.35rem; }
.verdict-sub { font-size:0.78rem; color:#6B7280; margin-top:0.3rem; font-family:'DM Mono',monospace; }

/* 警示 */
.alert-danger { background:#FFF5F5; border:1.5px solid #E53935; border-radius:10px; padding:0.85rem 1.1rem; color:#B91C1C; font-size:0.82rem; font-weight:500; line-height:1.6; }
.alert-safe   { background:#F0FDF4; border:1.5px solid #00A86B; border-radius:10px; padding:0.75rem 1rem; color:#166534; font-size:0.82rem; font-weight:500; }
.alert-warn   { background:#FFFBEB; border:1.5px solid #F59E0B; border-radius:10px; padding:0.85rem 1.1rem; color:#92400E; font-size:0.82rem; font-weight:500; line-height:1.6; }

/* 股票卡（整張卡片 = 按鈕） */
.hot-ticker { font-family:'DM Mono',monospace; font-size:0.88rem; font-weight:600; color:#0A66C2; }
.hot-cn { font-size:0.72rem; color:#9CA3AF; }
.grid-card-btn button {
    background:#fff !important;
    border-radius:16px !important;
    text-align:left !important;
    padding:1rem 1.1rem !important;
    height:auto !important;
    min-height:130px !important;
    color:#111 !important;
    white-space:pre-line !important;
    line-height:1.7 !important;
    font-size:0.83rem !important;
    transition:box-shadow 0.18s, transform 0.15s !important;
    box-shadow:0 1px 4px rgba(0,0,0,0.06) !important;
    width:100% !important;
}
.grid-card-btn button:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 6px 18px rgba(0,0,0,0.10) !important;
}
/* 各排邊框色 */
.row-blue button  { border:2px solid #93C5FD !important; }
.row-blue button:hover  { border-color:#3B82F6 !important; background:#F0F7FF !important; }
.row-pink button  { border:2px solid #F9A8D4 !important; }
.row-pink button:hover  { border-color:#EC4899 !important; background:#FDF4F8 !important; }
.row-gold button  { border:2px solid #FCD34D !important; }
.row-gold button:hover  { border-color:#F59E0B !important; background:#FFFCF0 !important; }
.row-green button { border:2px solid #86EFAC !important; }
.row-green button:hover { border-color:#22C55E !important; background:#F0FDF4 !important; }
.row-purple button{ border:2px solid #C4B5FD !important; }
.row-purple button:hover{ border-color:#8B5CF6 !important; background:#F8F5FF !important; }
.hot-price { font-size:1.05rem; font-weight:700; margin-top:0.25rem; }
.pos { color:#00A86B; } .neg { color:#E53935; }

/* 新聞列表純 HTML 連結 hover */
a:hover > div[style*="border-bottom:1px solid #EAECEF"] {
    background:#F0F7FF !important;
}

.divider { border:none; border-top:1px solid #E8EAED; margin:1rem 0; }

/* Expander 投資參數 */
.streamlit-expanderHeader {
    background: #F0F4FF !important;
    border: 1.5px solid #DBEAFE !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: #1D4ED8 !important;
    padding: 0.6rem 1rem !important;
}
.streamlit-expanderContent {
    border: 1.5px solid #DBEAFE !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    padding: 1rem !important;
    background: #FAFBFF !important;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════
# 工具函數
# ═══════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_quote(ticker):
    import concurrent.futures
    t = yf.Ticker(ticker)

    # ── 1. 價格：永遠用 fast_info（快、穩、不 timeout）──
    price, prev, currency, mkt_cap = 0.0, 0.0, "USD", 0
    try:
        fi       = t.fast_info
        price    = float(fi.last_price or 0)
        prev     = float(fi.previous_close or price)
        currency = getattr(fi, "currency", "USD") or "USD"
        mkt_cap  = getattr(fi, "market_cap", 0) or 0
    except Exception:
        pass

    if not price:
        return {"ok": False, "error": "找不到價格"}

    # ── 2. 財務數據：.info 加 8 秒 timeout，超時就放空 ──
    info = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            info = ex.submit(lambda: t.info or {}).result(timeout=8)
    except Exception:
        pass

    # .info 有更精確的價格就採用
    info_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    if info_price:
        price = float(info_price)
        prev  = float(info.get("previousClose") or prev)
    if info.get("currency"):
        currency = info["currency"]
    if info.get("marketCap"):
        mkt_cap = info["marketCap"]

    chg = (price - prev) / prev * 100 if prev else 0

    # ── 3. 52W 高低 + PE：.info 沒有就從歷史／財報自己算 ──
    w52h = info.get("fiftyTwoWeekHigh") or 0
    w52l = info.get("fiftyTwoWeekLow") or 0
    pe_val  = info.get("trailingPE")
    eps_val = info.get("trailingEps")

    hist = None
    try:
        hist = t.history(period="1y", auto_adjust=True)
    except Exception:
        pass

    if not w52h and hist is not None and not hist.empty:
        w52h = float(hist["High"].max())
        w52l = float(hist["Low"].min())

    # PE fallback：用季度財報算 TTM EPS → price / EPS
    if pe_val is None and price > 0:
        try:
            shares = getattr(fi, "shares", 0) or 0
            if shares > 0:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    q_stmt = ex.submit(lambda: t.quarterly_income_stmt).result(timeout=10)
                if q_stmt is not None and not q_stmt.empty:
                    for row_name in q_stmt.index:
                        label = str(row_name)
                        if "Net Income" in label and "Minority" not in label and "Noncontrolling" not in label:
                            ttm_ni = float(q_stmt.loc[row_name].iloc[:4].sum())
                            if ttm_ni > 0:
                                eps_val = ttm_ni / shares
                                pe_val  = price / eps_val
                            break
        except Exception:
            pass

    fetched_at = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "ok": True, "ticker": ticker.upper(),
        "name": info.get("longName", ticker.upper()),
        "cn_name": get_cn_name(ticker),
        "price": price, "chg_pct": chg, "chg_abs": price - prev,
        "volume": info.get("volume", 0), "mkt_cap": mkt_cap,
        "pe": pe_val, "pb": info.get("priceToBook"),
        "eps": eps_val, "rev_growth": info.get("revenueGrowth"),
        "sector": info.get("sector", ""), "currency": currency,
        "w52h": w52h, "w52l": w52l,
        "beta": info.get("beta", 1.0), "desc": info.get("longBusinessSummary", ""),
        "target": info.get("targetMeanPrice"), "rec": info.get("recommendationKey", ""),
        "fetched_at": fetched_at,
    }

@st.cache_data(ttl=86400, show_spinner=False)
def get_long_history(ticker):
    try:
        h = yf.Ticker(ticker).history(period="5y", auto_adjust=True)
        if h.empty:
            h = yf.Ticker(ticker).history(period="3y", auto_adjust=True)
        if not h.empty:
            h.index = pd.to_datetime(h.index).tz_localize(None)
        return h
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def get_history(ticker, period="1y"):
    try:
        df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        df.index = pd.to_datetime(df.index).tz_localize(None)

        # ── 過濾 yfinance 台股除權息調整 bug 造成的極端跳價 ──
        # 單日 log return 超過 ±20% 視為資料異常，用前一日收盤填補
        if len(df) > 5:
            log_ret = np.log(df["Close"] / df["Close"].shift(1)).abs()
            bad = log_ret > 0.20
            df.loc[bad, "Close"] = np.nan
            df["Close"] = df["Close"].ffill()

        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def get_news(ticker):
    try:
        items = yf.Ticker(ticker).news or []
        result = []
        for n in items[:12]:
            content = n.get("content") or {}
            thumb = ""
            if content:
                title     = content.get("title", "")
                link      = (content.get("canonicalUrl") or {}).get("url", "#") or \
                            (content.get("clickThroughUrl") or {}).get("url", "#")
                publisher = (content.get("provider") or {}).get("displayName", "")
                pub_date  = content.get("pubDate", "")
                img = content.get("thumbnail") or {}
                if isinstance(img, dict):
                    thumb = img.get("originalUrl") or img.get("url", "")
                try:
                    t = datetime.fromisoformat(pub_date.replace("Z", "+00:00")).astimezone(tw_tz).replace(tzinfo=None)
                except Exception:
                    t = datetime.now()
            else:
                title     = n.get("title", "")
                link      = n.get("link", "#")
                publisher = n.get("publisher", "")
                ts        = n.get("providerPublishTime", 0)
                t         = datetime.fromtimestamp(ts) if ts else datetime.now()
                raw_thumb = n.get("thumbnail") or {}
                ress = raw_thumb.get("resolutions", [])
                if ress:
                    thumb = ress[-1].get("url", "")
            if title:
                result.append({"title": title, "publisher": publisher, "link": link, "time": t, "thumb": thumb})
        return result
    except Exception:
        return []

def run_mc(close, hold_days, n=8000):
    log_ret = np.log(close/close.shift(1)).dropna()
    # 過濾除權息 bug 造成的離群值（與 check_risks 一致）
    log_ret = log_ret[log_ret.abs() <= 0.15]
    mu, sigma = log_ret.mean(), log_ret.std()
    entry = float(close.iloc[-1])
    rands = np.random.standard_normal((n, hold_days))
    finals = entry * np.exp(np.cumsum((mu-0.5*sigma**2)+sigma*rands, axis=1)[:,-1])
    returns = (finals/entry-1)*100
    paths = entry * np.exp(np.cumsum(
        (mu-0.5*sigma**2)+sigma*np.random.standard_normal((80,hold_days)), axis=1))
    return {"win":float(np.mean(returns>0)*100), "loss":float(np.mean(returns<0)*100),
            "exp":float(np.mean(returns)), "p10":float(np.percentile(returns,10)),
            "p90":float(np.percentile(returns,90)),
            "vol":sigma*np.sqrt(252)*100, "entry":entry,
            "paths":paths, "mu":mu, "sigma":sigma}

MEME_STOCKS = {"GME", "AMC", "BBBY", "KOSS", "BB", "NOK", "EXPR", "CLOV", "WISH", "WKHS"}

def check_risks(quote, df):
    risks = []
    if df.empty or not quote.get("ok"): return risks
    close, volume = df["Close"], df["Volume"]

    # ══════════════════════════════════════════════════════
    # 防線 0：MEME 股黑名單（不依賴財務數字，直接強制警示）
    # ══════════════════════════════════════════════════════
    base_ticker = quote.get("ticker", "").upper().split(".")[0]
    if base_ticker in MEME_STOCKS:
        risks.append({"level": "danger",
            "msg": f"🚨 已知高度投機 MEME 股（{base_ticker}）：股價極易受社群媒體與市場情緒操縱，"
                   "與基本面嚴重脫鉤，請勿以正常估值邏輯判斷，風險極高"})
    eps = quote.get("eps")
    pe  = quote.get("pe")

    if eps is not None and eps < 0:
        risks.append({"level": "warn",
            "msg": f"⚠️ 基本面風險：EPS 為負（{eps:.2f}），公司目前尚未獲利"})
    elif pe is not None and pe <= 0:
        risks.append({"level": "warn",
            "msg": "⚠️ 基本面風險：P/E Ratio 為負數，獲利能力存疑"})

    # ══════════════════════════════════════════════════════
    # 防線 2：高波動 / Beta
    # Beta > 2.0 觸發（台股 beta 普遍比美股高，1.5 太嚴格）
    # 年化波動率 > 60% 觸發（過濾離群值後再算，避免除權息 bug）
    # ══════════════════════════════════════════════════════
    beta = quote.get("beta") or 0

    ann_vol = 0.0
    if len(close) >= 30:
        log_ret = np.log(close / close.shift(1)).dropna()
        # 過濾單日超過 ±15% 的離群值（除權息調整 bug 保護）
        log_ret_clean = log_ret[log_ret.abs() <= 0.15]
        if len(log_ret_clean) >= 20:
            ann_vol = float(log_ret_clean.std() * np.sqrt(252) * 100)

    high_vol  = ann_vol > 60
    high_beta = beta > 2.0

    if high_beta or high_vol:
        detail_parts = []
        if high_beta: detail_parts.append(f"Beta {beta:.2f}")
        if high_vol:  detail_parts.append(f"年化波動率 {ann_vol:.1f}%")
        risks.append({"level": "danger",
            "msg": "🚨 極高波動風險：此為高風險/高波動標的，極易受市場情緒操縱，"
                   f"請嚴格控管資金（{' / '.join(detail_parts)}）"})

    # ══════════════════════════════════════════════════════
    # 防線 3：新上市 / 歷史數據不足
    # ══════════════════════════════════════════════════════
    days_of_data = len(close)
    if days_of_data < 30:
        risks.append({"level": "danger",
            "msg": f"⚠️ 新上市股票：僅有 {days_of_data} 天歷史數據，"
                   "模擬結果可靠度極低，風險極高，請謹慎"})
    elif days_of_data < 60:
        risks.append({"level": "danger",
            "msg": "新上市 / 資料不足：無法完整偵測籌碼異常，"
                   "建議等待上市滿 3 個月後再評估"})

    # ══════════════════════════════════════════════════════
    # 防線 4：高估值 IPO / P/E 過高
    # ══════════════════════════════════════════════════════
    mkt_cap = quote.get("mkt_cap", 0)
    currency = quote.get("currency", "USD")
    # 統一換算成美元比較（台幣約 1 USD = 32 TWD）
    mkt_cap_usd = mkt_cap / 32 if currency == "TWD" else mkt_cap
    if mkt_cap_usd and mkt_cap_usd > 1e12 and pe is not None and pe <= 0:
        risks.append({"level": "danger",
            "msg": "市值超過 1 兆美元但尚未獲利（P/E 為負），"
                   "屬於高風險成長股，估值泡沫風險高"})

    if pe and pe > 0:
        _sector = quote.get("sector", "") or ""
        _ticker_up = quote.get("ticker", "")
        _is_tech = (
            "Technology" in _sector or
            "Semiconductor" in _sector or
            "Electronic" in _sector or
            _ticker_up.endswith(".TW")  # 台股普遍 PE 偏高，統一用科技門檻
        )
        th = 80 if _is_tech else 50
        if pe > th * 2:
            risks.append({"level": "danger",
                "msg": f"P/E {pe:.0f}x 極度高估（超過合理值 {int(th*2)}x），小心估值崩塌"})
        elif pe > th * 1.5:
            risks.append({"level": "danger", "msg": f"P/E {pe:.0f}x 嚴重高估"})
        elif pe > th:
            risks.append({"level": "warn",   "msg": f"P/E {pe:.0f}x 估值偏高"})

    # ══════════════════════════════════════════════════════
    # 防線 5：VIX 恐慌指數
    # ══════════════════════════════════════════════════════
    try:
        vix = float(yf.Ticker("^VIX").history(period="3d")["Close"].iloc[-1])
        if vix >= 30:
            risks.append({"level": "warn", "msg": f"VIX {vix:.1f} 市場極度恐慌，建議大幅降低投入"})
        elif vix >= 22:
            risks.append({"level": "warn", "msg": f"VIX {vix:.1f} 市場警戒"})
    except:
        pass

    # ══════════════════════════════════════════════════════
    # 防線 6：成交量異常爆量
    # ══════════════════════════════════════════════════════
    if len(volume) >= 60:
        r = float(volume.tail(5).mean()) / float(volume.tail(60).mean())
        if r >= 3.5:
            risks.append({"level": "danger", "msg": f"成交量異常爆量 {r:.1f} 倍，疑似主力介入"})
        elif r >= 2.5:
            risks.append({"level": "warn",   "msg": f"成交量放大 {r:.1f} 倍，留意籌碼"})

    # ══════════════════════════════════════════════════════
    # 防線 7：短期暴漲
    # ══════════════════════════════════════════════════════
    if len(close) >= 11:
        ret5 = (float(close.iloc[-1]) / float(close.iloc[-6]) - 1) * 100
        if ret5 >= 30:
            risks.append({"level": "danger", "msg": f"5日暴漲 {ret5:.1f}%，小心追高接刀"})
        elif ret5 >= 18:
            risks.append({"level": "warn",   "msg": f"5日急漲 {ret5:.1f}%"})

    return risks

def fmt_cap(v, currency="USD"):
    sym = "NT$" if currency == "TWD" else "$"
    if v>=1e12: return f"{sym}{v/1e12:.2f}T"
    if v>=1e9:  return f"{sym}{v/1e9:.1f}B"
    if v>=1e6:  return f"{sym}{v/1e6:.1f}M"
    return f"{sym}{v:,.0f}"

US_TICKERS = ["TSM","NVDA","AAPL","MSFT","AMZN","META","AMD","TSLA"]
TW_TICKERS = ["2330.TW","2317.TW","2454.TW","2308.TW","2881.TW","2882.TW","2303.TW","3008.TW"]

@st.cache_data(ttl=300, show_spinner=False)
def get_fast_quote(ticker: str) -> dict:
    """首頁卡片用：只抓價格，速度快。"""
    try:
        fi = yf.Ticker(ticker).fast_info
        price = float(fi.last_price or 0)
        prev  = float(fi.previous_close or price)
        chg   = (price - prev) / prev * 100 if prev else 0.0
        cur   = getattr(fi, "currency", "TWD")
        return {"ok": True, "ticker": ticker, "price": price,
                "chg_pct": chg, "currency": cur,
                "cn_name": get_cn_name(ticker)}
    except Exception:
        return {"ok": False}

@st.cache_data(ttl=300, show_spinner=False)
def load_stocks(tickers):
    out = []
    for t in tickers:
        # 先用 fast_info 取價格（快），再補 mkt_cap
        q = get_fast_quote(t)
        if q.get("ok") and q["price"] > 0:
            try:
                info = yf.Ticker(t).fast_info
                q["mkt_cap"] = getattr(info, "market_cap", 0) or 0
            except Exception:
                q["mkt_cap"] = 0
            out.append(q)
    return out


@st.cache_data(ttl=300, show_spinner=False)
def get_quick_risk_status(ticker: str) -> dict:
    """
    首頁燈號：直接複用 check_risks，與個股頁永遠一致。
    快取 1 小時，避免首頁重複打 API。
    回傳 {"emoji": "🔴/🟡/🟢", "label": "危險/中等/安全", "color": "..."}
    """
    try:
        quote = get_quote(ticker)
        df    = get_history(ticker)
        risks = check_risks(quote, df)

        if any(r["level"] == "danger" for r in risks):
            return {"emoji": "🔴", "label": "危險", "color": "#E53935"}
        if any(r["level"] == "warn"   for r in risks):
            return {"emoji": "🟡", "label": "中等", "color": "#F59E0B"}
        return     {"emoji": "🟢", "label": "安全", "color": "#00A86B"}

    except Exception:
        return     {"emoji": "🟡", "label": "中等", "color": "#F59E0B"}


# ═══════════════════════════════════════════
# 狀態管理
# ═══════════════════════════════════════════

if "active" not in st.session_state: st.session_state.active = ""
if "invest" not in st.session_state: st.session_state.invest = 10000
if "hold"   not in st.session_state: st.session_state.hold   = "3 個月"


# ═══════════════════════════════════════════
# 頂部：標題 + 搜尋列（永遠顯示）
# ═══════════════════════════════════════════

# ── 標題列：時間 + 自動更新提示 ──────────────────
st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.25rem'>
  <div style='font-size:1.3rem;font-weight:700;letter-spacing:-0.02em'>💰 沅劭帶你賺大錢</div>
  <div style='text-align:right'>
    <div style='font-size:0.72rem;color:#9CA3AF;font-family:DM Mono,monospace'>🇹🇼 {now_tw.strftime('%H:%M:%S')}</div>
    <div style='font-size:0.62rem;color:#C4C9D4'>● 每 30 秒自動更新</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 搜尋列：輸入框 + 🔍分析 ──────────────────────
with st.form(key="search_form", clear_on_submit=False):
    fcols = st.columns([5.5, 1.5])
    with fcols[0]:
        search_val = st.text_input("搜尋", placeholder="美股：AAPL　台股直接輸入數字：2330",
                                    label_visibility="collapsed", key="search_box")
    with fcols[1]:
        search_btn = st.form_submit_button("🔍 分析", use_container_width=True)

def normalize_ticker(raw: str) -> str:
    """
    去空格、轉大寫；
    若輸入是純數字（台股代號），自動補 .TW（上市），
    後續若抓不到再 fallback 到 .TWO（上櫃）。
    """
    t = raw.replace(" ", "").upper()
    if t.isdigit():
        t = t + ".TW"
    return t

if search_btn and search_val.strip():
    st.session_state.active = normalize_ticker(search_val)
    st.rerun()

# ── 投資參數（可收合下拉）────────────────────────
with st.expander("⚙️ 投資參數設定", expanded=False):
    p1, p2 = st.columns(2)
    with p1:
        invest_amount = st.number_input("投入金額（USD $）", min_value=100, max_value=10_000_000,
                                         value=st.session_state.invest, step=1000, format="%d")
        st.session_state.invest = invest_amount
    with p2:
        hold_map = {"1 個月":21, "3 個月":63, "6 個月":126, "1 年":252}
        hold_choice = st.selectbox("預計持有時間", list(hold_map.keys()),
                                    index=list(hold_map.keys()).index(st.session_state.hold))
        st.session_state.hold = hold_choice
hold_map  = {"1 個月":21, "3 個月":63, "6 個月":126, "1 年":252}
hold_days = hold_map[st.session_state.hold]
invest_amount = st.session_state.invest

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ═══════════════════════════════════════════
# 分支 A：首頁
# ═══════════════════════════════════════════

if not st.session_state.active:
    st.markdown("<div style='font-size:1.1rem;font-weight:700;margin-bottom:0.75rem'>今日市場總覽</div>", unsafe_allow_html=True)

    tab_tw, tab_us, tab_screen = st.tabs(["🇹🇼  台股熱門", "🇺🇸  美股熱門", "🎯  自己選啦"])

    ROW_COLORS = ["row-blue", "row-pink", "row-gold", "row-green", "row-purple"]

    def render_grid(tickers):
        with st.spinner("載入行情…"):
            stocks = load_stocks(tickers)
        rows = [stocks[i:i+2] for i in range(0, len(stocks), 2)]
        for row_idx, pair in enumerate(rows):
            row_cls = ROW_COLORS[row_idx % len(ROW_COLORS)]
            cols = st.columns(2)
            for col, q in zip(cols, pair):
                chg    = q["chg_pct"]
                arrow  = "▲" if chg >= 0 else "▼"
                cn     = q.get("cn_name", "")
                cur    = q.get("currency", "TWD")
                risk   = get_quick_risk_status(q["ticker"])
                mkt_cap = q.get("mkt_cap", 0)
                cap_str = fmt_cap(mkt_cap, cur)
                chg_sym = "+" if chg >= 0 else ""
                label = (
                    f"{risk['emoji']} {risk['label']}   {q['ticker']}\n"
                    f"{cn}\n"
                    f"{cur} {q['price']:,.1f}\n"
                    f"{arrow} {abs(chg):.2f}%   {cap_str}"
                )
                with col:
                    st.markdown(f'<div class="grid-card-btn {row_cls}">', unsafe_allow_html=True)
                    if st.button(label, key=f"btn_{q['ticker']}", use_container_width=True):
                        st.session_state.active = q["ticker"]
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    with tab_tw:
        render_grid(TW_TICKERS)
    with tab_us:
        render_grid(US_TICKERS)
    with tab_screen:
        render_stock_screener()

    st.stop()


# ═══════════════════════════════════════════
# 分支 B：個股分析
# ═══════════════════════════════════════════

active = st.session_state.active

# 返回按鈕
if st.button("← 返回首頁"):
    st.session_state.active = ""
    st.rerun()

with st.spinner(f"分析 {active} 中…"):
    quote = get_quote(active)
    df    = get_history(active)

    # ── 智慧後備：.TW 抓不到時自動試 .TWO（上櫃股票）──
    need_fallback = (
        active.endswith(".TW") and
        (not quote.get("ok") or quote.get("price", 0) == 0 or df.empty)
    )
    if need_fallback:
        two_ticker = active[:-3] + ".TWO"
        quote_two  = get_quote(two_ticker)
        df_two     = get_history(two_ticker)
        if quote_two.get("ok") and quote_two.get("price", 0) > 0:
            quote  = quote_two
            df     = df_two
            active = two_ticker
            st.session_state.active = two_ticker
            st.toast(f"自動切換為上櫃代號 {two_ticker}", icon="💡")

if not quote.get("ok") or df.empty or quote["price"]==0:
    st.error(f"找不到「{active}」。美股請輸入代號如 AAPL，台股直接輸入數字如 2330")
    st.stop()

# 風險偵測
risks = check_risks(quote, df)
danger = [r for r in risks if r["level"]=="danger"]
warns  = [r for r in risks if r["level"]=="warn"]

if danger:
    st.markdown(f'<div class="alert-danger">🚨 <b>高風險警示</b><br>{"<br>".join("⚠️ "+r["msg"] for r in danger)}</div>', unsafe_allow_html=True)
if warns:
    st.markdown(f'<div class="alert-warn" style="margin-top:0.5rem">⚠️ <b>注意</b><br>{"<br>".join("• "+r["msg"] for r in warns)}</div>', unsafe_allow_html=True)
if not risks:
    st.markdown('<div class="alert-safe">✅ 未偵測到明顯風險</div>', unsafe_allow_html=True)

st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

# 股票標題
cn   = quote.get("cn_name","")
name = quote["name"]
price= quote["price"]
chg  = quote["chg_pct"]
cur  = quote.get("currency","USD")
pc   = "#00A86B" if chg>=0 else "#E53935"
arrow= "▲" if chg>=0 else "▼"

fetched_at = quote.get("fetched_at", "")
st.markdown(f"""
<div style="margin-bottom:0.75rem">
    <div style="font-size:0.72rem;color:#9CA3AF;font-weight:600;letter-spacing:0.06em;text-transform:uppercase">{quote.get('sector','') or '股票'} · {cur}</div>
    <div style="font-size:1.2rem;font-weight:700">{name}{"（"+cn+"）" if cn else ""}</div>
    <div style="display:flex;align-items:baseline;gap:0.75rem;margin-top:0.25rem">
        <span style="font-family:'DM Mono',monospace;font-size:1.8rem;font-weight:600;color:{pc}">{cur} {price:,.2f}</span>
        <span style="font-size:0.9rem;font-weight:600;color:{pc}">{arrow} {abs(chg):.2f}%</span>
    </div>
    {"<div style='font-size:0.65rem;color:#C4C9D4;margin-top:0.2rem'>🕐 資料擷取時間："+fetched_at+" (台灣時間)</div>" if fetched_at else ""}
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# 蒙地卡羅
close_s = df["Close"].dropna()
with st.spinner("模擬計算中…"):
    mc = run_mc(close_s, hold_days)

win_rate = mc["win"]
loss_rate= mc["loss"]
exp_pct  = mc["exp"]
exp_gain = invest_amount * exp_pct / 100
p10_amt  = invest_amount * mc["p10"] / 100
p90_amt  = invest_amount * mc["p90"] / 100

# 三大數字
st.markdown("<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.10em;text-transform:uppercase;color:#9CA3AF;margin-bottom:0.75rem'>決策核心 — 8,000 次模擬</div>", unsafe_allow_html=True)

v1, v2, v3 = st.columns(3)
with v1:
    st.markdown(f"""
    <div class="card" style="text-align:center;padding:1.5rem 0.5rem">
        <div class="verdict-label">勝率</div>
        <div class="verdict-number verdict-win">{win_rate:.0f}<span style="font-size:2rem">%</span></div>
        <div class="verdict-sub">賺錢的機率</div>
    </div>""", unsafe_allow_html=True)
with v2:
    st.markdown(f"""
    <div class="card" style="text-align:center;padding:1.5rem 0.5rem">
        <div class="verdict-label">賠錢機率</div>
        <div class="verdict-number verdict-loss">{loss_rate:.0f}<span style="font-size:2rem">%</span></div>
        <div class="verdict-sub">波動率 {mc['vol']:.1f}%</div>
    </div>""", unsafe_allow_html=True)
with v3:
    gc = "#00A86B" if exp_gain>=0 else "#E53935"
    gs = "+" if exp_gain>=0 else ""
    st.markdown(f"""
    <div class="card" style="text-align:center;padding:1.5rem 0.5rem">
        <div class="verdict-label">預測收益</div>
        <div class="verdict-number" style="color:{gc}">{gs}{exp_pct:.1f}<span style="font-size:2rem">%</span></div>
        <div class="verdict-sub">{gs}${abs(exp_gain):,.0f}</div>
    </div>""", unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center;font-size:0.72rem;color:#9CA3AF;margin-top:0.5rem">
    投入 {cur} {invest_amount:,} · 持有 {hold_choice} · 90% 落在 {p10_amt:+,.0f} ~ {p90_amt:+,.0f} {cur}
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# 次要指標
m1,m2,m3,m4 = st.columns(4)
_cur_sym = cur
_cur_sign = "NT$" if cur == "TWD" else "$"
for col,(label,val) in zip([m1,m2,m3,m4],[
    ("市值",   fmt_cap(quote["mkt_cap"], cur) if quote["mkt_cap"] else "N/A"),
    ("本益比", f"{quote['pe']:.1f}x"     if quote["pe"]      else "N/A"),
    ("一年最高價", f"{_cur_sym} {quote['w52h']:,.2f}" if quote["w52h"] else "N/A"),
    ("一年最低價", f"{_cur_sym} {quote['w52l']:,.2f}" if quote["w52l"] else "N/A"),
]):
    with col:
        st.markdown(f"""
        <div class="card-sm" style="text-align:center">
            <div style="font-size:0.65rem;color:#9CA3AF;font-weight:700;letter-spacing:0.06em;text-transform:uppercase">{label}</div>
            <div style="font-family:'DM Mono',monospace;font-size:1rem;font-weight:600;margin-top:0.2rem">{val}</div>
        </div>""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# Tabs
tab_chart, tab_news, tab_trade = st.tabs(["📈  走勢與預測", "📰  新聞與財報", "💰  真的要投？好啦"])

with tab_chart:
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        fig = make_subplots(rows=2,cols=1,row_heights=[0.72,0.28],
                            shared_xaxes=True,vertical_spacing=0.04)
        fig.add_trace(go.Scatter(x=df.index,y=df["Close"],name="收盤價",
            line=dict(color="#111",width=2),
            hovertemplate="%{x|%Y-%m-%d}<br>" + cur + " %{y:,.2f}<extra></extra>"),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["Close"].rolling(200).mean(),name="200MA",
            line=dict(color="#9CA3AF",width=1.5,dash="dot")),row=1,col=1)

        last_date    = df.index[-1]
        future_dates = pd.date_range(start=last_date+timedelta(days=1),periods=hold_days,freq="B")
        for path in mc["paths"][:50]:
            fig.add_trace(go.Scatter(x=future_dates,y=path,mode="lines",
                line=dict(color="rgba(10,102,194,0.07)",width=1),
                showlegend=False,hoverinfo="skip"),row=1,col=1)

        t = np.arange(1,hold_days+1)
        mu,sigma,entry = mc["mu"],mc["sigma"],mc["entry"]
        fig.add_trace(go.Scatter(x=future_dates,y=entry*np.exp((mu-0.5*sigma**2)*t+sigma*np.sqrt(t)*1.28),
            name="樂觀P90",line=dict(color="#00A86B",width=2,dash="dash")),row=1,col=1)
        fig.add_trace(go.Scatter(x=future_dates,y=entry*np.exp((mu-0.5*sigma**2)*t),
            name="中性P50",line=dict(color="#0A66C2",width=2)),row=1,col=1)
        fig.add_trace(go.Scatter(x=future_dates,y=entry*np.exp((mu-0.5*sigma**2)*t+sigma*np.sqrt(t)*(-1.28)),
            name="悲觀P10",line=dict(color="#E53935",width=2,dash="dash"),
            fill="tonexty",fillcolor="rgba(10,102,194,0.04)"),row=1,col=1)
        fig.add_vline(x=str(last_date),line_color="#E8EAED",line_width=1.5)

        vc = ["#00A86B" if c>=o else "#E53935" for c,o in zip(df["Close"],df["Open"])]
        fig.add_trace(go.Bar(x=df.index,y=df["Volume"],name="成交量",marker_color=vc,opacity=0.6),row=2,col=1)

        fig.update_layout(height=480,paper_bgcolor="#fff",plot_bgcolor="#fff",
            font=dict(family="DM Sans",color="#6B7280",size=11),hovermode="x unified",
            legend=dict(orientation="h",yanchor="bottom",y=1.01,bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(gridcolor="#F0F1F3"),yaxis=dict(gridcolor="#F0F1F3"),
            xaxis2=dict(gridcolor="#F0F1F3"),yaxis2=dict(gridcolor="#F0F1F3"),
            xaxis_rangeslider_visible=False)
        st.plotly_chart(fig,use_container_width=True)
    except Exception as e:
        st.warning(f"圖表錯誤：{e}")

with tab_news:
    col_n, col_f = st.columns([3, 2])

    with col_n:
        with st.spinner("抓取新聞…"):
            nl = get_news(active)

        if nl:
            try:
                _ns_idx = min(int(st.query_params.get("ns", 0)), len(nl) - 1)
            except Exception:
                _ns_idx = 0
            sel = nl[_ns_idx]

            sub_list, sub_feat = st.columns([4, 6])

            with sub_list:
                _list_html = "<div style='font-size:0.60rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#9CA3AF;margin-bottom:0.35rem'>近期新聞</div>"
                for _i, _n in enumerate(nl):
                    _is_sel  = (_i == _ns_idx)
                    _short   = _n["title"][:34] + "…" if len(_n["title"]) > 34 else _n["title"]
                    _ds      = _n["time"].strftime("%m/%d %H:%M")
                    _bg      = "#EFF6FF" if _is_sel else "#FAFAFA"
                    _bl      = "3px solid #3B82F6" if _is_sel else "3px solid transparent"
                    _fw      = "600" if _is_sel else "400"
                    _tc      = "#1D4ED8" if _is_sel else "#374151"
                    _list_html += f"""
                    <a href="?ns={_i}" style="text-decoration:none;display:block">
                      <div style="padding:0.35rem 0.4rem 0.35rem 0.5rem;background:{_bg};
                                  border-bottom:1px solid #EAECEF;border-left:{_bl}">
                        <div style="font-size:0.71rem;font-weight:{_fw};color:{_tc};
                                    line-height:1.28;display:-webkit-box;
                                    -webkit-line-clamp:2;-webkit-box-orient:vertical;
                                    overflow:hidden">{_short}</div>
                        <div style="font-size:0.60rem;color:#22C55E;margin-top:0.08rem">{_ds}</div>
                      </div>
                    </a>"""
                st.markdown(_list_html, unsafe_allow_html=True)

            with sub_feat:
                _t_str   = sel["time"].strftime("%Y/%m/%d %H:%M")
                _pub_str = (sel["publisher"] + " · ") if sel.get("publisher") else ""
                _img_html = (
                    f'<img src="{sel["thumb"]}" style="width:100%;height:172px;object-fit:cover;display:block">'
                    if sel.get("thumb") else
                    '<div style="height:172px;display:flex;align-items:center;justify-content:center;'
                    'background:linear-gradient(135deg,#DBEAFE,#EDE9FE)">'
                    '<span style="font-size:2.5rem">📰</span></div>'
                )
                _link_html = ""
                if sel.get("link") and sel["link"] != "#":
                    _link_html = (f'<a href="{sel["link"]}" target="_blank" style="text-decoration:none">'
                                  f'<div style="display:inline-block;background:#2563EB;color:#fff;'
                                  f'font-size:0.76rem;font-weight:600;padding:0.35rem 0.85rem;'
                                  f'border-radius:7px;margin-top:0.55rem">🔗 閱讀全文</div></a>')
                st.markdown(f"""
                <div style="border-radius:12px;overflow:hidden;border:1px solid #E8EAED;background:#fff">
                    {_img_html}
                    <div style="padding:0.72rem 0.85rem 0.8rem">
                        <div style="font-size:0.87rem;font-weight:700;color:#111;
                                    line-height:1.42;margin-bottom:0.25rem">{sel['title']}</div>
                        <div style="font-size:0.64rem;color:#22C55E">{_pub_str}{_t_str}</div>
                        {_link_html}
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#9CA3AF;font-size:0.85rem;padding:1rem 0">暫無新聞</div>', unsafe_allow_html=True)

    with col_f:
        st.markdown("<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#9CA3AF;margin-bottom:0.75rem'>財報指標</div>", unsafe_allow_html=True)
        def fin_row(k,v,pos=None):
            c = "#9CA3AF" if v in (None,"N/A") else "#00A86B" if pos is True else "#E53935" if pos is False else "#111"
            return f'<div style="display:flex;justify-content:space-between;padding:0.65rem 0;border-bottom:1px solid #F0F1F3"><span style="font-size:0.8rem;color:#6B7280">{k}</span><span style="font-family:DM Mono,monospace;font-size:0.85rem;font-weight:500;color:{c}">{v}</span></div>'

        pe=quote.get("pe"); pb=quote.get("pb"); eps=quote.get("eps")
        rev=quote.get("rev_growth"); beta=quote.get("beta"); tgt=quote.get("target")
        rev_s = f"+{rev*100:.1f}%" if rev and rev>0 else (f"{rev*100:.1f}%" if rev else "N/A")
        up = (tgt/price-1)*100 if tgt and price else None
        up_s = f"{_cur_sign}{tgt:.2f} ({up:+.1f}%)" if up else "N/A"

        html = (fin_row("本益比 P/E", f"{pe:.1f}x" if pe else "N/A") +
                fin_row("股價淨值比", f"{pb:.2f}x" if pb else "N/A") +
                fin_row("EPS",        f"{_cur_sign}{eps:.2f}" if eps else "N/A") +
                fin_row("營收成長",   rev_s, pos=(rev>0) if rev else None) +
                fin_row("Beta",       f"{beta:.2f}" if beta else "N/A") +
                fin_row("目標價",     up_s, pos=(up>0) if up else None) +
                fin_row("分析師評級", quote.get("rec","").upper() or "N/A"))
        st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)

        funny = get_funny_desc(active, quote.get("desc", ""))
        if funny:
            with st.expander("📖 公司簡介（白話版）"):
                st.markdown(f'<div style="font-size:0.82rem;color:#374151;line-height:1.9">{funny}</div>', unsafe_allow_html=True)

with tab_trade:
    try:
        close_t = df["Close"].dropna()
        vol_t   = df["Volume"].dropna()

        # ── RSI(14) ──────────────────────────────────────
        delta    = close_t.diff()
        gain     = delta.clip(lower=0).rolling(14).mean()
        loss     = (-delta.clip(upper=0)).rolling(14).mean()
        rsi_s    = 100 - (100 / (1 + gain / loss.replace(0, float("nan"))))
        cur_rsi  = float(rsi_s.iloc[-1]) if not rsi_s.empty else 50.0

        # ── 趨勢 ─────────────────────────────────────────
        ma200      = close_t.rolling(200).mean()
        above_ma   = bool(close_t.iloc[-1] > ma200.iloc[-1]) if len(ma200.dropna()) > 0 else True
        ma200_val  = float(ma200.iloc[-1]) if not ma200.dropna().empty else price

        # ── 52W 位置 ──────────────────────────────────────
        w52h_v = quote.get("w52h") or float(close_t.max())
        w52l_v = quote.get("w52l") or float(close_t.min())
        price_pct_in_range = (price - w52l_v) / (w52h_v - w52l_v) * 100 if w52h_v > w52l_v else 50.0

        # ── 量能比 ───────────────────────────────────────
        vol_ratio = float(vol_t.tail(5).mean() / vol_t.tail(60).mean()) if len(vol_t) >= 60 else 1.0

        # ── 操盤評分 ─────────────────────────────────────
        score = 0
        reasons = []
        if cur_rsi < 35:
            score += 3; reasons.append(f"RSI {cur_rsi:.0f} 超賣區，籌碼洗乾淨")
        elif cur_rsi < 50:
            score += 1; reasons.append(f"RSI {cur_rsi:.0f} 中性偏低")
        elif cur_rsi > 70:
            score -= 2; reasons.append(f"RSI {cur_rsi:.0f} 過熱，追高風險大")

        if above_ma:
            score += 1; reasons.append("站穩年線，長期趨勢向上")
        else:
            score -= 1; reasons.append("跌破年線，趨勢偏弱")

        if price_pct_in_range < 25:
            score += 2; reasons.append(f"股價接近年低（年內 {price_pct_in_range:.0f}% 位置）")
        elif price_pct_in_range > 80:
            score -= 1; reasons.append(f"股價靠近年高（年內 {price_pct_in_range:.0f}% 位置）")

        win_r = mc["win"]
        if win_r >= 72: score += 2
        elif win_r >= 60: score += 1
        elif win_r < 45: score -= 2

        if vol_ratio >= 2.0:
            score -= 1; reasons.append(f"爆量 {vol_ratio:.1f}x，主力可能出貨")
        elif vol_ratio < 0.6:
            score += 1; reasons.append("縮量盤整，蓄勢待發")

        # ── 總結 ─────────────────────────────────────────
        if score >= 4:
            verdict_label = "✅ 可以進場"
            verdict_color = "#00A86B"
            verdict_bg    = "rgba(0,168,107,0.07)"
            verdict_sub   = "多項指標同時看好，時機成熟"
        elif score >= 1:
            verdict_label = "⏳ 等待更好時機"
            verdict_color = "#F59E0B"
            verdict_bg    = "rgba(245,158,11,0.07)"
            verdict_sub   = "條件尚未全部到位，可列入觀察"
        else:
            verdict_label = "🚫 暫時避開"
            verdict_color = "#E53935"
            verdict_bg    = "rgba(229,57,53,0.07)"
            verdict_sub   = "多項指標偏空，等反轉信號再說"

        st.markdown(f"""
        <div style="background:{verdict_bg};border:1.5px solid {verdict_color}33;border-radius:12px;
                    padding:1rem 1.25rem;margin-bottom:1rem">
            <div style="font-size:1.15rem;font-weight:700;color:{verdict_color}">{verdict_label}</div>
            <div style="font-size:0.78rem;color:#6B7280;margin-top:0.2rem">{verdict_sub}</div>
            <div style="font-size:0.72rem;color:#9CA3AF;margin-top:0.5rem">{'　·　'.join(reasons[:3])}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── 買入 / 出場 並排 ──────────────────────────────
        col_buy, col_sell = st.columns(2)

        # 理想進場價：RSI 偏高就等跌，否則現價附近
        if cur_rsi > 60:
            ideal_entry = price * 0.95
            entry_note  = "建議等回檔 5% 再進"
        elif cur_rsi > 50:
            ideal_entry = price * 0.97
            entry_note  = "可小量試水，等確認後加碼"
        else:
            ideal_entry = price
            entry_note  = "現價附近可直接進場"

        # Kelly 倉位
        win_p  = mc["win"] / 100
        loss_p = mc["loss"] / 100
        avg_w  = max(mc["p90"] / 100, 0.01)
        avg_l  = max(abs(mc["p10"]) / 100, 0.01)
        kelly  = max(0.0, min((win_p * avg_w - loss_p * avg_l) / avg_w, 0.30))
        half_kelly = kelly * 0.5
        pos_pct = round(half_kelly * 100)

        # 目標 & 止損
        target_price = mc["entry"] * np.exp(
            (mc["mu"] - 0.5 * mc["sigma"]**2) * hold_days
            + mc["sigma"] * np.sqrt(hold_days) * 1.28)
        stop_pct    = max(0.07, mc["sigma"] * np.sqrt(21) * 1.5)  # 1.5σ 月波動
        stop_price  = price * (1 - stop_pct)
        target_pct  = (target_price / price - 1) * 100
        stop_pct_show = stop_pct * 100

        with col_buy:
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.1rem">
                <div style="font-size:0.65rem;color:#9CA3AF;font-weight:700;letter-spacing:0.08em;
                            text-transform:uppercase;margin-bottom:0.6rem">買入策略</div>
                <div style="display:flex;justify-content:space-between;padding:0.5rem 0;
                            border-bottom:1px solid #F0F1F3">
                    <span style="font-size:0.8rem;color:#6B7280">理想進場價</span>
                    <span style="font-family:DM Mono,monospace;font-size:0.85rem;font-weight:600">
                        {cur} {ideal_entry:,.2f}</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.5rem 0;
                            border-bottom:1px solid #F0F1F3">
                    <span style="font-size:0.8rem;color:#6B7280">建議倉位</span>
                    <span style="font-family:DM Mono,monospace;font-size:0.85rem;font-weight:600">
                        {pos_pct}% 資金</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.5rem 0;
                            border-bottom:1px solid #F0F1F3">
                    <span style="font-size:0.8rem;color:#6B7280">分批策略</span>
                    <span style="font-size:0.8rem;font-weight:600">50% 進 → 跌5% 加50%</span>
                </div>
                <div style="font-size:0.72rem;color:#9CA3AF;margin-top:0.5rem">{entry_note}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_sell:
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.1rem">
                <div style="font-size:0.65rem;color:#9CA3AF;font-weight:700;letter-spacing:0.08em;
                            text-transform:uppercase;margin-bottom:0.6rem">出場策略</div>
                <div style="display:flex;justify-content:space-between;padding:0.5rem 0;
                            border-bottom:1px solid #F0F1F3">
                    <span style="font-size:0.8rem;color:#6B7280">目標賣出</span>
                    <span style="font-family:DM Mono,monospace;font-size:0.85rem;font-weight:600;color:#00A86B">
                        {cur} {target_price:,.2f} (+{target_pct:.1f}%)</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.5rem 0;
                            border-bottom:1px solid #F0F1F3">
                    <span style="font-size:0.8rem;color:#6B7280">停損點</span>
                    <span style="font-family:DM Mono,monospace;font-size:0.85rem;font-weight:600;color:#E53935">
                        {cur} {stop_price:,.2f} (-{stop_pct_show:.1f}%)</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.5rem 0;
                            border-bottom:1px solid #F0F1F3">
                    <span style="font-size:0.8rem;color:#6B7280">預計持有</span>
                    <span style="font-size:0.8rem;font-weight:600">{hold_choice}</span>
                </div>
                <div style="font-size:0.72rem;color:#9CA3AF;margin-top:0.5rem">
                    到達目標或觸碰停損任一先到先出場</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # ── 週度投資機會圖 ────────────────────────────────
        st.markdown("<div style='font-size:0.65rem;color:#9CA3AF;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.4rem'>最佳買入時機 — 歷年週度勝率 vs 成交量</div>", unsafe_allow_html=True)
        try:
            import plotly.graph_objects as go_w
            _lh = get_long_history(active)
            _df_w = _lh if not _lh.empty else df.copy()
            _df_w = _df_w.copy()
            _df_w.index = pd.to_datetime(_df_w.index)
            if hasattr(_df_w.index, "tz") and _df_w.index.tz is not None:
                _df_w.index = _df_w.index.tz_localize(None)
            _wk = _df_w.resample("W").agg({"Close": ["first", "last"], "Volume": "sum"})
            _wk.columns = ["wk_open", "wk_close", "wk_vol"]
            _wk["week_num"] = pd.to_datetime(_wk.index).isocalendar().week.astype(int)
            _wk["is_up"] = (_wk["wk_close"] > _wk["wk_open"]).astype(int)
            _by_wk = _wk.groupby("week_num").agg(
                win_rate=("is_up", "mean"),
                avg_vol=("wk_vol", "mean")
            ).reset_index()
            _by_wk = _by_wk[_by_wk["week_num"].between(1, 52)].reset_index(drop=True)
            _cur_wk = int(datetime.now().isocalendar()[1])
            _bar_clr = [
                "#3B82F6" if int(w) == _cur_wk else
                "#22C55E" if r > 0.55 else
                "#F87171" if r < 0.45 else "#FCD34D"
                for w, r in zip(_by_wk["week_num"], _by_wk["win_rate"])
            ]
            _fig_w = go_w.Figure()
            _fig_w.add_trace(go_w.Bar(
                x=_by_wk["week_num"],
                y=(_by_wk["win_rate"] * 100).round(1),
                name="歷史獲利機率",
                marker_color=_bar_clr,
                opacity=0.85,
                yaxis="y",
                hovertemplate="第%{x}週<br>獲利機率 %{y:.1f}%<extra></extra>",
            ))
            _vol_unit = 1000 if _by_wk["avg_vol"].max() > 5e6 else 1
            _vol_label = "千張" if _vol_unit == 1000 else "張"
            _fig_w.add_trace(go_w.Scatter(
                x=_by_wk["week_num"],
                y=(_by_wk["avg_vol"] / _vol_unit).round(0),
                name=f"平均週成交量({_vol_label})",
                mode="lines+markers",
                marker=dict(size=5, color="#6366F1", symbol="circle"),
                line=dict(color="#6366F1", width=1.8, dash="dot"),
                yaxis="y2",
                hovertemplate=f"第%{{x}}週<br>成交量 %{{y:,.0f}}{_vol_label}<extra></extra>",
            ))
            _fig_w.add_hline(y=50, line_width=1, line_dash="dash", line_color="#D1D5DB", yref="y",
                             annotation_text="50%", annotation_position="right",
                             annotation_font_size=9, annotation_font_color="#9CA3AF")
            _fig_w.update_layout(
                height=240,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=55, t=28, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.0,
                            bgcolor="rgba(0,0,0,0)", font_size=10, x=0),
                xaxis=dict(
                    title=None, gridcolor="#F5F5F5",
                    tickmode="array",
                    tickvals=[w for w in _by_wk["week_num"] if w % 4 == 0 or w == 1 or w == _cur_wk],
                    ticktext=[f"第{w}週{'⬅' if w==_cur_wk else ''}"
                              for w in _by_wk["week_num"] if w % 4 == 0 or w == 1 or w == _cur_wk],
                    tickfont=dict(size=10),
                ),
                yaxis=dict(
                    title=None, gridcolor="#F0F1F3",
                    range=[0, 105], ticksuffix="%", tickfont=dict(size=10),
                ),
                yaxis2=dict(
                    title=None, overlaying="y", side="right",
                    showgrid=False, tickfont=dict(size=10),
                ),
                hovermode="x unified",
                bargap=0.25,
            )
            st.plotly_chart(_fig_w, use_container_width=True)
        except Exception:
            pass

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        # ── 法人動向 ─────────────────────────────────────
        st.markdown("<div style='font-size:0.65rem;color:#9CA3AF;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.5rem'>法人動向（近5日）</div>", unsafe_allow_html=True)

        stock_id_raw = active.split(".")[0]
        inst_html = ""
        inst_ok   = False

        try:
            from screener import _fetch_institutional_data, _FOREIGN, _TRUST, _DEALER, _latest_net
            inst_raw = _fetch_institutional_data(stock_id_raw)
            if not inst_raw.empty:
                inst_ok = True
                def _net_row(label, names, color_pos, color_neg):
                    nets = _latest_net(inst_raw, names, days=5)
                    if nets.empty:
                        return ""
                    total = int(nets.sum())
                    arrow = "▲" if total >= 0 else "▼"
                    clr   = color_pos if total >= 0 else color_neg
                    action = "買超" if total >= 0 else "賣超"
                    return (f'<div style="display:flex;justify-content:space-between;padding:0.5rem 0;'
                            f'border-bottom:1px solid #F0F1F3">'
                            f'<span style="font-size:0.8rem;color:#6B7280">{label}</span>'
                            f'<span style="font-family:DM Mono,monospace;font-size:0.85rem;font-weight:600;color:{clr}">'
                            f'{arrow} {abs(total):,} 張 {action}</span></div>')

                inst_html = (
                    _net_row("外資", _FOREIGN, "#00A86B", "#E53935") +
                    _net_row("投信", _TRUST,   "#00A86B", "#E53935") +
                    _net_row("自營商", _DEALER, "#00A86B", "#E53935")
                )
        except Exception:
            pass

        if inst_ok and inst_html:
            # 三大法人合計方向
            try:
                all_nets = _latest_net(inst_raw, _FOREIGN | _TRUST | _DEALER, days=5)
                total_all = int(all_nets.sum())
                overall   = "法人合計 買超" if total_all >= 0 else "法人合計 賣超"
                ov_color  = "#00A86B" if total_all >= 0 else "#E53935"
                inst_html += (f'<div style="padding:0.6rem 0;font-size:0.78rem;font-weight:700;color:{ov_color}">'
                              f'{"▲" if total_all>=0 else "▼"} {overall} {abs(total_all):,} 張</div>')
            except Exception:
                pass
            st.markdown(f'<div class="card" style="padding:0.6rem 1.1rem">{inst_html}</div>', unsafe_allow_html=True)
        else:
            # 無法人資料時用成交量代替
            vol5  = float(vol_t.tail(5).mean()) if len(vol_t) >= 5  else 0
            vol20 = float(vol_t.tail(20).mean()) if len(vol_t) >= 20 else vol5
            ratio = vol5 / vol20 if vol20 else 1.0
            vol_signal = "量增" if ratio >= 1.2 else "量縮" if ratio <= 0.8 else "量平"
            vol_clr    = "#00A86B" if ratio >= 1.2 else "#9CA3AF"
            st.markdown(f"""
            <div class="card" style="padding:0.75rem 1.1rem;color:#9CA3AF;font-size:0.78rem">
                法人籌碼資料暫不可用（限台股）<br>
                <span style="color:{vol_clr};font-weight:600">近5日均量 vs 月均量：{ratio:.2f}x（{vol_signal}）</span>
            </div>""", unsafe_allow_html=True)

        # ── 免責聲明 ──────────────────────────────────────
        st.markdown("""
        <div style="font-size:0.65rem;color:#C4C9D4;margin-top:1rem;line-height:1.6">
        ⚠️ 以上分析由演算法自動生成，僅供參考，不構成投資建議。
        股市有風險，投資前請自行判斷。
        </div>""", unsafe_allow_html=True)

    except Exception as e:
        st.warning(f"分析計算錯誤：{e}")
