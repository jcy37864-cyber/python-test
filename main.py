import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (양식 선택형)")

    # 1. 설정 및 양식 선택
    with st.expander("⚙️ 분석 기준 및 양식 설정", expanded=True):
        data_type = st.radio(
            "데이터 양식 선택", 
            ["유형 A (좌표 포함 - N, O, P 형태)", "유형 B (결과값만 - Nominal, 1.nmp 형태)"],
            horizontal=True
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수", min_value=1, value=4)
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")
        with col3:
            view_mode = st.radio("그래프 범위", ["자동", "수동"])

    # 2. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200)
    analyze_button = st.button("📊 데이터 분석 시작", type="primary", use_container_width=True)

    if analyze_button and raw_input:
        try:
            lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
            rows = []
            for line in lines:
                # 숫자 추출 (유형 B의 '1.nmp' 등 번호 오인식 방지를 위해 소수점 위주로 추출하거나 필터링)
                nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                if nums: rows.append(nums)

            results = []

            # --- 유형 A: 좌표 기반 로직 ---
            if "유형 A" in data_type:
                for i in range(0, len(rows) // 3 * 3, 3):
                    dia, x, y = rows[i], rows[i+1], rows[i+2]
                    label = f"P{(i//3)+1}"
                    for s in range(1, len(x)): # 첫 값은 도면값
                        results.append({
                            "측정포인트": f"{label}_S{s}",
                            "위치도": round(np.sqrt((x[s]-x[0])**2 + (y[s]-y[0])**2) * 2, 4),
                            "최종공차": round(tol + max(0, dia[s-1] - mmc_ref), 4),
                            "X_dev": x[s]-x[0], "Y_dev": y[s]-y[0]
                        })

            # --- 유형 B: 결과값 기반 로직 ---
            else:
                # 1, 2, 3, 4 같은 순번 줄은 제외 (소수점이 있는 줄만 선택)
                valid_rows = [r for r in rows if any(n != int(n) for n in r)]
                for i in range(0, len(valid_rows) // 3 * 3, 3):
                    pos_row, mmc_row = valid_rows[i], valid_rows[i+1]
                    label = f"P{(i//3)+1}"
                    samples = pos_row[-sc:]
                    bonuses = mmc_row[-sc:]
                    for s in range(sc):
                        p_val = samples[s]
                        results.append({
                            "측정포인트": f"{label}_S{s+1}",
                            "위치도": p_val,
                            "최종공차": round(tol + max(0, bonuses[s] - mmc_ref), 4),
                            "X_dev": (p_val/4) * (1 if s<2 else -1), # 시각화용 가상 좌표
                            "Y_dev": (p_val/4) * (1 if s%2==0 else -1)
                        })

            df = pd.DataFrame(results)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

            # 3. 시각화 및 결과 (공통)
            max_r = df['최종공차'].max() / 2
            v_limit = (max_r * 2.2) if view_mode == "자동" else st.slider("줌", 0.1, 5.0, 0.5)

            fig = go.Figure()
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="RoyalBlue", width=2))
            fig.add_shape(type="circle", x0=-max_r, y0=-max_r, x1=max_r, y1=max_r, line=dict(color="Red", width=2, dash="dot"))

            for res in ["✅ OK", "❌ NG"]:
                sub = df[df['판정'] == res]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['X_dev'], y=sub['Y_dev'], mode='markers+text', name=res, 
                                             text=sub['측정포인트'], marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c")))

            fig.update_layout(width=600, height=600, xaxis=dict(range=[-v_limit, v_limit]), yaxis=dict(range=[-v_limit, v_limit]))
            st.plotly_chart(fig)
            
            # NG 리스트 스크롤 박스 (이전 기능 유지)
            ngs = df[df['판정'] == "❌ NG"]
            if not ngs.empty:
                st.error("🚨 규격 이탈 상세")
                st.dataframe(ngs[['측정포인트', '위치도', '최종공차']])
            
            st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

        except Exception as e:
            st.error(f"선택하신 양식과 데이터가 맞지 않습니다: {e}")

if __name__ == "__main__":
    run_position_analysis()
