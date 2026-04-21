import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.title("🎯 위치도 정밀 분석 시스템")

    # 1. 버튼 클릭 상태 유지를 위한 세션 초기화
    if 'tab1_active' not in st.session_state: st.session_state.tab1_active = False
    if 'tab2_active' not in st.session_state: st.session_state.tab2_active = False

    tab1, tab2 = st.tabs(["📍 유형 A (좌표 포함)", "📊 유형 B (결과값 기입)"])

    # --- [탭 1: 유형 A] ---
    with tab1:
        st.subheader("좌표(X, Y) 기반 분석")
        col1, col2 = st.columns(2)
        with col1:
            tol_a = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="ta")
            mmc_a = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="ma")
        with col2:
            zoom_a = st.slider("🔍 그래프 줌 조절", 0.05, 5.0, 0.5, step=0.05, key="za")

        raw_a = st.text_area("데이터를 붙여넣으세요", height=150, key="ia")
        if st.button("유형 A 분석 시작", type="primary", key="ba"):
            st.session_state.tab1_active = True # 상태 저장
        
        if st.session_state.tab1_active and raw_a:
            try:
                rows = [ [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)] for l in raw_a.split('\n') if re.findall(r'[-+]?\d*\.\d+|\d+', l) ]
                results = []
                for i in range(0, len(rows) // 3 * 3, 3):
                    dia, x, y = rows[i], rows[i+1], rows[i+2]
                    for s in range(1, len(x)):
                        bonus = max(0, (dia[s-1] if (s-1) < len(dia) else dia[-1]) - mmc_a)
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s}",
                            "위치도": round(np.sqrt((x[s]-x[0])**2 + (y[s]-y[0])**2) * 2, 4),
                            "최종공차": round(tol_a + bonus, 4),
                            "X_dev": x[s]-x[0], "Y_dev": y[s]-y[0]
                        })
                show_result(results, tol_a, zoom_a)
            except Exception as e: st.error(f"오류: {e}")

    # --- [탭 2: 유형 B] ---
    with tab2:
        st.subheader("MMC공차 행 포함 분석")
        col1, col2 = st.columns(2)
        with col1:
            tol_b = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tb")
            sc_b = st.number_input("샘플 수", min_value=1, value=4, key="sb")
        with col2:
            zoom_b = st.slider("🔍 그래프 줌 조절", 0.05, 5.0, 0.5, step=0.05, key="zb")

        raw_b = st.text_area("데이터를 붙여넣으세요", height=150, key="ib")
        if st.button("유형 B 분석 시작", type="primary", key="bb"):
            st.session_state.tab2_active = True # 상태 저장
        
        if st.session_state.tab2_active and raw_b:
            try:
                valid_rows = [ [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)] for l in raw_b.split('\n') if any(n != int(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)) ]
                results = []
                for i in range(0, len(valid_rows) // 3 * 3, 3):
                    pos_vals, mmc_vals = valid_rows[i][-sc_b:], valid_rows[i+1][-sc_b:]
                    for s in range(sc_b):
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s+1}",
                            "위치도": pos_vals[s],
                            "최종공차": round(tol_b + mmc_vals[s], 4),
                            "X_dev": (pos_vals[s]/4) * (1 if s<sc_b/2 else -1), "Y_dev": 0
                        })
                show_result(results, tol_b, zoom_b)
            except Exception as e: st.error(f"오류: {e}")

def show_result(results, base_tol, zoom):
    if not results: return
    df = pd.DataFrame(results)
    df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
    
    fig = go.Figure()
    max_tol = df['최종공차'].max()
    fig.add_shape(type="circle", x0=-base_tol/2, y0=-base_tol/2, x1=base_tol/2, y1=base_tol/2, line=dict(color="RoyalBlue", width=2))
    fig.add_shape(type="circle", x0=-max_tol/2, y0=-max_tol/2, x1=max_tol/2, y1=max_tol/2, line=dict(color="Red", width=1.5, dash="dot"))

    for res in ["✅ OK", "❌ NG"]:
        sub = df[df['판정'] == res]
        if not sub.empty:
            fig.add_trace(go.Scatter(x=sub['X_dev'], y=sub['Y_dev'], mode='markers
