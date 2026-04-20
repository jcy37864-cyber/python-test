import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.3", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* 사이드바 리셋 버튼 - 빨간색 고대비 */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #ef4444 !important;
        color: white !important;
        font-weight: bold !important;
        height: 3em !important;
        margin-top: 20px !important;
    }
    
    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 24px; }
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 20px; }
    .report-text { font-size: 1.05em; line-height: 1.8; color: #1e293b; white-space: pre-wrap; }
    .ok-text { color: #10b981; font-weight: bold; }
    .ng-text { color: #e11d48; font-weight: bold; }
    
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
        
        st.subheader("🔍 캐비티별 상세 분포")
        c_grid = st.columns(2)
        summary_results = []
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            with c_grid[i % 2]:
                st.markdown('<div class="stBox">', unsafe_allow_html=True)
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                b_colors = ['#ef4444' if p == "NG" else '#1f77b4' for p in df[f"{cav}_판정"]]
                fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors, name="측정값"))
                fig_ind.update_layout(title=f"<b>{cav} 분석</b>", yaxis_range=y_range, height=300, 
                                      xaxis=dict(tickfont=dict(size=12, byte=True)), yaxis=dict(tickfont=dict(size=12, byte=True)))
                st.plotly_chart(fig_ind, use_container_width=True)
                summary_results.append({"cav": cav, "ng": len(df[df[f"{cav}_판정"]=="NG"]), "total": len(df)})
                st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("📋 품질 분석 리포트")
        total_ng = sum(r['ng'] for r in summary_results)
        report_text = f"✅ 최종 판정: {'[부적합] - 수정 요망' if total_ng > 0 else '[양호] - 합격'}\n\n"
        for res in summary_results:
            rate = ((res['total']-res['ng'])/res['total'])*100
            report_text += f"• {res['cav']}: 합격률 {rate:.1f}% (NG: {res['ng']}건)\n"
        st.markdown(f'<div class="stBox report-text">{report_text}</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 (정원 보정 및 폰트 강화) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 시스템")
    
    def get_mmc_template():
        template_df = pd.DataFrame({"측정포인트": list(range(1, 9)), "기본공차": [0.30] * 8, "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1], "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3], "측정치_X": [0.0]*8, "측정치_Y": [0.0]*8, "실측지름_MMC용": [0.50]*8})
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: template_df.to_excel(writer, index=False); return out.getvalue()

    with st.expander("📂 데이터 입력", expanded=True):
        h1, h2 = st.columns([5, 1])
        with h2: 
            if st.button("🔄 데이터 리셋", use_container_width=True): full_reset()
        c1, c2 = st.columns([1, 2])
        with c1:
            st.download_button("📥 양식 다운로드", get_mmc_template(), "MMC_Template.xlsx")
            mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
        with c2: file = st.file_uploader("엑셀 업로드", type=["xlsx"], key=f"mmc_up_{st.session_state.reset_key}")

    if file: df_m = pd.read_excel(file)
    else: # 샘플 데이터
        df_m = pd.DataFrame({"측정포인트": [1, 2, 3, 4, 5, 6, 7, 8], "기본공차": [0.30] * 8, "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1], "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3], "측정치_X": [-55.715, -35.79, -14.81, 5.10, -45.52, -5.09, -55.74, 5.11], "측정치_Y": [-38.82, -38.80, -38.79, -38.81, -54.72, -54.68, -70.32, -70.31], "실측지름_MMC용": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]})

    df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
    df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
    df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
    df_m['최종공차'] = df_m['기본공차'] + (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
    df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

    # --- 그래프 시각화 (정원 보정) ---
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    fig_m = go.Figure()
    
    # [핵심] Y축을 X축에 고정하여 정원 유지
    fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#eee', tickfont=dict(size=14, color="black"))
    fig_m.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#eee', tickfont=dict(size=14, color="black"))

    # 공차 가이드 원
    max_t = df_m['최종공차'].max() / 2
    fig_m.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, line=dict(color="Blue", dash="dot", width=1.5))
    fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=2), fillcolor="rgba(147, 112, 219, 0.05)")
    
    # 측정 데이터 점 및 텍스트(강조)
    for _, row in df_m.iterrows():
        p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
        fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', 
                                   text=[f"<b>{row['측정포인트']}</b>"], 
                                   textposition="top center",
                                   textfont=dict(size=16, color="black"),
                                   marker=dict(size=12, color=p_c, line=dict(width=1.5, color='white'))))
    
    fig_m.update_layout(title="🎯 과녁 위치도 (정원 유지)", width=700, height=700, template="plotly_white", showlegend=False, 
                        margin=dict(l=40, r=40, t=60, b=40))
    st.plotly_chart(fig_m, use_container_width=False) # 중앙 정렬 유지를 위해 False 권장
    st.markdown('</div>', unsafe_allow_html=True)

    # 요약 및 다운로드
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.subheader("📊 분석 요약 및 보고서")
    r1, r2, r3 = st.columns(3)
    r1.write(f"**총 검사:** {len(df_m)} 포인트")
    r2.write(f"**NG 합계:** {len(df_m[df_m['판정']=='NG'])} EA")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_m.to_excel(writer, index=False)
    r3.download_button("🚀 엑셀 결과 저장", output.getvalue(), "Position_Result.xlsx", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 4] 품질 계산기 (토크/단위 포함) ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 현장 계산 도구")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🎯 MMC 보너스", "🔧 토크/단위 변환", "⚖️ 공차 판정"])
    with t1:
        c1, c2 = st.columns(2)
        m_t = c1.radio("유형", ["구멍", "축"])
        m_g = c2.number_input("기하공차", value=0.050, format="%.3f")
        m_m, m_a = st.number_input("MMC 규격", value=10.0), st.number_input("실측치", value=10.02)
        bonus = max(0.0, m_a - m_m if "구멍" in m_t else m_m - m_a)
        st.metric("최종 허용 공차", f"{m_g + bonus:.4f}")
    with t2:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("토크")
            v_t = st.number_input("값", value=1.0)
            m_mode = st.selectbox("변환", ["N·m → kgf·m", "kgf·m → N·m"])
            st.write(f"결과: {v_t * 0.10197:.4f}" if "kgf" in m_mode else f"결과: {v_t * 9.80665:.4f}")
        with col_t2:
            st.subheader("단위")
            v_u = st.number_input("수치", value=1.0)
            u_mode = st.selectbox("변환", ["mm → inch", "inch → mm"])
            st.write(f"결과: {v_u / 25.4:.4f}" if "inch" in u_mode else f"결과: {v_u * 25.4:.4f}")
    st.markdown('</div>', unsafe_allow_html=True)
