import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 초기 설정
st.set_page_config(page_title="Quality Analysis Hybrid v2.2", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
        .ng-box { height: 180px; overflow-y: auto; border: 1px solid #ff4b4b; padding: 12px; border-radius: 5px; background-color: #fff5f5; }
        </style>
    """, unsafe_allow_html=True)

def run_integrated_analysis():
    set_style()
    st.title("🎯 위치도 정밀 분석 시스템 (Hybrid)")

    with st.sidebar:
        st.header("⚙️ 시스템 설정")
        mode = st.radio("데이터 성적서 유형", ["유형 B (가로 데이터)", "유형 A (3줄 세트)"])
        st.divider()
        sc = st.number_input("샘플(캐비티) 수", min_value=1, value=4)
        tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        if mode == "유형 A (3줄 세트)":
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")
        view_mode = st.radio("그래프 범위", ["자동(권장)", "수동 조절"], horizontal=True)
        if view_mode == "수동 조절":
            view_limit = st.slider("줌 조절 (±mm)", 0.1, 5.0, 0.5, step=0.1)

    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=250)
    analyze_button = st.button("📊 데이터 분석 시작", type="primary")

    if analyze_button and raw_input:
        try:
            results = []
            # --- 유형 B 로직 ---
            if mode == "유형 B (가로 데이터)":
                lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i+3 >= len(lines): break
                    try:
                        nom_x = float(re.sub(r'[^0-9\.\-]', '', lines[i+2][0]))
                        nom_y = float(re.sub(r'[^0-9\.\-]', '', lines[i+3][0]))
                        p_label = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                        for s in range(sc):
                            idx = -(sc - s)
                            ax = float(re.sub(r'[^0-9\.\-]', '', lines[i+2][idx]))
                            ay = float(re.sub(r'[^0-9\.\-]', '', lines[i+3][idx]))
                            dv = float(re.sub(r'[^0-9\.\-]', '', lines[i+1][idx])) if len(lines[i+1]) > abs(idx) else 0.35
                            results.append({"측정포인트": f"{p_label}_S{s+1}", "도면_X": nom_x, "도면_Y": nom_y, "측정_X": ax, "측정_Y": ay, "지름_MMC": dv})
                    except: continue
            # --- 유형 A 로직 ---
            else:
                lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
                rows = [ [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)] for l in lines ]
                rows = [ [n if abs(n) < 150 else n % 100 for n in r] for r in rows if r ]
                for i in range(0, len(rows) // 3 * 3, 3):
                    d_v, x_v, y_v = rows[i], rows[i+1], rows[i+2]
                    for s in range(1, len(x_v)):
                        results.append({"측정포인트": f"P{(i//3)+1}_S{s}", "도면_X": x_v[0], "도면_Y": y_v[0], "측정_X": x_v[s], "측정_Y": y_v[s], "지름_MMC": d_v[s-1] if (s-1) < len(d_v) else d_v[-1]})

            df = pd.DataFrame(results)
            df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
            df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
            df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
            df['보너스'] = (df['지름_MMC'] - (mmc_ref if mode=="유형 A (3줄 세트)" else 0.35)).clip(lower=0).round(4)
            df['최종공차'] = (tol + df['보너스']).round(4)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

            # 시각화
            max_tol = df['최종공차'].max()
            v_lim = round((max_tol / 2) * 1.5, 2) if view_mode == "자동(권장)" else view_limit
            fig = go.Figure()
            fig.add_shape(type="circle", x0=-tol/2, y0=-
