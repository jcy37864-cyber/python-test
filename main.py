import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.title("🎯 위치도 정밀 분석 시스템")
    
    # 탭으로 명확하게 분리 (유형별 독립 공간)
    tab1, tab2 = st.tabs(["📍 유형 A (좌표 포함 양식)", "📊 유형 B (결과값 기입 양식)"])

    # --- [탭 1: 유형 A - 좌표 포함 데이터] ---
    with tab1:
        st.subheader("좌표(X, Y) 기반 정밀 분석")
        col1, col2 = st.columns(2)
        with col1:
            tol_a = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_a")
            mmc_ref_a = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="mmc_a")
        with col2:
            zoom_a = st.slider("그래프 줌 조절", 0.05, 5.0, 0.5, step=0.05, key="zoom_a")

        raw_a = st.text_area("N/O/P 좌표 데이터를 붙여넣으세요", height=200, key="input_a")
        
        if st.button("유형 A 분석 실행", type="primary"):
            try:
                rows = [ [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)] for l in raw_a.split('\n') if re.findall(r'[-+]?\d*\.\d+|\d+', l) ]
                results = []
                for i in range(0, len(rows) // 3 * 3, 3):
                    dia, x, y = rows[i], rows[i+1], rows[i+2]
                    for s in range(1, len(x)):
                        bonus = max(0, (dia[s-1] if (s-1) < len(dia) else dia[-1]) - mmc_ref_a)
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s}",
                            "위치도": round(np.sqrt((x[s]-x[0])**2 + (y[s]-y[0])**2) * 2, 4),
                            "최종공차": round(tol_a + bonus, 4),
                            "X_dev": x[s]-x[0], "Y_dev": y[s]-y[0]
                        })
                show_result(results, tol_a, zoom_a)
            except Exception as e: st.error(f"유형 A 데이터 파싱 오류: {e}")

    # --- [탭 2: 유형 B - MMC공차 기입 데이터] ---
    with tab2:
        st.subheader("MMC공차 행 포함 데이터 분석")
        col1, col2 = st.columns(2)
        with col1:
            tol_b = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_b")
            sc_b = st.number_input("샘플 수(n.mp)", min_value=1, value=4, key="sc_b")
        with col2:
            zoom_b = st.slider("그래프 줌 조절", 0.05, 5.0, 0.5, step=0.05, key="zoom_b")

        raw_b = st.text_area("Nominal/MMC공차/Y 행 데이터를 붙여넣으세요", height=200, key="input_b")
        
        if st.button("유형 B 분석 실행", type="primary"):
            try:
                # 숫자 데이터만 추출 (순번 제외)
                valid_rows = []
                for l in raw_b.split('\n'):
                    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)]
                    if nums and any(n != int(n) for n in nums): valid_rows.append(nums)
                
                results = []
                for i in range(0, len(valid_rows) // 3 * 3, 3):
                    pos_vals, mmc_vals = valid_rows[i][-sc_b:], valid_rows[i+1][-sc_b:]
                    for s in range(sc_b):
                        # 유형 B는 표에 적힌 MMC공차를 그대로 보너스로 사용
                        bonus = mmc_vals[s]
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s+1}",
                            "위치도": pos_vals[s],
                            "최종공차": round(tol_b + bonus, 4),
                            # 유형 B는 좌표가 없으므로 가상 X축 시각화
                            "X_dev": (pos_vals[s]/4) * (1 if s<sc_b/2 else -1),
                            "Y_dev": 0 # 일직선상 분포로 시각화 개선
                        })
                show_result(results, tol_b, zoom_b)
            except Exception as e: st.error(f"유형 B 데이터 파싱 오류: {e}")

def show_result(results, base_tol, zoom_limit):
    if not results: return
    df = pd.DataFrame(results)
    df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
    
    # 그래프 그리기
    fig = go.Figure()
    max_tol = df['최종공차'].max()
    
    # 공차 범위 시각화
    fig.add_shape(type="circle", x0=-base_tol/2, y0=-base_tol/2, x1=base_tol/2, y1=base_tol/2, line=dict(color="RoyalBlue", width=2))
    fig.add_shape(type="circle", x0=-max_tol/2, y0=-max_tol/2, x1=max_tol/2, y1=max_tol/2, line=dict(color="Red", width=1.5, dash="dot"))

    for res in ["✅ OK", "❌ NG"]:
        sub = df[df['판정'] == res]
        if not sub.empty:
            fig.add_trace(go.Scatter(x=sub['X_dev'], y=sub['Y_dev'], mode='markers+text', name=res, 
                                     text=sub['측정포인트'], marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c")))

    fig.update_layout(width=600, height=600, xaxis=dict(range=[-zoom_limit, zoom_limit]), yaxis=dict(range=[-zoom_limit, zoom_limit]))
    st.plotly_chart(fig)
    st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

if __name__ == "__main__":
    run_position_analysis()
