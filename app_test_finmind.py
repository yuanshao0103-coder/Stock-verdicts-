"""
app_test_finmind.py
FinMind 籌碼面串接測試：外資 / 投信連續 3 日買超判斷
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from FinMind.data import DataLoader

st.set_page_config(page_title="FinMind 籌碼測試", page_icon="🔬", layout="wide")
st.title("🔬 FinMind 籌碼面串接測試")
st.caption("驗證外資 / 投信連續 3 日買超判斷邏輯")


# ═══════════════════════════════════════════════════════════
# 核心函數
# ═══════════════════════════════════════════════════════════

def check_institutional_buy(stock_id: str) -> dict:
    """
    抓取台股法人買賣超資料，判斷是否符合：
      - 外資連續 3 日買超
      - 投信連續 3 日買超

    回傳 dict:
      raw_df              原始 DataFrame（供 debug）
      foreign_buy_3_days  bool
      trust_buy_3_days    bool
      foreign_df          外資最近 3 日淨買賣超（DataFrame）
      trust_df            投信最近 3 日淨買賣超（DataFrame）
      error               若有錯誤，回傳字串；否則 None
    """
    result = {
        "raw_df": pd.DataFrame(),
        "foreign_buy_3_days": False,
        "trust_buy_3_days": False,
        "foreign_df": pd.DataFrame(),
        "trust_df": pd.DataFrame(),
        "error": None,
    }

    # 1. 動態推算日期：往前 15 天確保涵蓋最近 3 個交易日
    end_date   = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=15)).strftime("%Y-%m-%d")

    # 2. 呼叫 FinMind API
    try:
        dl  = DataLoader()
        raw = dl.taiwan_stock_institutional_investors(
            stock_id   = stock_id,
            start_date = start_date,
            end_date   = end_date,
        )
    except Exception as e:
        result["error"] = f"FinMind API 呼叫失敗：{e}"
        return result

    if raw is None or raw.empty:
        result["error"] = f"查無資料（stock_id={stock_id}，{start_date} ~ {end_date}）"
        return result

    result["raw_df"] = raw.copy()

    # 3. 資料清洗：確認必要欄位存在
    required_cols = {"date", "name", "buy", "sell"}
    missing = required_cols - set(raw.columns)
    if missing:
        result["error"] = f"回傳欄位缺失：{missing}，實際欄位：{list(raw.columns)}"
        return result

    raw["date"] = pd.to_datetime(raw["date"])
    raw["buy"]  = pd.to_numeric(raw["buy"],  errors="coerce").fillna(0)
    raw["sell"] = pd.to_numeric(raw["sell"], errors="coerce").fillna(0)
    raw["net"]  = raw["buy"] - raw["sell"]

    # 4. 濾出外資與投信，計算每日淨買賣超
    # FinMind name 標籤（以實際 API 回傳為準，此處涵蓋常見變體）
    FOREIGN_NAMES = {
        "Foreign_Investor",
        "外資及陸資(不含外資自營商)",
        "外資及陸資",
        "外資",
    }
    TRUST_NAMES = {"Investment_Trust", "投信"}

    def _latest_3_net(df: pd.DataFrame, names: set) -> pd.DataFrame:
        """過濾指定法人、彙總每日淨買賣超，取最近 3 個交易日。"""
        subset = df[df["name"].isin(names)].copy()
        if subset.empty:
            return pd.DataFrame(columns=["date", "net"])
        daily = (
            subset.groupby("date", as_index=False)["net"]
            .sum()
            .sort_values("date", ascending=False)
            .head(3)
        )
        return daily.reset_index(drop=True)

    foreign_daily = _latest_3_net(raw, FOREIGN_NAMES)
    trust_daily   = _latest_3_net(raw, TRUST_NAMES)

    result["foreign_df"] = foreign_daily
    result["trust_df"]   = trust_daily

    # 5. 核心判斷：3 天資料都 > 0 才算連續買超
    if len(foreign_daily) >= 3:
        result["foreign_buy_3_days"] = bool((foreign_daily["net"] > 0).all())

    if len(trust_daily) >= 3:
        result["trust_buy_3_days"] = bool((trust_daily["net"] > 0).all())

    return result


# ═══════════════════════════════════════════════════════════
# Streamlit 測試介面
# ═══════════════════════════════════════════════════════════

col_input, col_btn = st.columns([3, 1])
with col_input:
    stock_id = st.text_input("股票代號", value="2330", placeholder="例：2330、2317",
                              label_visibility="collapsed")
with col_btn:
    run = st.button("🚀 執行查詢", use_container_width=True)

if run and stock_id.strip():
    sid = stock_id.strip()
    with st.spinner(f"正在抓取 {sid} 的法人買賣超資料…"):
        res = check_institutional_buy(sid)

    if res["error"]:
        st.error(f"❌ {res['error']}")
        st.stop()

    # ── 燈號結果 ──────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 判斷結果")

    c1, c2 = st.columns(2)
    with c1:
        emoji = "🟢" if res["foreign_buy_3_days"] else "🔴"
        label = "達成" if res["foreign_buy_3_days"] else "未達成"
        st.metric(label=f"{emoji} 外資連續 3 日買超", value=label)
        if not res["foreign_df"].empty:
            df_show = res["foreign_df"].copy()
            df_show["date"] = df_show["date"].dt.strftime("%Y-%m-%d")
            df_show.columns = ["日期", "淨買賣超（股）"]
            df_show["淨買賣超（股）"] = df_show["淨買賣超（股）"].apply(
                lambda x: f"+{x:,.0f}" if x > 0 else f"{x:,.0f}")
            st.dataframe(df_show, use_container_width=True, hide_index=True)
        else:
            st.caption("無外資資料")

    with c2:
        emoji = "🟢" if res["trust_buy_3_days"] else "🔴"
        label = "達成" if res["trust_buy_3_days"] else "未達成"
        st.metric(label=f"{emoji} 投信連續 3 日買超", value=label)
        if not res["trust_df"].empty:
            df_show = res["trust_df"].copy()
            df_show["date"] = df_show["date"].dt.strftime("%Y-%m-%d")
            df_show.columns = ["日期", "淨買賣超（股）"]
            df_show["淨買賣超（股）"] = df_show["淨買賣超（股）"].apply(
                lambda x: f"+{x:,.0f}" if x > 0 else f"{x:,.0f}")
            st.dataframe(df_show, use_container_width=True, hide_index=True)
        else:
            st.caption("無投信資料")

    # ── 原始 DataFrame ────────────────────────────────────
    st.markdown("---")
    with st.expander("🗃️ API 原始回傳資料（完整 DataFrame）", expanded=True):
        raw = res["raw_df"].copy()
        if "date" in raw.columns:
            raw["date"] = pd.to_datetime(raw["date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(raw, use_container_width=True)
        st.caption(f"共 {len(raw)} 筆 · 欄位：{list(raw.columns)}")
