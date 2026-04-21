import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.title("🎯 위치도 정밀 분석 시스템")

    # 1. 상태 유지를 위한 세션 변수 초기화
    if 'active_tab1' not in st.session_state: st.session_state.active_tab1 = False
    if 'active_tab2' not in st.session_state: st.session_state.active_tab2 = False

    tab1, tab2 = st.tabs(["📍 유형 A (좌표 방식)", "📊 유형 B (결과값 방식)"])

    # --- [탭 1: 유형 A - 좌표 데이터용] ---
    with tab1:
        st.subheader("좌표(X, Y) 기반 분석")
        c1, c2 = st.columns(2)
        with c1:
            tol_a = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="t_a")
            mmc_a = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="m_a")
        with c2:
            zoom_a = st.slider("🔍 그래프 줌 조절", 0.05, 5.0, 0.5, step=0.05, key="z_a")

        raw_a = st.text_area("N/O/P 데이터를 붙여넣으세요", height=150, key="i_a")
        if st.button("유형 A 분석 시작", type="primary", key="b_a"):
            st.session_state.active_tab1 = True
        
        if st.session_state.active_tab1 and raw_a:
            try:
                rows = [ [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)] for l in raw_a.split('\n') if re.findall(r'[-+]?\d*\.\d+|\d+', l) ]
                res_a = []
                for i in range(0, len(rows) // 3 * 3, 3):
                    dia, x, y = rows[i], rows[i+1], rows[i+2]
                    for s in range(1, len(x)):
                        bonus = max(0, (dia[s-1] if (s-1) < len(dia) else dia[-1]) - mmc_a)
                        res_a.append({
                            "측정포인트": f"P{(i//3)+1}_S{s}",
                            "위치도": round(np.sqrt((x[s]-x[0])**2 + (y[s]-y[0])**2) * 2, 4),
                            "최종공차": round(tol_a + bonus, 4),
                            "X_dev": x[s]-x[0], "Y_dev": y[s]-y[0]
                        })
                show_graph_and_table(res_a, tol_a, zoom_a)
            except Exception as e: st.error(f"유형 A 오류: {e}")

    # --- [탭 2: 유형 B - MMC공차 기입용] ---
    with tab2:
        st.subheader("MMC공차 행 포함 분석")
        c1, c2 = st.columns(2)
        with c1:
            tol_b = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="t_b")
            sc_b = st.number_input("샘플 수", min_value=1, value=4, key="s_b")
        with c2:
            zoom_b = st.slider("🔍 그래프 줌 조절", 0.05, 5.0, 0.5, step=0.05, key="z_b")

        raw_b = st.text_area("Nominal/MMC공차/Y 데이터를 붙여넣으세요", height=150, key="i_b")
        if st.button("유형 B 분석 시작", type="primary", key="b_b"):
            st.session_state.active_tab2 = True
        
        if st.session_state.active_tab2 and raw_b:
            try:
                v_rows = [ [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)] for l in raw_b.split('\n') if any(n != int(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)) ]
                res_b = []
                for i in range(0, len(v_rows) // 3 * 3, 3):
                    pos, mmc = v_rows[i][-sc_b:], v_rows[i+1][-sc_b:]
                    for s in range(sc_b):
                        res_b.append({
                            "측정포인트": f"P{(i//3)+1}_S{s+1}",
                            "위치도": pos[s],
                            "최종공차": round(tol_b + mmc[s], 4),
                            "X_dev": (pos[s]/4) * (1 if s < sc_b/2 else -1), "Y_dev": 0
                        })
                show_graph_and_table(res_b, tol_b, zoom_b)
            except Exception as e: st.error(f"유형 B 오류: {e}")

def show_graph_and_table(results, base_tol, zoom):
    if not results: return
    df = pd.DataFrame(results)
    df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
    
    fig = go.Figure()
    m_tol = df['최종공차'].max()
    fig.add_shape(type="circle", x0=-base_tol/2, y0=-base_tol/2, x1=base_tol/2, y1=base_tol/2, line=dict(color="RoyalBlue", width=2))
    fig.add_shape(type="circle", x0=-m_tol/2, y0=-m_tol/2, x1=m_tol/2, y1=m_tol/2, line=dict(color="Red", width=1.5, dash="dot"))

    for res in ["✅ OK", "❌ NG"]:
        sub = df[df['판정'] == res]
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=sub['X_dev'], y=sub['Y_dev'], 
                mode='markers+text', name=res, 
                text=sub['측정포인트'], textposition="top center",
                marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c")
            ))

    fig.update_layout(width=600, height=600, xaxis=dict(range=[-zoom, zoom]), yaxis=dict(range=[-zoom, zoom]), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

if __name__ == "__main__":
    run_position_analysis()
