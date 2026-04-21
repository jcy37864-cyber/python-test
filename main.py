import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (오류 수정 및 기능 복구)")

    # 1. 설정 영역 (Key 값을 고유하게 부여하여 충돌 방지)
    with st.expander("⚙️ 분석 기준 설정 (클릭하여 열기)", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수 (S1~S4 기준 4)", min_value=1, value=4, key="final_sc_fix")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="final_tol_fix")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="final_mmc_fix")
        with col3:
            std_range = round(tol, 2)
            view_mode = st.radio("그래프 범위", ["표준(권장)", "수동 조절"], horizontal=True, key="final_mode_fix")
            view_limit = std_range if view_mode == "표준(권장)" else st.slider("범위 조절(±mm)", 0.1, 5.0, std_range, step=0.1, key="final_zoom_fix")

    # 2. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200, placeholder="숫자 데이터를 입력해주세요.")

    if not raw_input:
        st.info("💡 데이터를 입력하면 실시간으로 분석 그래프가 생성됩니다.")
        return

    # 3. 데이터 파싱 및 계산 (try-except 문법 오류 수정 완료)
    try:
        nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', raw_input)]
        
        if not nums:
            st.warning("데이터에서 숫자를 찾을 수 없습니다.")
            return

        results = []
        step = 1 + sc
        set_len = step * 3
        for i in range(len(nums) // set_len):
            base = i * set_len
            dia_p = nums[base : base + step]
            x_p = nums[base + step : base + step * 2]
            y_p = nums[base + step * 2 : base + step * 3]
            label = chr(65 + i) if i < 26 else f"P{i+1}"
            for s in range(sc):
                results.append({
                    "측정포인트": f"{label}_S{s+1}",
                    "도면_X": x_p[0], "도면_Y": y_p[0],
                    "측정_X": x_p[s+1], "측정_Y": y_p[s+1],
                    "지름_MMC": dia_p[s+1]
                })
        
        df = pd.DataFrame(results)
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # 4. 그래프 시각화 (이중 원 및 수치 표기)
        fig = go.Figure()
        
        r_blue = tol / 2
        fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue,
                      line=dict(color="RoyalBlue", width=2.5), fillcolor="rgba(65, 105, 225, 0.05)")
        
        max_total_tol = df['최종공차'].max()
        r_red = max_total_tol / 2
        display_r_red = min(r_red, view_limit * 0.98)
        fig.add_shape(type="circle", x0=-display_r_red, y0=-display_r_red, x1=display_r_red, y1=display_r_red,
                      line=dict(color="Red", width=2, dash="dot"))

        fig.add_annotation(x=r_blue*0.7, y=r_blue*0.7, text=f"기본: Ø{tol:.3f}", showarrow=False, font=dict(color="RoyalBlue"), bgcolor="white")
        if max_total_tol > tol:
            fig.add_annotation(x=display_r_red*0.7, y=-display_r_red*0.7, text=f"최종(MMC): Ø{max_total_tol:.3f}", showarrow=False, font=dict(color="Red"), bgcolor="white")

        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            vis = sub[(sub['편차_X'].abs() <= view_limit) & (sub['편차_Y'].abs() <= view_limit)]
            if not vis.empty:
                fig.add_trace(go.Scatter(x=vis['편차_X'], y=vis['편차_Y'], mode='markers+text', name=res,
                                         text=vis['측정포인트'], textposition="top center",
                                         marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))))

        fig.update_layout(width=700, height=700, xaxis=dict(range=[-view_limit, view_limit], zeroline=True), yaxis=dict(range=[-view_limit, view_limit], zeroline=True), plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        
        # 5. NG 스크롤 리스트 및 요약
        st.info(f"📌 **품질 규격 요약** | 도면: Ø{tol:.3f} / 최대합격(MMC): Ø{max_total_tol:.3f}")
        
        ng_list = df[df['판정'] == "❌ NG"]
        if not ng_list.empty:
            st.error(f"🚨 **규격 이탈(NG) 리스트**")
            ng_html = f"<div style='height: 180px
