import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. 페이지 설정 및 강화된 CSS ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.1", layout="wide")

st.markdown("""
    <style>
    /* 배경 및 사이드바 기본 */
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* 사이드바 초기화 버튼 - 빨간색으로 시인성 강화 */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #ef4444 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        height: 3em !important;
        margin-top: 20px !important;
    }
    
    /* 카드 디자인 */
    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); margin-bottom: 24px; }
    .guide-box { background-color: #eff6ff; padding: 15px; border-radius: 10px; border: 1px solid #bfdbfe; color: #1e40af; font-size: 0.95em; margin-bottom: 20px; }
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 20px; }
    
    /* 캐비티 요약 카드 */
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 10px; text-align: center;
    }
    .ng-text { color: #e11d48; font-weight: bold; }
    .ok-text { color: #10b981; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 전역 초기화 로직 ---
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

def full_reset():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.reset_key = 0
    st.rerun()

# --- 3. 사이드바 메뉴 ---
st.sidebar.title("🚀 품질 분석 메뉴")
menu = st.sidebar.radio("📋 업무 선택", ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"])

if st.sidebar.button("🧹 전체 데이터 초기화", use_container_width=True):
    full_reset()

# --- [섹션 1] 데이터 변환기 ---
if menu == "🔄 데이터 변환기":
    st.title("🔄 좌표 데이터 변환기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 10, "Y": [""] * 10, "Z": [""] * 10})
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")
    if st.button("🚀 변환 결과 생성", use_container_width=True):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row.get("X","")).strip(), str(row.get("Y","")).strip(), str(row.get("Z","")).strip()
            if x and y and z: results.extend([z, x, y])
        if results:
            res_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(res_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [섹션 2] 멀티 캐비티 분석 (기존 기능 100% 복구) ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    
    def get_cavity_template():
        df_temp = pd.DataFrame({"Point": list(range(1, 55)), "SPEC_MIN": [30.03]*54, "SPEC_MAX": [30.38]*54, "Cavity_1": [30.2]*54, "Cavity_2": [30.22]*54, "Cavity_3": [30.18]*54, "Cavity_4": [30.25]*54})
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df_temp.to_excel(writer, index=False); return out.getvalue()

    col_file, col_temp = st.columns([3, 1])
    with col_temp: st.download_button("📄 템플릿 받기", get_cavity_template(), "Quality_Template.xlsx", use_container_width=True)
    with col_file: uploaded_file = st.file_uploader("분석 파일 업로드", type=["xlsx", "csv"], key=f"cav_{st.session_state.reset_key}")

    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        
        # [핵심수정] 전 구간 데이터 기반으로 정밀 Y축 범위 자동 설정 (margin 0.02 적용)
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(all_vals.min()) - 0.02, float(all_vals.max()) + 0.02]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']

        st.subheader("🔍 캐비티별 상세 분포 (정밀 스케일 적용)")
        c_grid = st.columns(2)
        summary_results = []
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            with c_grid[i % 2]:
                st.markdown('<div class="stBox">', unsafe_allow_html=True)
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", width=1.1, dash="dash"), name="MIN"))
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", width=1.1, dash="dash"), name="MAX"))
                b_colors = ['#ef4444' if p == "NG" else cav_colors[i % 4] for p in df[f"{cav}_판정"]]
                fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors, name="측정값"))
                fig_ind.update_layout(title=f"<b>{cav} 분석</b>", yaxis_range=y_range, height=300, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_ind, use_container_width=True)
                summary_results.append({"cav": cav, "ng": len(df[df[f"{cav}_판정"]=="NG"]), "total": len(df), "color": cav_colors[i % 4]})
                st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("📋 품질현황 요약 대쉬보드")
        d_cols = st.columns(len(summary_results))
        for i, res in enumerate(summary_results):
            rate = ((res['total'] - res['ng']) / res['total']) * 100
            d_cols[i].markdown(f'<div class="summary-card" style="border-top-color: {res["color"]};"><small>{res["cav"]}</small><br><span class="{"ok-text" if rate==100 else "ng-text"}" style="font-size:1.6em;">{rate:.1f}%</span><br><small>NG: {res["ng"]} EA</small></div>', unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 경향성 (전체 평균 Trend)")
        df['Average'] = df[cav_cols].mean(axis=1)
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="blue", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="red", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Average'], name="평균 Trend", line=dict(color="black", width=3)))
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', marker=dict(size=7, color=cav_colors[i % 4], opacity=0.4)))
        fig_total.update_layout(yaxis_range=y_range, height=500, template="plotly_white")
        st.plotly_chart(fig_total, use_container_width=True)
        
        output_res = BytesIO()
        with pd.ExcelWriter(output_res, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Result')
        st.download_button("📥 통합 분석 보고서(엑셀) 저장", output_res.getvalue(), "Cavity_Analysis.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [섹션 3] 위치도 분석 (리셋, 요약, 다운로드 완전 복구) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 시스템")
    
    def get_mmc_template():
        template_df = pd.DataFrame({"측정포인트": list(range(1, 9)), "기본공차": [0.30] * 8, "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1], "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3], "측정치_X": [0.0]*8, "측정치_Y": [0.0]*8, "실측지름_MMC용": [0.50]*8})
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: template_df.to_excel(writer, index=False); return out.getvalue()

    def create_mmc_excel(dataframe, plotly_fig):
        output = BytesIO()
        try: img_bytes = plotly_fig.to_image(format="png", width=800, height=800)
        except: img_bytes = None
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, sheet_name='분석결과', index=False)
            if img_bytes: writer.sheets['분석결과'].insert_image('I2', 'graph.png', {'image_data': BytesIO(img_bytes), 'x_scale': 0.6, 'y_scale': 0.6})
        return output.getvalue()

    # [복구] 데이터 입력 섹션의 리셋 버튼과 템플릿 버튼
    with st.expander("📂 데이터 입력 및 설정", expanded=True):
        header_col1, header_col2 = st.columns([5, 1])
        with header_col2: 
            if st.button("🔄 데이터 리셋", use_container_width=True): full_reset()
        c1, c2 = st.columns([1, 2])
        with c1:
            st.download_button("📥 위치도 양식 다운로드", get_mmc_template(), "MMC_Template.xlsx", use_container_width=True)
            mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
        with c2:
            file = st.file_uploader("엑셀 업로드", type=["xlsx"], key=f"mmc_up_{st.session_state.reset_key}")

    if file: df_m = pd.read_excel(file)
    else: # 샘플 데이터 (1번부터 시작)
        df_m = pd.DataFrame({"측정포인트": [1, 2, 3, 4, 5, 6, 7, 8], "기본공차": [0.30] * 8, "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1], "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3], "측정치_X": [-55.715, -35.79, -14.81, 5.10, -45.52, -5.09, -55.74, 5.11], "측정치_Y": [-38.82, -38.80, -38.79, -38.81, -54.72, -54.68, -70.32, -70.31], "실측지름_MMC용": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]})

    # 위치도 계산 로직
    df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
    df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
    df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
    df_m['보너스'] = (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
    df_m['최종공차'] = df_m['기본공차'] + df_m['보너스']
    df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")
    df_m.index = np.arange(1, len(df_m) + 1)

    st.markdown("""<div class="stBox"><h4>💡 과녁 가이드</h4>🔵기본공차 | 🟣MMC합격선 | 🔴NG마지노선</div>""", unsafe_allow_html=True)
    
    # [복구] 과녁 그래프 시각화
    fig_m = go.Figure()
    fig_m.update_xaxes(zeroline=True, zerolinewidth=2.5, zerolinecolor='black', gridcolor='#eee')
    fig_m.update_yaxes(zeroline=True, zerolinewidth=2.5, zerolinecolor='black', gridcolor='#eee')
    fig_m.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, line=dict(color="Blue", dash="dot"))
    max_t = df_m['최종공차'].max() / 2
    fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=2.5), fillcolor="rgba(147, 112, 219, 0.1)")
    fig_m.add_shape(type="circle", x0=-(max_t+0.02), y0=-(max_t+0.02), x1=(max_t+0.02), y1=(max_t+0.02), line=dict(color="Red", width=1.5, dash="dashdot"))
    
    for _, row in df_m.iterrows():
        p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
        fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', text=[f"<b>{row['측정포인트']}</b>"], textposition="top center", marker=dict(size=13, color=p_c, line=dict(width=1.5, color='white'))))
    fig_m.update_layout(xaxis_range=[-0.35, 0.35], yaxis_range=[-0.35, 0.35], height=650, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_m, use_container_width=True)

    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📋 분석 상세 데이터 (1번부터)")
    st.dataframe(df_m.style.map(lambda x: 'color:red; font-weight:bold' if x == 'NG' else '', subset=['판정']), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # [복구] 하단 요약 및 엑셀 보고서 다운로드
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.subheader("📊 품질 분석 요약")
    res_c1, res_c2, res_c3 = st.columns(3)
    with res_c1: st.write(f"**총 검사:** {len(df_m)} 포인트 | **합격:** {len(df_m[df_m['판정']=='OK'])} EA")
    with res_c2: 
        if len(df_m[df_m['판정']=="NG"]) == 0: st.success("✅ 모든 포인트 합격")
        else: st.error(f"🚨 {len(df_m[df_m['판정']=='NG'])}개 불량 발생")
    with res_c3:
        report_mmc = create_mmc_excel(df_m, fig_m)
        st.download_button("🚀 이미지 포함 보고서 저장", report_mmc, "Position_Report.xlsx", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [섹션 4] 계산기 ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 현장 계산 도구")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    tabs = st.tabs(["🎯 MMC 보너스", "⚖️ 공차 판정", "📊 통계"])
    with tabs[0]:
        c1, c2 = st.columns(2)
        m_type = c1.radio("유형", ["구멍", "축"], horizontal=True)
        m_geo = c2.number_input("기하공차", value=0.05)
        m_mmc, m_act = st.number_input("MMC 규격", value=10.0), st.number_input("실측치", value=10.02)
        bonus = max(0.0, m_act - m_mmc if "구멍" in m_type else m_mmc - m_act)
        st.metric("최종 공차", f"{m_geo + bonus:.4f}")
    st.markdown('</div>', unsafe_allow_html=True)
