import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 강화된 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.5", layout="wide")

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
        border-radius: 8px;
    }
    
    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 24px; }
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 20px; }
    .report-text { font-size: 1.1em; line-height: 1.8; color: #1e293b; white-space: pre-wrap; font-family: 'Malgun Gothic', sans-serif; }
    .ok-text { color: #10b981; font-weight: bold; }
    .ng-text { color: #e11d48; font-weight: bold; }
    
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); text-align: center; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 초기화 로직 ---
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

def full_reset():
    for key in list(st.session_state.keys()):
        if key != 'reset_key': del st.session_state[key]
    st.session_state.reset_key += 1
    st.rerun()

# --- 3. 사이드바 ---
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
    
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic", key=f"ed_{st.session_state.reset_key}")
    
    if st.button("🚀 변환 결과 생성", use_container_width=True):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row.get("X","")).strip(), str(row.get("Y","")).strip(), str(row.get("Z","")).strip()
            if x and y and z: results.extend([z, x, y])
        if results:
            res_df = pd.DataFrame(results, columns=["변환 결과"])
            st.session_state.trans_out = res_df

    if "trans_out" in st.session_state:
        st.dataframe(st.session_state.trans_out, use_container_width=True)
        st.download_button("📂 CSV 다운로드", st.session_state.trans_out.to_csv(index=False).encode('utf-8-sig'), "converted_data.csv", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [섹션 2] 멀티 캐비티 분석 (복구 완료) ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    
    def get_cavity_template():
        df_temp = pd.DataFrame({"Point": list(range(1, 55)), "SPEC_MIN": [30.03]*54, "SPEC_MAX": [30.38]*54, "Cavity_1": [30.2]*54, "Cavity_2": [30.22]*54, "Cavity_3": [30.18]*54, "Cavity_4": [30.25]*54})
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df_temp.to_excel(writer, index=False); return out.getvalue()

    col_f, col_t = st.columns([3, 1])
    with col_t: st.download_button("📄 템플릿 받기", get_cavity_template(), "Template.xlsx", use_container_width=True)
    with col_f: uploaded_file = st.file_uploader("분석 파일 업로드", type=["xlsx", "csv"], key=f"cav_{st.session_state.reset_key}")

    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(np.nanmin(all_vals)) - 0.02, float(np.nanmax(all_vals)) + 0.02]
        
        # 상단 요약 카드
        st.subheader("📋 품질현황 대쉬보드")
        summary_results = []
        d_cols = st.columns(len(cav_cols))
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            ng_count = len(df[df[f"{cav}_판정"]=="NG"])
            rate = ((len(df)-ng_count)/len(df))*100
            d_cols[i].markdown(f'<div class="summary-card"><b>{cav}</b><br><span class="{"ok-text" if rate==100 else "ng-text"}" style="font-size:1.5em;">{rate:.1f}%</span><br><small>NG: {ng_count} EA</small></div>', unsafe_allow_html=True)
            summary_results.append({"cav": cav, "ng": ng_count, "total": len(df)})

        # 그래프 그리드
        st.subheader("🔍 상세 분포 (정밀 스케일)")
        c_grid = st.columns(2)
        for i, cav in enumerate(cav_cols):
            with c_grid[i % 2]:
                st.markdown('<div class="stBox">', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                b_colors = ['#ef4444' if p == "NG" else '#1f77b4' for p in df[f"{cav}_판정"]]
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors, name="Data"))
                fig.update_layout(title=f"<b>{cav} Trend</b>", yaxis_range=y_range, height=300, margin=dict(l=10,r=10,t=40,b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # [복구] 하단 텍스트 상세 리포트
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📝 종합 분석 리포트 요약")
        total_ng = sum(r['ng'] for r in summary_results)
        report_text = f"**[판정 결과]**: {'🚨 부적합 (수정 필요)' if total_ng > 0 else '✅ 최종 합격 (양호)'}\n\n"
        for res in summary_results:
            report_text += f"- {res['cav']}: 총 {res['total']}포인트 중 {res['ng']}개 NG 발생 (합격률: {((res['total']-res['ng'])/res['total'])*100:.1f}%)\n"
        st.markdown(f'<div class="report-text">{report_text}</div>', unsafe_allow_html=True)
        
        out_excel = BytesIO()
        with pd.ExcelWriter(out_excel, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
        st.download_button("📥 전체 분석 결과(엑셀) 저장", out_excel.getvalue(), "Analysis_Report.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [섹션 3] 위치도 분석 (에러 수정 완료) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 시스템")
    
    with st.expander("📂 데이터 입력", expanded=True):
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
    # [에러완전수정] byte=False 등 불필요 인자 제거
    fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#eee', tickfont=dict(size=14, color="black"))
    fig_m.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#eee', tickfont=dict(size=14, color="black"))
    
    max_t = df_m['최종공차'].max() / 2
    fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=2), fillcolor="rgba(147, 112, 219, 0.1)")
    
    for _, row in df_m.iterrows():
        p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
        fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', 
                                   text=[f"<b>{int(row['측정포인트'])}</b>"], textposition="top center",
                                   textfont=dict(size=16, color="black"),
                                   marker=dict(size=14, color=p_c, line=dict(width=1.5, color='white'))))
    
    fig_m.update_layout(title="🎯 위치도 분석 과녁 (정원 유지)", width=700, height=700, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_m, use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.subheader("📊 위치도 분석 요약")
    r1, r2, r3 = st.columns(3)
    r1.metric("전체 포인트", f"{len(df_m)} EA")
    r2.metric("불량 발생", f"{len(df_m[df_m['판정']=='NG'])} EA")
    out_mmc = BytesIO()
    with pd.ExcelWriter(out_mmc, engine='xlsxwriter') as writer: df_m.to_excel(writer, index=False)
    r3.download_button("🚀 위치도 결과 저장", out_mmc.getvalue(), "Position_Result.xlsx", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [섹션 4] 품질 계산기 (전체 복구) ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 현장 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    tabs = st.tabs(["🎯 MMC 보너스", "🔧 토크/단위 환산", "⚖️ 공차 판정", "📊 통계분석"])
    
    with tabs[0]:
        cc1, cc2 = st.columns(2)
        m_t = cc1.radio("유형", ["구멍", "축"])
        m_g = cc2.number_input("도면공차", value=0.050, format="%.3f")
        m_m, m_a = st.number_input("MMC 규격", value=10.0), st.number_input("실측치", value=10.02)
        bonus = max(0.0, m_a - m_m if "구멍" in m_t else m_m - m_a)
        st.metric("최종 허용 공차", f"{m_g + bonus:.4f}")
        
    with tabs[1]:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.write("**[토크 변환]**")
            v_t = st.number_input("값", value=1.0, key="tk")
            m_t = st.selectbox("단위", ["N·m → kgf·m", "kgf·m → N·m"])
            st.success(f"결과: {v_t * 0.10197:.4f}" if "kgf" in m_t else f"결과: {v_t * 9.80665:.4f}")
        with col_c2:
            st.write("**[단위 변환]**")
            v_u = st.number_input("값", value=1.0, key="un")
            m_u = st.selectbox("항목", ["mm → inch", "inch → mm", "mm → μm"])
            if "inch" in m_u: res = v_u / 25.4 if "mm" in m_u[:2] else v_u * 25.4
            else: res = v_u * 1000
            st.success(f"결과: {res:.4f}")

    with tabs[2]:
        st.write("**[상하한 판정]**")
        p1, p2, p3 = st.columns(3)
        base = p1.number_input("기준값", value=0.0)
        up = p2.number_input("상한(+)", value=0.1)
        lo = p3.number_input("하한(-)", value=-0.1)
        meas = st.number_input("측정치", value=0.0, key="ms_p")
        if (base + lo) <= meas <= (base + up): st.success("✅ 합격 (OK)")
        else: st.error("🚨 불합격 (NG)")

    with tabs[3]:
        st.write("**[기초 통계]**")
        raw = st.text_area("데이터 (쉼표 구분)")
        if raw:
            try:
                ns = [float(x.strip()) for x in raw.split(",") if x.strip()]
                st.write(f"평균: {np.mean(ns):.4f} | σ: {np.std(ns):.4f} | R: {np.ptp(ns):.4f}")
            except: st.error("형식을 확인하세요.")
    st.markdown('</div>', unsafe_allow_html=True)
