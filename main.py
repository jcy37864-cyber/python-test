import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.4", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* 사이드바 리셋 버튼 - 고대비 레드 */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #ef4444 !important;
        color: white !important;
        font-weight: bold !important;
        height: 3.5em !important;
        margin-top: 20px !important;
        border: none !important;
    }
    
    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 24px; }
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 20px; }
    .report-text { font-size: 1.1em; line-height: 1.8; color: #1e293b; white-space: pre-wrap; font-family: 'Malgun Gothic', sans-serif; }
    .ok-text { color: #10b981; font-weight: bold; }
    .ng-text { color: #e11d48; font-weight: bold; }
    
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 전역 초기화 로직 ---
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

def full_reset():
    for key in list(st.session_state.keys()):
        if key != 'reset_key': del st.session_state[key]
    st.session_state.reset_key += 1
    st.rerun()

# --- 3. 사이드바 메뉴 ---
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
    
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic", key=f"editor_{st.session_state.reset_key}")
    
    c1, c2 = st.columns(2)
    if c1.button("🚀 변환 결과 생성", use_container_width=True):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row.get("X","")).strip(), str(row.get("Y","")).strip(), str(row.get("Z","")).strip()
            if x and y and z: results.extend([z, x, y])
        if results:
            res_df = pd.DataFrame(results, columns=["변환 결과"])
            st.session_state.trans_res = res_df

    if "trans_res" in st.session_state:
        st.dataframe(st.session_state.trans_res, use_container_width=True)
        # [복구] 다운로드 버튼
        csv = st.session_state.trans_res.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📂 변환 데이터(CSV) 다운로드", csv, "converted_data.csv", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 2] 멀티 캐비티 분석 ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    
    def get_cavity_template():
        df_temp = pd.DataFrame({"Point": list(range(1, 11)), "SPEC_MIN": [30.03]*10, "SPEC_MAX": [30.38]*10, "Cavity_1": [30.2]*10, "Cavity_2": [30.22]*10})
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df_temp.to_excel(writer, index=False); return out.getvalue()

    col_file, col_temp = st.columns([3, 1])
    with col_temp: st.download_button("📄 템플릿 받기", get_cavity_template(), "Quality_Template.xlsx", use_container_width=True)
    with col_file: uploaded_file = st.file_uploader("분석 파일 업로드 (xlsx/csv)", type=["xlsx", "csv"], key=f"cav_{st.session_state.reset_key}")

    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(all_vals.min()) - 0.02, float(all_vals.max()) + 0.02]
        
        st.subheader("🔍 캐비티별 정밀 분포")
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
                # [에러수정] byte=True 제거 및 폰트 설정 최적화
                fig_ind.update_layout(title=f"<b>{cav} 분석</b>", yaxis_range=y_range, height=320,
                                      xaxis=dict(tickfont=dict(size=11)), yaxis=dict(tickfont=dict(size=11)))
                st.plotly_chart(fig_ind, use_container_width=True)
                summary_results.append({"cav": cav, "ng": len(df[df[f"{cav}_판정"]=="NG"]), "total": len(df)})
                st.markdown('</div>', unsafe_allow_html=True)

        # [복구] 하단 요약 리포트
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📝 품질 분석 상세 리포트")
        total_ng_sum = sum(r['ng'] for r in summary_results)
        report_content = f"### 📢 종합 판정: {'❌ 부적합 (NG 발생)' if total_ng_sum > 0 else '✅ 양호 (전 항목 합격)'}\n"
        for res in summary_results:
            rate = ((res['total']-res['ng'])/res['total'])*100
            report_content += f"- **{res['cav']}**: 합격률 {rate:.1f}% | 불량 {res['ng']}건 / 전체 {res['total']}건\n"
        st.markdown(f'<div class="report-text">{report_content}</div>', unsafe_allow_html=True)
        
        output_res = BytesIO()
        with pd.ExcelWriter(output_res, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
        st.download_button("📥 통합 분석 엑셀 저장", output_res.getvalue(), "Quality_Full_Report.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 시스템")
    
    with st.expander("📂 데이터 입력 및 설정", expanded=True):
        h1, h2 = st.columns([5, 1])
        with h2: 
            if st.button("🔄 데이터 리셋", use_container_width=True): full_reset()
        c1, c2 = st.columns([1, 2])
        with c1:
            mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
        with c2:
            file = st.file_uploader("엑셀 업로드", type=["xlsx"], key=f"mmc_up_{st.session_state.reset_key}")

    if file: df_m = pd.read_excel(file)
    else:
        df_m = pd.DataFrame({"측정포인트": [1, 2, 3, 4], "기본공차": [0.3]*4, "도면치수_X": [10.0]*4, "도면치수_Y": [20.0]*4, "측정치_X": [10.02, 10.05, 9.98, 10.15], "측정치_Y": [20.01, 20.03, 19.95, 20.21], "실측지름_MMC용": [0.52, 0.55, 0.51, 0.58]})

    df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
    df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
    df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
    df_m['최종공차'] = df_m['기본공차'] + (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
    df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    fig_m = go.Figure()
    # 정원 유지 설정
    fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinewidth=2, zerolinecolor='black', tickfont=dict(size=14, color="black", byte=False))
    fig_m.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', tickfont=dict(size=14, color="black", byte=False))
    
    max_t = df_m['최종공차'].max() / 2
    fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=2), fillcolor="rgba(147, 112, 219, 0.1)")
    
    for _, row in df_m.iterrows():
        p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
        fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', 
                                   text=[f"<b>{int(row['측정포인트'])}</b>"], textposition="top center",
                                   textfont=dict(size=16, color="black"),
                                   marker=dict(size=14, color=p_c, line=dict(width=1.5, color='white'))))
    
    fig_m.update_layout(title="🎯 위치도 분석 과녁 (정원 보정)", width=700, height=700, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_m, use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.subheader("📊 위치도 분석 요약")
    res_c1, res_c2, res_c3 = st.columns(3)
    res_c1.metric("검사 포인트", f"{len(df_m)} EA")
    res_c2.metric("불량(NG)", f"{len(df_m[df_m['판정']=='NG'])} EA", delta_color="inverse")
    output_mmc = BytesIO()
    with pd.ExcelWriter(output_mmc, engine='xlsxwriter') as writer: df_m.to_excel(writer, index=False)
    res_c3.download_button("🚀 보고서 저장", output_mmc.getvalue(), "Position_Report.xlsx", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 4] 품질 계산기 (전체 복구) ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 현장 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["🎯 MMC 보너스", "🔧 토크/단위 환산", "⚖️ 공차 판정", "📊 통계분석"])
    
    with t1:
        c1, c2 = st.columns(2)
        m_type = c1.radio("대상 유형", ["구멍(Internal)", "축(External)"])
        m_geo = c2.number_input("도면 기하공차", value=0.050, format="%.3f")
        m_m, m_a = st.number_input("MMC 규격치", value=10.0), st.number_input("실측 데이터", value=10.02)
        bonus = max(0.0, m_a - m_m if "구멍" in m_type else m_m - m_a)
        st.info(f"계산된 보너스 공차: {bonus:.4f}")
        st.metric("최종 허용 위치도 공차", f"{m_geo + bonus:.4f}")
        
    with t2:
        st.subheader("🔧 변환 도구함")
        col_calc1, col_calc2 = st.columns(2)
        with col_calc1:
            st.markdown("**[토크 환산]**")
            v_t = st.number_input("토크 수치", value=1.0, key="torque_val")
            m_t = st.selectbox("단위 선택", ["N·m → kgf·m", "kgf·m → N·m"])
            res_t = v_t * 0.10197 if "kgf" in m_t else v_t * 9.80665
            st.success(f"결과: {res_t:.4f}")
        with col_calc2:
            st.markdown("**[단위 환산]**")
            v_u = st.number_input("수치 입력", value=1.0, key="unit_val")
            m_u = st.selectbox("항목 선택", ["mm → inch", "inch → mm", "mm → μm"])
            if "inch" in m_u: res_u = v_u / 25.4 if "mm →" in m_u else v_u * 25.4
            else: res_u = v_u * 1000
            st.success(f"결과: {res_u:.4f}")

    with t3:
        st.subheader("⚖️ 합격/불합격 판정")
        p1, p2, p3 = st.columns(3)
        base = p1.number_input("기준치", value=0.0)
        u_limit = p2.number_input("상한(+)", value=0.1)
        l_limit = p3.number_input("하한(-)", value=-0.1)
        ms_val = st.number_input("현재 측정값", value=0.0)
        if (base + l_limit) <= ms_val <= (base + u_limit): st.success("✅ 합격 (OK)")
        else: st.error("🚨 불합격 (NG)")

    with t4:
        st.subheader("📊 데이터 기초 통계")
        raw_data = st.text_area("데이터 입력 (쉼표로 구분, 예: 10.1, 10.2, 10.05)")
        if raw_data:
            try:
                nums = [float(x.strip()) for x in raw_data.split(",") if x.strip()]
                st.write(f"**평균:** {np.mean(nums):.4f}  |  **최대:** {np.max(nums):.4f}  |  **최소:** {np.min(nums):.4f}")
                st.write(f"**범위(R):** {np.ptp(nums):.4f}  |  **표준편차(σ):** {np.std(nums):.4f}")
            except: st.warning("올바른 숫자 형식을 입력하세요.")
    st.markdown('</div>', unsafe_allow_html=True)
