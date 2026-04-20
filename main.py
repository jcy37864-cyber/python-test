import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.2", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* 사이드바 리셋 버튼 시인성 강화 */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #ef4444 !important;
        color: white !important;
        font-weight: bold !important;
        height: 3em !important;
        margin-top: 20px !important;
        border-radius: 8px;
    }
    
    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 24px; }
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 20px; }
    .report-text { font-size: 1.05em; line-height: 1.8; color: #1e293b; white-space: pre-wrap; font-family: sans-serif; }
    .ng-text { color: #e11d48; font-weight: bold; }
    .ok-text { color: #10b981; font-weight: bold; }
    
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 초기화 로직 ---
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

def full_reset():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.reset_key += 1
    st.rerun()

# --- 3. 사이드바 ---
st.sidebar.title("🚀 품질 분석 메뉴")
menu = st.sidebar.radio("📋 업무 선택", ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"])

if st.sidebar.button("🧹 전체 데이터 초기화", use_container_width=True):
    full_reset()

# --- [메뉴 1] 데이터 변환기 ---
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
            st.download_button("📂 CSV 다운로드", res_df.to_csv(index=True).encode("utf-8-sig"), "zxy_result.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 2] 멀티 캐비티 분석 ---
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
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(all_vals.min()) - 0.02, float(all_vals.max()) + 0.02]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']

        # 개별 그래프
        st.subheader("🔍 캐비티별 상세 분포 (정밀 스케일)")
        c_grid = st.columns(2)
        summary_results = []
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            with c_grid[i % 2]:
                st.markdown('<div class="stBox">', unsafe_allow_html=True)
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", width=1, dash="dash"), name="MIN"))
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", width=1, dash="dash"), name="MAX"))
                b_colors = ['#ef4444' if p == "NG" else cav_colors[i % 4] for p in df[f"{cav}_판정"]]
                fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors, name="측정값"))
                fig_ind.update_layout(title=f"<b>{cav} 분석</b>", yaxis_range=y_range, height=300, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_ind, use_container_width=True)
                summary_results.append({"cav": cav, "ng": len(df[df[f"{cav}_판정"]=="NG"]), "total": len(df), "color": cav_colors[i % 4]})
                st.markdown('</div>', unsafe_allow_html=True)

        # 요약 대시보드
        st.subheader("📋 품질현황 요약 대쉬보드")
        d_cols = st.columns(len(summary_results))
        for i, res in enumerate(summary_results):
            rate = ((res['total'] - res['ng']) / res['total']) * 100
            d_cols[i].markdown(f'<div class="summary-card" style="border-top-color: {res["color"]};"><small>{res["cav"]}</small><br><span class="{"ok-text" if rate==100 else "ng-text"}" style="font-size:1.6em;">{rate:.1f}%</span><br><small>NG: {res["ng"]} EA</small></div>', unsafe_allow_html=True)

        # 통합 트렌드
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 경향성")
        df['Average'] = df[cav_cols].mean(axis=1)
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="blue", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="red", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Average'], name="평균 Trend", line=dict(color="black", width=3)))
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', marker=dict(size=7, color=cav_colors[i % 4], opacity=0.4)))
        fig_total.update_layout(yaxis_range=y_range, height=500, template="plotly_white")
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [복구] 상세 텍스트 리포트
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📝 품질 분석 상세 리포트")
        total_ng_sum = sum(r['ng'] for r in summary_results)
        report_content = f"⚠️ 종합 판정: {'부적합' if total_ng_sum > 0 else '양호'}\n\n"
        for res in summary_results:
            report_content += f"■ {res['cav']}: 합격률 {((res['total']-res['ng'])/res['total'])*100:.1f}% (NG: {res['ng']}건)\n"
        st.markdown(f'<div class="report-text">{report_content}</div>', unsafe_allow_html=True)
        
        output_res = BytesIO()
        with pd.ExcelWriter(output_res, engine='xlsxwriter') as writer: df.to_excel(writer, index=False, sheet_name='Result')
        st.download_button("📥 결과 엑셀 다운로드", output_res.getvalue(), "Quality_Final_Report.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 ---
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

    with st.expander("📂 데이터 입력 및 설정", expanded=True):
        h1, h2 = st.columns([5, 1])
        with h2: 
            if st.button("🔄 데이터 리셋", use_container_width=True): full_reset()
        c1, c2 = st.columns([1, 2])
        with c1:
            st.download_button("📥 양식 다운로드", get_mmc_template(), "MMC_Template.xlsx", use_container_width=True)
            mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
        with c2:
            file = st.file_uploader("엑셀 업로드", type=["xlsx"], key=f"mmc_up_{st.session_state.reset_key}")

    if file: df_m = pd.read_excel(file)
    else:
        df_m = pd.DataFrame({"측정포인트": [1, 2, 3, 4, 5, 6, 7, 8], "기본공차": [0.30] * 8, "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1], "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3], "측정치_X": [-55.715, -35.79, -14.81, 5.10, -45.52, -5.09, -55.74, 5.11], "측정치_Y": [-38.82, -38.80, -38.79, -38.81, -54.72, -54.68, -70.32, -70.31], "실측지름_MMC용": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]})

    df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
    df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
    df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
    df_m['보너스'] = (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
    df_m['최종공차'] = df_m['기본공차'] + df_m['보너스']
    df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")
    df_m.index = np.arange(1, len(df_m) + 1)

    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    fig_m = go.Figure()
    fig_m.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, line=dict(color="Blue", dash="dot"))
    max_t = df_m['최종공차'].max() / 2
    fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=2.5), fillcolor="rgba(147, 112, 219, 0.1)")
    fig_m.add_shape(type="circle", x0=-(max_t+0.02), y0=-(max_t+0.02), x1=(max_t+0.02), y1=(max_t+0.02), line=dict(color="Red", width=1.5, dash="dashdot"))
    for _, row in df_m.iterrows():
        p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
        fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', text=[f"<b>{row['측정포인트']}</b>"], textposition="top center", marker=dict(size=13, color=p_c, line=dict(width=1.5, color='white'))))
    fig_m.update_layout(xaxis_range=[-0.35, 0.35], yaxis_range=[-0.35, 0.35], height=650, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_m, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📋 분석 데이터")
    st.dataframe(df_m.style.map(lambda x: 'color:red; font-weight:bold' if x == 'NG' else '', subset=['판정']), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.subheader("📊 품질 분석 요약")
    res_c1, res_c2, res_c3 = st.columns(3)
    with res_c1: st.write(f"**총 검사:** {len(df_m)} 포인트 | **합격:** {len(df_m[df_m['판정']=='OK'])} EA")
    with res_c2: 
        if len(df_m[df_m['판정']=="NG"]) == 0: st.success("✅ 전 포인트 합격")
        else: st.error(f"🚨 {len(df_m[df_m['판정']=='NG'])}개 불량 발생")
    with res_c3:
        report_mmc = create_mmc_excel(df_m, fig_m)
        st.download_button("🚀 보고서(이미지 포함) 저장", report_mmc, "Position_Report.xlsx", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 4] 품질 계산기 (토크/단위 복구) ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 현장 계산 도구")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    tabs = st.tabs(["🎯 MMC 보너스", "⚖️ 공차 판정", "🔧 토크/단위 변환", "📊 기초 통계"])
    
    with tabs[0]:
        c1, c2 = st.columns(2)
        m_type = c1.radio("유형", ["구멍", "축"], horizontal=True)
        m_geo = c2.number_input("도면 기하공차", value=0.05)
        m_mmc, m_act = st.number_input("MMC 규격", value=10.0), st.number_input("실측치", value=10.02)
        bonus = max(0.0, m_act - m_mmc if "구멍" in m_type else m_mmc - m_act)
        st.metric("최종 공차", f"{m_geo + bonus:.4f}")
        
    with tabs[1]:
        p1, p2, p3, p4 = st.columns(4)
        base, u_t, l_t, ms = p1.number_input("기준"), p2.number_input("상한"), p3.number_input("하한"), p4.number_input("측정")
        if (base+l_t) <= ms <= (base+u_t): st.success("✅ OK")
        else: st.error("🚨 NG")
        
    with tabs[2]: # [복구] 토크 및 단위 변환
        col_calc1, col_calc2 = st.columns(2)
        with col_calc1:
            st.subheader("🔧 토크 변환")
            v_t = st.number_input("토크 값 입력", value=1.0, key="t_val")
            m_t = st.selectbox("변환 방향", ["N·m → kgf·m", "kgf·m → N·m"])
            res_t = v_t * 0.101972 if "kgf" in m_t else v_t * 9.80665
            st.info(f"결과: {res_t:.4f}")
        with col_calc2:
            st.subheader("📏 단위 변환")
            v_u = st.number_input("단위 값 입력", value=1.0, key="u_val")
            m_u = st.selectbox("변환 항목", ["mm → inch", "inch → mm", "mm → μm"])
            if "inch" in m_u: res_u = v_u / 25.4 if "mm →" in m_u else v_u * 25.4
            else: res_u = v_u * 1000
            st.info(f"결과: {res_u:.4f}")

    with tabs[3]:
        data_str = st.text_area("데이터 입력 (쉼표 구분)")
        if data_str:
            try:
                nums = [float(x.strip()) for x in data_str.split(",") if x.strip()]
                st.write(f"평균: {np.mean(nums):.4f} | R: {np.ptp(nums):.4f} | σ: {np.std(nums):.4f}")
            except: st.error("숫자 형식을 확인하세요.")
    st.markdown('</div>', unsafe_allow_html=True)
