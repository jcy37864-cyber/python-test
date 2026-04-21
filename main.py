import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    """
    이 함수 전체를 복사해서 기존 앱의 메뉴 분기점(if menu == "위치도")에 넣으세요.
    """
    st.subheader("🎯 위치도 정밀 분석 (MMC & 표준 범위)")

    # 1. 분석에 필요한 기준 설정 (기존 앱의 사이드바와 겹치지 않게 본문에 배치하거나 선택 가능)
    with st.expander("⚙️ 분석 기준 설정 (클릭하여 열기)", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수", min_value=1, value=4)
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")
            std_range = round(tol, 2)
        with col3:
            view_mode = st.radio("보기 범위", ["표준(권장)", "수동 조절"], horizontal=True)
            if view_mode == "표준(권장)":
                view_limit = std_range
            else:
                view_limit = st.slider("범위 조절", 0.1, 5.0, std_range, step=0.1)

    # 2. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=150, help="지름, X, Y 순서의 데이터를 인식합니다.")

    if raw_input:
        # [내부 함수] 데이터 파싱
        def parse_data(text, sample_count):
            nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', text)]
            if not nums: return None
            res = []
            step = 1 + sample_count
            set_len = step * 3
            for i in range(len(nums) // set_len):
                base = i * set_len
                dia_p = nums[base : base + step]
                x_p = nums[base + step : base + step * 2]
                y_p = nums[base + step * 2 : base + step * 3]
                label = chr(65 + i) if i < 26 else f"P{i+1}"
                for s in range(sample_count):
                    res.append({
                        "측정포인트": f"{label}_S{s+1}",
                        "도면_X": x_p[0], "도면_Y": y_p[0],
                        "측정_X": x_p[s+1], "측정_Y": y_p[s+1],
                        "지름_MMC": dia_p[s+1]
                    })
            return res

        data = parse_data(raw_input, sc)
        if data:
            df = pd.DataFrame(data)
            # 계산 로직
            df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
            df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
            df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
            df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
            df['최종공차'] = (tol + df['보너스']).round(4)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

            # --- 3. 그래프 시각화 ---
            fig = go.Figure()
            
            # 파란 원 (기본)
            r_blue = tol / 2
            fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue,
                          line=dict(color="RoyalBlue", width=2.5), fillcolor="rgba(65, 105, 225, 0.05)")
            
            # 빨간 원 (최종)
            max_total_tol = df['최종공차'].max()
            r_red = max_total_tol / 2
            display_r_red = min(r_red, view_limit * 0.98)
            fig.add_shape(type="circle", x0=-display_r_red, y0=-display_r_red, x1=display_r_red, y1=display_r_red,
                          line=dict(color="Red", width=2, dash="dot"))

            # 그래프 내 수치 텍스트 (누락 없음)
            fig.add_annotation(x=r_blue*0.7, y=r_blue*0.7, text=f"기본: Ø{tol:.3f}", showarrow=False, font=dict(color="RoyalBlue"), bgcolor="white")
            if max_total_tol > tol:
                fig.add_annotation(x=display_r_red*0.7, y=-display_r_red*0.7, text=f"최종(MMC): Ø{max_total_tol:.3f}", showarrow=False, font=dict(color="Red"), bgcolor="white")

            # 데이터 점
            for res in ["✅ OK", "❌ NG"]:
                sub = df[df['판정'] == res]
                vis = sub[(sub['편차_X'].abs() <= view_limit) & (sub['편차_Y'].abs() <= view_limit)]
                if not vis.empty:
                    fig.add_trace(go.Scatter(x=vis['편차_X'], y=vis['편차_Y'], mode='markers+text', name=res,
                                             text=vis['측정포인트'], textposition="top center",
                                             marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))))

            fig.update_layout(width=700, height=700, xaxis=dict(range=[-view_limit, view_limit], zeroline=True), yaxis=dict(range=[-view_limit, view_limit], zeroline=True), plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
            
            # --- 4. 상세 안내 (스크롤 및 요약 유지) ---
            st.info(f"📌 **품질 규격 요약** | 도면: Ø{tol:.3f} / 최대합격(MMC): Ø{max_total_tol:.3f}")
            
            ng_list = df[df['판정'] == "❌ NG"]
            if not ng_list.empty:
                st.error(f"🚨 **규격 이탈(NG) 리스트 (총 {len(ng_list)}건)**")
                ng_html = "<div style='height: 180px; overflow-y: auto; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; background-color: #fff5f5;'>"
                for _, row in ng_list.iterrows():
                    excess = row['위치도'] - row['최종공차']
                    ng_html += f"<p style='color: #d32f2f; margin: 4px 0;'>• <b>{row['측정포인트']}</b>: {row['위치도']:.3f} (규격 Ø{row['최종공차']:.3f} 대비 <b>{excess:.3f} 초과</b>)</p>"
                ng_html += "</div>"
                st.markdown(ng_html, unsafe_allow_html=True)
            else:
                st.success("✅ 모든 시료가 합격 범위 내에 있습니다.")

            st.dataframe(df[['측정포인트', '위치도', '보너스', '최종공차', '판정']])

# 실제 기존 앱에 이식할 때 예시:
# if menu == "위치도 분석":
#     run_position_analysis()
