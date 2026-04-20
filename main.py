import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 (기본 유지) ---
st.set_page_config(page_title="품질 통합 분석 시스템 v8.8", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
    .stButton > button {
        background-color: #ef4444 !important; color: white !important;
        font-weight: bold !important; width: 100%; border-radius: 8px;
    }
    .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 25px; }
    .report-card { background-color: #f1f5f9; padding: 20px; border-left: 10px solid #3b82f6; border-radius: 8px; line-height: 2.0; font-size: 1.1em; }
    .guide-box { padding: 15px; background-color: #f8fafc; border-radius: 10px; border: 1px dashed #cbd5e1; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- 2. 사이드바 (초기화 버튼 위치 고정) ---
st.sidebar.title("💎 품질 통합 플랫폼 v8.8")
menu = st.sidebar.radio("📋 업무 선택", ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"], key=f"m_{st.session_state.reset_key}")

st.sidebar.markdown("---")
if st.sidebar.button("🧹 모든 데이터 초기화"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.reset_key += 1
    st.rerun()

# --- [메뉴 2] 멀티 캐비티 분석 (엑셀 이미지 삽입 로직 추가) ---
if menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    up = st.file_uploader("파일 업로드", type=["xlsx", "csv"])
    if up:
        df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        c_grid = st.columns(2)
        summary_items = []
        for i, cav in enumerate(cav_cols):
            color = cav_colors[i % len(cav_colors)]
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            summary_items.append(f"✅ **{cav}**: 합격률 **{((len(df)-len(df[df[f'{cav}_판정']=='NG']))/len(df))*100:.1f}%**")
            with c_grid[i % 2]:
                st.markdown(f'<div class="stBox"><b style="color:{color};">{cav}</b>', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=color))
                fig.update_layout(height=280, margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 트렌드 분석")
        fig_total = go.Figure()
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], mode='markers+lines', marker=dict(color=cav_colors[i%len(cav_colors)]), name=cav))
        st.plotly_chart(fig_total, use_container_width=True)
        
        # 엑셀 다운로드 (이미지 포함 시도)
        out_cav = BytesIO()
        with pd.ExcelWriter(out_cav, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Result_Data', index=False)
            workbook = writer.book
            worksheet = workbook.add_worksheet('Chart_Report')
            try:
                # [이미지 삽입 핵심 코드]
                img_data = fig_total.to_image(format="png", engine="kaleido")
                worksheet.insert_image('B2', 'trend.png', {'image_data': BytesIO(img_data)})
            except:
                worksheet.write('A1', '※ 이미지 생성 엔진 오류로 데이터만 저장되었습니다. 그래프는 웹에서 캡처해 주세요.')
        
        st.download_button("📥 분석 결과 엑셀 저장", out_cav.getvalue(), "Cavity_Report.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 (색상 가이드 + 이미지 삽입 추가) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 (MMC)")
    up_pos = st.file_uploader("파일 업로드", type=["xlsx"])
    if up_pos:
        df_m = pd.read_excel(up_pos)
        mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
        df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
        df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
        df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
        df_m['최종공차'] = df_m['기본공차'] + (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
        df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.markdown("""<div class="guide-box">🔵 파랑: ±0.05 | 🟣 보라: 최종합격 | 🔴 빨강: 한계선</div>""", unsafe_allow_html=True)
        
        fig_m = go.Figure()
        fig_m.update_yaxes(scaleanchor="x", scaleratio=1)
        # (과녁 그리기 로직 v8.3과 동일)
        max_t = df_m['최종공차'].max() / 2
        fig_m.add_shape(type="circle", x0=-0.05, y0=-0.05, x1=0.05, y1=0.05, line=dict(color="Blue", dash="dot"))
        fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=3))
        for _, r in df_m.iterrows():
            p_c = '#10b981' if r['판정']=="OK" else '#ef4444'
            fig_m.add_trace(go.Scatter(x=[r['X편차']], y=[r['Y편차']], mode='markers+text', text=[str(int(r['측정포인트']))], marker=dict(size=12, color=p_c)))
        st.plotly_chart(fig_m, use_container_width=True)
        
        st.subheader("📋 실측 데이터 확인")
        st.dataframe(df_m, use_container_width=True)
        
        # 엑셀 다운로드 (이미지 포함 시도)
        out_pos = BytesIO()
        with pd.ExcelWriter(out_pos, engine='xlsxwriter') as writer:
            df_m.to_excel(writer, sheet_name='Position_Data', index=False)
            workbook = writer.book
            worksheet = workbook.add_worksheet('Position_Chart')
            try:
                img_data_pos = fig_m.to_image(format="png", engine="kaleido")
                worksheet.insert_image('B2', 'position.png', {'image_data': BytesIO(img_data_pos)})
            except:
                worksheet.write('A1', '이미지 저장 실패: 서버 엔진 확인 요망')

        st.download_button("📥 위치도 분석 결과 저장", out_pos.getvalue(), "Position_Analysis.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 나머지 메뉴 (데이터 변환기, 계산기)는 기존과 동일하게 유지 ---
