import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 페이지 설정 및 스타일
st.set_page_config(page_title="Quality Analysis Hybrid v2.3", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #007bff; color: white; }
        .ng-box { height: 180px; overflow-y: auto; border: 1px solid #ff4b4b; padding: 12px; border-radius: 5px; background-color: #fff5f5; }
        </style>
    """, unsafe_allow_html=True)

def run_integrated_analysis():
    set_style()
    st.title("🎯 위치도 정밀 분석 시스템 (Hybrid)")

    # -------------------------------------------
    # [설정] 사이드바 영역
    # -------------------------------------------
    with st.sidebar:
        st.header("⚙️ 설정")
        mode = st.radio("성적서 유형 선택", ["유형 B (가로형)", "유형 A (3줄 세트)"])
        st.divider()
        sc = st.number_input("샘플(캐비티) 수", min_value=1, value=4)
        tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        
        mmc_val = 0.350 # 기본값
        if mode == "유형 A (3줄 세트)":
            mmc_val = st.number_input("MMC 기준치", value=0.060, format="%.3f")
        
        view_mode = st.radio("그래프 범위", ["자동", "수동"], horizontal=True)
        v_limit_input = 0.5
        if view_mode == "수동":
            v_limit_input = st.slider("줌 (±mm)", 0.1, 5.0, 0.5, step=0.1)

    # -------------------------------------------
    # [입력] 데이터 텍스트 영역
    # -------------------------------------------
    raw_input = st.text_area("성적서 내용을 붙여넣으세요", height=250)
    analyze_btn = st.button("📊 분석 시작")

    if analyze_btn and raw_input:
        try:
            results = []
            
            # --- 유형 B: 가로형 데이터 파싱 (황금 인덱스 복구) ---
            if mode == "유형 B (가로형)":
                lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i + 3 >= len(lines): break
                    try:
                        # 도면값(Nominal) 추출
                        nom_x = float(re.sub(r'[^0-9\.\-]', '', lines[i+2][0]))
                        nom_y = float(re.sub(r'[^0-9\.\-]', '', lines[i+3][0]))
                        label = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                        
                        for s in range(sc):
                            idx = -(sc - s) # 뒤에서부터 샘플 데이터 추출
                            act_x = float(re.sub(r'[^0-9\.\-]', '', lines[i+2][idx]))
                            act_y = float(re.sub(r'[^0-9\.\-]', '', lines[i+3][idx]))
                            dia_val = float(re.sub(r'[^0-9\.\-]', '', lines[i+1][idx])) if len(lines[i+1]) > abs(idx) else 0.35
                            
                            results.append({
                                "ID": f"{label}_S{s+1}",
                                "NOM_X": nom_x, "NOM_Y": nom_y,
                                "ACT_X": act_x, "ACT_Y": act_y,
                                "DIA": dia_val
                            })
                    except: continue

            # --- 유형 A: 3줄 세트 파싱 ---
            else:
                lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
                rows = []
                for l in lines:
                    n = [float(val) for val in re.findall(r'[-+]?\d*\.\d+|\d+', l)]
                    n = [val if abs(val) < 150 else val % 100 for val in n]
                    if n: rows.append(n)
                
                for i in range(0, len(rows) // 3 * 3, 3):
                    d_line, x_line, y_line = rows[i], rows[i+1], rows[i+2]
                    for s in range(1, len(x_line)):
                        results.append({
                            "ID": f"P{(i//3)+1}_S{s}",
                            "NOM_X": x_line[0], "NOM_Y": y_line[0],
                            "ACT_X": x_line[s], "ACT_Y": y_line[s],
                            "DIA": d_line[s-1] if (s-1) < len(d_line) else d_line[-1]
                        })

            # -------------------------------------------
            # 데이터 가공 및 분석
            # -------------------------------------------
            df = pd.DataFrame(results)
            df['DX'] = (df['ACT_X'] - df['NOM_X']).round(4)
            df['DY'] = (df['ACT_Y'] - df['NOM_Y']).round(4)
            df['POS'] = (np.sqrt(df['DX']**2 + df['DY']**2) * 2).round(4)
            df['BONUS'] = (df['DIA'] - mmc_val).clip(lower=0).round(4)
            df['LIMIT'] = (tol + df['BONUS']).round(4)
            df['RESULT'] = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            # 그래프 범위 계산
            max_limit = df['LIMIT'].max()
            v_lim = round((max_limit / 2) * 1.5, 2) if view_mode == "자동" else v_limit_input

            # -------------------------------------------
            # 시각화 (Plotly)
            # -------------------------------------------
            fig = go.Figure()
            
            # 기본 공차원 및 최대 공차원
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, 
                          line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.05)")
            fig.add_shape(type="circle", x0=-max_limit/2, y0=-max_limit/2, x1=max_limit/2, y1=max_limit/2, 
                          line=dict(color="Red", width=1.5, dash="dot"))

            # 포인트 타점
            for res, color in zip(["✅ OK", "❌ NG"], ["#2ecc71", "#e74c3c"]):
                pdf = df[df['RESULT'] == res]
                if not pdf.empty:
                    fig.add_trace(go.Scatter(x=pdf['DX'], y=pdf['DY'], mode='markers+text', name=res,
                                             text=pdf['ID'], textposition="top center",
                                             marker=dict(size=10, color=color, line=dict(width=1, color="white"))))

            fig.update_layout(width=70
