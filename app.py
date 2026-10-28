import pandas as pd
import streamlit as st

st.set_page_config(page_title="膳择智策", page_icon="🍱")
st.title("🍱 膳择智策｜校园食堂膳食推荐助手")

@st.cache_data
def load_data(path="food.csv"):
    try:
        # 尝试正常读取
        df = pd.read_csv(path, encoding="gbk")
        # 如果发现只有一列（WPS经常干这事），代码自动按逗号切开
        if len(df.columns) == 1:
            df = df.iloc[:, 0].str.split(',', expand=True)
            df.columns = ["窗口", "菜品", "价格", "标签"]
        df["价格"] = pd.to_numeric(df["价格"])
        return df
    except Exception:
        # 如果 gbk 报错，换 utf-8 再试一次
        df = pd.read_csv(path, encoding="utf-8-sig")
        if len(df.columns) == 1:
            df = df.iloc[:, 0].str.split(',', expand=True)
            df.columns = ["窗口", "菜品", "价格", "标签"]
        df["价格"] = pd.to_numeric(df["价格"])
        return df

try:
    df = load_data()
except Exception as e:
    st.error(f"读取 food.csv 失败。错误信息: {e}")
    st.stop()

def hard_filter(df, taboo):
    result = df.copy()
    t = taboo.replace(" ", "")
    if any(k in t for k in ["不吃辣", "不要辣", "忌辣"]):
        result = result[~result["标签"].fillna("").str.contains("辣|辛辣", regex=True)]
    if any(k in t for k in ["不吃油", "低油", "少油"]):
        result = result[~result["标签"].fillna("").str.contains("高油", regex=False)]
    return result

def local_fallback(candidates, budget):
    if candidates.empty:
        return [], "当前条件下没有可组合的菜品。"
    mains = candidates[candidates["标签"].fillna("").str.contains("主食", regex=False)]
    others = candidates[~candidates["标签"].fillna("").str.contains("主食", regex=False)]
    if mains.empty:
        mains = candidates.iloc[[0]]
    plans = []
    for _, m in mains.iterrows():
        for i in range(len(others)):
            for j in range(i + 1, len(others)):
                a, b = others.iloc[i], others.iloc[j]
                total = m["价格"] + a["价格"] + b["价格"]
                if total <= budget:
                    plans.append((total, [m, a, b]))
    plans.sort(key=lambda x: x[0], reverse=True)
    plans = plans[:3]
    if not plans:
        return [], "当前预算内没有足够的菜品组合，建议适当提高预算或放宽忌口。"
    lines = []
    for idx, (total, items) in enumerate(plans, 1):
        names = "、".join(f"{r['菜品']}（{r['价格']}元，{r['窗口']}）" for r in items)
        lines.append(f"**套餐{idx}**：{names}｜总价 {total}元")
    return plans, "\n\n".join(lines)

budget = st.number_input("💰 预算（元）", min_value=1, value=12)
taboo = st.text_input("📝 忌口 / 需求（例：不吃辣、减脂、低油）", "")

candidates = hard_filter(df, taboo)
st.caption(f"硬过滤后候选菜品：{len(candidates)} 道")

if st.button("✨ 生成推荐套餐"):
    if candidates.empty:
        st.warning("当前忌口条件下没有符合条件的菜品，请放宽条件。")
    else:
        st.subheader("📋 推荐结果")
        _, fallback_text = local_fallback(candidates, budget)
        st.markdown(fallback_text)
        st.info("当前为本地规则推荐模式，总价已校验，绝不超预算。")

st.divider()
st.subheader("📖 食堂菜品库预览")
st.dataframe(df, use_container_width=True)