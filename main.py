import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
import os

# --- 1. 페이지 설정 및 디자인 (v8.3 동일 유지) ---
st.set_page_config(page_title="품질 통합 분석 시스템 v8.4", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
    .stButton > button {
        background-color: #ef4444 !important; color: white !important;
        font-weight: bold !important; width: 100%; border-radius: 8px;
    }
    .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); margin-bottom: 25px; }
    .report-card { background-color: #f1f5f9; padding: 20px; border-left: 10px solid #3b82f6; border-radius: 8px; line-height: 2.0; font-size: 1.1em; }
    .guide-box { padding: 15px; background-color: #f8fafc; border-radius: 10px; border: 1px dashed #cbd5e1; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- 2. 사이드바 (v8.3 구조 유지) ---
st.sidebar.title("💎 품질 통합 플랫폼 v8.4")
menu = st.sidebar.radio("📋 업무 선택", ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"], key=f"m_{st.session_state.reset_key}")

st.sidebar.markdown("---")
if st.sidebar.button("🧹 모든 데이터 초기화"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.reset_key += 1
    st.rerun()

# --- [메뉴 1] 데이터 변환기 (유지) ---
if menu == "🔄 데이터 변환기":
    st.title("🔄 좌표 데이터 변환기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    df_input = st.data_editor(pd.DataFrame({"X": [""]*10, "Y": [""]*10, "Z": [""]*10}), num_rows="dynamic", use_container_width=True)
    if st.button("🚀 데이터 변환 실행"):
        res = []
        for _, r in df_input.iterrows():
            if str(r['X']).strip(): res.extend([r['Z'], r['X'], r['Y']])
        if res:
            df_res = pd.DataFrame(res, columns=["변환 데이터 (Z-X-Y)"])
            st.dataframe(df_res, use_container_width=True)
            st.download_button("📥 결과 CSV 저장", df_res.to_csv(index=False).encode('utf-8-sig'), "converted_data.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 2] 멀티 캐비티 분석 (이미지 삽입 보완) ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    def get_cav_template():
        df_t = pd.DataFrame({"Point": range(1,6), "SPEC_MIN": [30.1]*5, "SPEC_MAX": [30.5]*5, "Cavity_1": [30.2]*5, "Cavity_2": [30.3]*5, "Cavity_3": [30.2]*5, "Cavity_4": [30.4]*5})
        out = BytesIO(); writer = pd.ExcelWriter(out, engine='xlsxwriter'); df_t.to_excel(writer, index=False); writer.close()
        return out.getvalue()
    st.download_button("📄 분석용 템플릿 다운로드", get_cav_template(), "Multi_Cavity_Template.xlsx")
    
    up = st.file_uploader("파일 업로드", type=["xlsx", "csv"])
    if up:
        df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_min, y_max = np.nanmin(all_vals) - 0.03, np.nanmax(all_vals) + 0.03
        
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
                fig.update_layout(height=280, yaxis_range=[y_min, y_max], margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 트렌드 분석")
        df['Avg'] = df[cav_cols].mean(axis=1)
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dot"), name="MIN"))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dot"), name="MAX"))
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], mode='markers', marker=dict(color=cav_colors[i%len(cav_colors)], size=10), name=cav))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Avg'], line=dict(color="black", width=3), name="평균"))
        st.plotly_chart(fig_total, use_container_width=True)
        
        st.markdown(f'<div class="report-card">{"<br>".join(summary_items)}</div>', unsafe_allow_html=True)
        
        # [이미지 삽입 엑셀 다운로드 로직]
        out_cav = BytesIO()
        with pd.ExcelWriter(out_cav, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data_Result', index=False)
            workbook = writer.book
            worksheet = workbook.add_worksheet('Visual_Chart')
            # 안내 문구 삽입
            worksheet.write('A1', '※ 통합 트렌드 그래프는 시스템에서 자동 생성되어 삽입되었습니다.')
            img_data = fig_total.to_image(format="png", width=800, height=500)
            img_io = BytesIO(img_data)
            worksheet.insert_image('A3', 'trend_chart.png', {'image_data': img_io})
            
        st.download_button("📥 그래프 포함 분석결과 엑셀 저장", out_cav.getvalue(), "Cavity_Report_Full.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 (이미지 삽입 보완) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 (MMC)")
    def get_pos_template():
        df_pt = pd.DataFrame({"측정포인트": [1], "기본공차": [0.3], "도면치수_X": [10.0], "도면치수_Y": [10.0], "측정치_X": [10.02], "측정치_Y": [10.01], "실측지름_MMC용": [0.52]})
        out = BytesIO(); writer = pd.ExcelWriter(out, engine='xlsxwriter'); df_pt.to_excel(writer, index=False); writer.close()
        return out.getvalue()
    st.download_button("📄 위치도 템플릿 다운로드", get_pos_template(), "Position_Template.xlsx")

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
        st.markdown("""<div class="guide-box">🔵 파란 점선: 중심 정밀(±0.05) | 🟣 보라 실선: 최종 합격 범위 | 🔴 빨간 점선: 공차 한계선</div>""", unsafe_allow_html=True)
        
        fig_pos = go.Figure()
        fig_pos.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinecolor='black')
        fig_pos.update_xaxes(zeroline=True, zerolinecolor='black')
        max_t = df_m['최종공차'].max() / 2
        fig_pos.add_shape(type="circle", x0=-0.05, y0=-0.05, x1=0.05, y1=0.05, line=dict(color="Blue", dash="dot"))
        fig_pos.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=3), fillcolor="rgba(147, 112, 219, 0.1)")
        fig_pos.add_shape(type="circle", x0=-(max_t+0.05), y0=-(max_t+0.05), x1=(max_t+0.05), y1=(max_t+0.05), line=dict(color="Red", dash="dash"))
        for _, r in df_m.iterrows():
            p_c = '#10b981' if r['판정']=="OK" else '#ef4444'
            fig_pos.add_trace(go.Scatter(x=[r['X편차']], y=[r['Y편차']], mode='markers+text', text=[f"<b>{int(r['측정포인트'])}</b>"], textposition="top center", marker=dict(size=12, color=p_c, line=dict(width=1, color='white'))))
        st.plotly_chart(fig_pos, use_container_width=True)
        
        st.subheader("📋 실측 데이터 확인")
        st.dataframe(df_m.style.map(lambda x: 'background-color: #d1fae5' if x == 'OK' else 'background-color: #fee2e2', subset=['판정']), use_container_width=True)
        
        # [이미지 삽입 엑셀 다운로드 로직]
        out_pos = BytesIO()
        with pd.ExcelWriter(out_pos, engine='xlsxwriter') as writer:
            df_m.to_excel(writer, sheet_name='Position_Data', index=False)
            workbook = writer.book
            worksheet = workbook.add_worksheet('Position_Chart')
            worksheet.write('A1', '※ 위치도 분석 과녁 그래프가 삽입되었습니다.')
            # Plotly 서식을 유지하여 이미지 변환
            img_data = fig_pos.to_image(format="png", width=700, height=700)
            img_io = BytesIO(img_data)
            worksheet.insert_image('A3', 'pos_chart.png', {'image_data': img_io})

        st.download_button("📥 그래프 포함 분석결과 엑셀 저장", out_pos.getvalue(), "Position_Report_Full.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 4] 품질 계산기 (유지) ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    tabs = st.tabs(["🎯 MMC 보너스", "🔧 일반 단위환산", "⚙️ 토크 변환", "⚖️ 합격 판정"])
    with tabs[0]:
        base_g = st.number_input("기본 기하공차", value=0.05); mmc_s = st.number_input("MMC 규격", value=10.00); act_s = st.number_input("현재 실측", value=10.02)
        st.metric("최종 공차", f"{base_g + max(0, act_s - mmc_s):.4f}")
    with tabs[1]:
        v = st.number_input("값", value=1.0); m = st.selectbox("종류", ["mm ➔ inch", "inch ➔ mm"])
        st.success(f"결과: {v/25.4:.4f}" if "inch" in m[:4] else f"결과: {v*25.4:.4f}")
    with tabs[2]:
        t_v = st.number_input("토크 값 입력", value=1.0); t_m = st.selectbox("단위", ["N·m ➔ kgf·m", "kgf·m ➔ N·m", "N·m ➔ kgf·cm", "kgf·cm ➔ N·m"])
        if t_m == "N·m ➔ kgf·m": res = t_v * 0.10197
        elif t_m == "kgf·m ➔ N·m": res = t_v * 9.80665
        elif t_m == "N·m ➔ kgf·cm": res = t_v * 10.197
        else: res = t_v * 0.09806
        st.info(f"변환 결과: {res:.4f}")
    with tabs[3]:
        spec = st.number_input("기준"); u, l = st.number_input("상한"), st.number_input("하한"); m_v = st.number_input("측정")
        if (spec+l) <= m_v <= (spec+u): st.success("✅ 합격")
        else: st.error("🚨 불합격")
    st.markdown('</div>', unsafe_allow_html=True)
