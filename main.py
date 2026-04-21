import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (데이터 정제 기능 강화)")

    # 1. 설정 영역 (Key 값을 고유하게 설정하여 충돌 방지)
    with st.expander("⚙️ 분석 기준 설정", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수 (S1~S4 기준 4)", min_value=1, value=4, key="final_sc")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="final_tol")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="final_mmc")
        with col3:
            std_range = round(tol, 2)
            view_mode = st.radio("그래프 범위", ["표준(권장)", "수동 조절"], horizontal=True, key="final_mode")
            view_limit = std_range if view_mode == "표준(권장)" else st.slider("범위 조절", 0.1, 5.0, std_range, step=0.1, key="final_zoom")

    # 2. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200, placeholder="이미지의 표 데이터를 그대로 복사해서 넣어주세요.")

    if not raw_input:
        st.info("💡 데이터를 입력하면 분석이 시작됩니다.")
        return

    # [핵심] 443 방지 로직: 줄 단위로 정제하여 좌표가 위치도로 섞이지 않게 함
    def advanced_parse(text, sample_count):
        # 숫자가 아닌 문자(포인트명 등)는 제거하고 숫자만 추출하되, 행 구조 유지 시도
        lines = text.strip().split('\n')
        clean_data = []
        for line in lines:
            nums = re.findall(r'[-+]?\d*\.\d+|\d+', line)
            if nums:
                clean_data.extend([float(n) for n in nums])
        
        if not clean_data: return None
        
        results = []
        step = 1 + sample_count # 도면값1 + 샘플수
        set_len = step * 3      # Ø그룹 + X그룹 + Y그룹
        
        for i in range(len(clean_data) // set_len):
            base = i * set_len
            try:
                # 데이터 매칭 구조 강제 지정
                dia_vals = clean_data[base : base + step]
                x_vals = clean_data[base + step : base + step * 2]
                y_vals = clean_data[base + step * 2 : base + step * 3]
                
                label = chr(65 + i) if i < 26 else f"P{i+1}"
                for s in range(sample_count):
                    results.append({
                        "측정포인트": f"{label}_S{s+1}",
                        "도면_X": x_vals[0], "도면_Y": y_vals[0],
                        "측정_X": x_vals[s+1], "측정_Y": y_vals[s+1],
                        "지름_MMC": dia_vals[s+1]
                    })
            except IndexError:
                break
        return results

    data = advanced_parse(raw_input, sc)

    if data:
        df = pd.DataFrame(data)
        # 위치도 계산 공식 (편차의 2배)
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- 3. 그래프 시각화 (모든 기능 포함) ---
        fig = go.Figure()
        
        # 원 그리기 로직 (파란원, 빨간원)
        r_blue = tol / 2
        fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue,
                      line=dict(color="RoyalBlue", width=2.5), fillcolor="rgba(65, 105, 225, 0.05)")
        
        max_total_tol = df['최종공차'].max()
        r_red = max_total_tol / 2
        display_r_red = min(r_red, view_limit * 0.98)
        fig.add_shape(type="circle", x0=-display_r_red, y0=-display_r_red, x1=display_r_red, y1=display_r_red,
                      line=dict(color="Red", width=2, dash="dot"))

        # 수치 텍스트 유지
        fig.add_annotation(x=r_blue*0.7, y=r_blue*0.7, text=f"기본: Ø{tol:.3f}", showarrow=False, font=dict(color="RoyalBlue"), bgcolor="white")
        if max_total_tol > tol:
            fig.add_annotation(x=display_r_red*0.7, y=-display_r_red*0.7, text=f"최종(MMC): Ø{max_total_tol:.3f}", showarrow=False, font=dict(color="Red"), bgcolor="white")

        # 데이터 타점
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            vis = sub[(sub['편차_X'].abs() <= view_limit) & (sub['편차_Y'].abs() <= view_limit)]
            if not vis.empty:
                fig.add_trace(go.Scatter(x=vis['편차_X'], y=vis['편차_Y'], mode='markers+text', name=res,
                                         text=vis['측정포인트'], textposition="top center",
                                         marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))))

        fig.update_layout(width=700, height=700, xaxis=dict(range=[-view_limit, view_limit], zeroline=True), yaxis=dict(range=[-view_limit, view_limit], zeroline=True), plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    run_position_analysis()
