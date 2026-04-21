import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (오류 수정 및 통합 버전)")

    # 1. 설정 영역
    with st.expander("⚙️ 양식 및 기준 설정", expanded=True):
        data_type = st.radio(
            "데이터 양식 선택", 
            ["유형 A (좌표 포함 - N, O, P 형태)", "유형 B (결과값만 - Nominal, 1.nmp 형태)"],
            horizontal=True, key="sel_type"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수 (S1~S4 기준 4)", min_value=1, value=4)
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")
        with col3:
            view_mode = st.radio("그래프 범위", ["자동", "수동"])

    # 2. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200, placeholder="양식을 선택한 후 데이터를 붙여넣어 주세요.")
    analyze_button = st.button("📊 데이터 분석 시작", type="primary", use_container_width=True)

    if analyze_button and raw_input:
        try:
            lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
            results = []

            # --- [유형 A: 좌표 기반 로직 (기존 성공 버전 복구)] ---
            if "유형 A" in data_type:
                rows = []
                for line in lines:
                    # 모든 숫자를 다 가져옴 (정수 포함)
                    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                    if nums: rows.append(nums)
                
                # 3줄(지름, X, Y) 세트로 분석
                for i in range(0, len(rows) // 3 * 3, 3):
                    dia_vals, x_vals, y_vals = rows[i], rows[i+1], rows[i+2]
                    label = f"P{(i//3)+1}"
                    # 데이터 개수가 맞는지 확인 (안전장치)
                    if len(x_vals) > 1 and len(y_vals) > 1:
                        for s in range(1, len(x_vals)):
                            results.append({
                                "측정포인트": f"{label}_S{s}",
                                "위치도": round(np.sqrt((x_vals[s]-x_vals[0])**2 + (y_vals[s]-y_vals[0])**2) * 2, 4),
                                "최종공차": round(tol + max(0, (dia_vals[s-1] if (s-1) < len(dia_vals) else dia_vals[-1]) - mmc_ref), 4),
                                "X_dev": round(x_vals[s]-x_vals[0], 4), 
                                "Y_dev": round(y_vals[s]-y_vals[0], 4)
                            })

            # --- [유형 B: 결과값 기반 로직 (오인식 방지 강화)] ---
            else:
                valid_rows = []
                for line in lines:
                    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                    # 제목줄(1.nmp 2.nmp) 거르기: 소수점이 하나라도 있는 줄만 데이터로 인정
                    if nums and any(n != int(n) for n in nums):
                        valid_rows.append(nums)
                
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
                            "X_dev": round((p_val/4) * (1 if s<2 else -1), 4),
                            "Y_dev": round((p_val/4) * (1 if s%2==0 else -1), 4)
                        })

            if not results:
                st.error("❌ 데이터를 인식하지 못했습니다. 선택한 양식과 데이터가 일치하는지 확인해주세요.")
                return

            df = pd.DataFrame(results)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

            # 3. 시각화 및 결과 리포트
            max_r = df['최종공차'].max() / 2
            v_limit = (max_r * 2.2) if view_mode == "자동" else st.slider("줌 조절", 0.1, 5.0, 0.5)

            fig = go.Figure()
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="RoyalBlue", width=2.5))
            fig.add_shape(type="circle", x0=-max_r, y0=-max_r, x1=max_r, y1=max_r, line=dict(color="Red", width=2, dash="dot"))

            for res in ["✅ OK", "❌ NG"]:
                sub = df[df['판정'] == res]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['X_dev'], y=sub['Y_dev'], mode='markers+text', name=res, 
                                             text=sub['측정포인트'], textposition="top center",
                                             marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))))

            fig.update_layout(width=700, height=700, xaxis=dict(range=[-v_limit, v_limit], zeroline=True), 
                              yaxis=dict(range=[-v_limit, v_limit], zeroline=True), plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
            
            ngs = df[df['판정'] == "❌ NG"]
            if not ngs.empty:
                st.error(f"🚨 규격 이탈(NG) 리스트 ({len(ngs)}건)")
                st.dataframe(ngs[['측정포인트', '위치도', '최종공차', '판정']])
            else:
                st.success("✅ 모든 시료 합격!")
            
            st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

        except Exception as e:
            st.error(f"⚠️ 분석 실패: {e}\n데이터 복사 범위나 선택한 양식을 다시 확인해 주세요.")

if __name__ == "__main__":
    run_position_analysis()
