import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 앱 설정
st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 위치도 정밀 분석 (최종 마스터 버전)")

# [데이터 파싱 함수]
def parse_smart_data(raw_text, sc):
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', raw_text)]
    if not nums: return None
    results = []
    step = 1 + sc
    set_len = step * 3
    for i in range(len(nums) // set_len):
        base = i * set_len
        try:
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
        except: break
    return results

# 2. 사이드바 기준 설정
with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수 (이미지 기준 4)", min_value=1, value=4)
    tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
    mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")
    
    st.divider()
    st.header("🔍 그래프 보기 범위")
    # 표준 범위 계산 (공차 반지름의 2배 = 지름 크기만큼을 한쪽 범위로 설정)
    std_range = round(tol, 2) 
    
    view_mode = st.radio("범위 모드", ["표준(권장)", "사용자 조절"])
    
    if view_mode == "표준(권장)":
        view_limit = std_range
        st.info(f"📍 표준 범위 ±{view_limit}mm로 고정됨")
    else:
        view_limit = st.slider("수동 조절(±mm)", 0.1, 5.0, std_range, step=0.1)

# 3. 데이터 입력
raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=150)

if raw_input:
    data = parse_smart_data(raw_input, sc)
    if data:
        df = pd.DataFrame(data)
        # 핵심 계산
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- 4. 그래프 시각화 ---
        fig = go.Figure()
        
        # 파란 원 (도면 기본 규격)
        r_blue = tol / 2
        fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue,
                      line=dict(color="RoyalBlue", width=2.5), fillcolor="rgba(65, 105, 225, 0.05)")
        
        # 빨간 원 (최종 MMC 규격)
        max_total_tol = df['최종공차'].max()
        r_red = max_total_tol / 2
        # 화면 이탈 방지 로직 유지
        display_r_red = min(r_red, view_limit * 0.98)
        fig.add_shape(type="circle", x0=-display_r_red, y0=-display_r_red, x1=display_r_red, y1=display_r_red,
                      line=dict(color="Red", width=2, dash="dot"))

        # [기능 유지] 그래프 내부 수치 텍스트 표기
        fig.add_annotation(x=r_blue*0.7, y=r_blue*0.7, text=f"기본: Ø{tol:.3f}", showarrow=False, font=dict(color="RoyalBlue", size=11), bgcolor="white")
        if max_total_tol > tol:
            fig.add_annotation(x=display_r_red*0.7, y=-display_r_red*0.7, text=f"최종(MMC): Ø{max_total_tol:.3f}", showarrow=False, font=dict(color="Red", size=11), bgcolor="white")

        # 데이터 점 표시 (OK/NG 구분)
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            # 화면 범위 안의 점만 필터링
            visible = sub[(sub['편차_X'].abs() <= view_limit) & (sub['편차_Y'].abs() <= view_limit)]
            if not visible.empty:
                fig.add_trace(go.Scatter(x=visible['편차_X'], y=visible['편차_Y'], mode='markers+text', name=res,
                                         text=visible['측정포인트'], textposition="top center",
                                         marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))))

        # 그래프 레이아웃 설정
        fig.update_layout(
            width=700, height=700,
            xaxis=dict(range=[-view_limit, view_limit], zeroline=True, gridcolor='lightgrey'),
            yaxis=dict(range=[-view_limit, view_limit], zeroline=True, gridcolor='lightgrey'),
            plot_bgcolor='white',
            title=f"🎯 위치도 분석 (보기 범위: ±{view_limit}mm)"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # --- 5. 하단 텍스트 및 스크롤 리스트 ---
        st.divider()
        
        # [기능 유지] 규격 요약 정보
        st.info(f"📌 **품질 규격 요약**\n- **도면 기준 공차**: Ø{tol:.3f}\n- **최대 합격 한계(MMC 적용)**: Ø{max_total_tol:.3f}")
        
        ng_list = df[df['판정'] == "❌ NG"]
        
        if not ng_list.empty:
            st.error(f"🚨 **규격 이탈(NG) 시료 상세 리스트 (총 {len(ng_list)}건)**")
            
            # [기능 유지] 스크롤 박스 (HTML)
            ng_html = "<div style='height: 200px; overflow-y: auto; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; background-color: #fff5f5;'>"
            for _, row in ng_list.iterrows():
                excess = row['위치도'] - row['최종공차']
                ng_html += f"<p style='color: #d32f2f; margin: 5px 0;'>• <b>{row['측정포인트']}</b>: 측정 {row['위치도']:.3f} (규격 Ø{row['최종공차']:.3f} 대비 <b>{excess:.3f} 초과</b>)</p>"
            ng_html += "</div>"
            st.markdown(ng_html, unsafe_allow_html=True)
        else:
            st.success("✅ **모든 시료가 최종 합격 범위 내에 있습니다.**")

        # 전체 데이터 테이블 유지
        st.subheader("📊 전체 데이터 테이블")
        st.dataframe(df[['측정포인트', '위치도', '보너스', '최종공차', '판정']])
