import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. 페이지 설정 및 공통 스타일 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.0", layout="wide")

st.markdown("""
    <style>
    /* 기본 배경 및 폰트 */
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* 카드형 컨테이너 */
    .stBox { 
        background-color: #ffffff; padding: 24px; border-radius: 16px; 
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        margin-bottom: 24px; 
    }
    
    /* 가이드 및 요약 박스 */
    .guide-box { 
        background-color: #eff6ff; padding: 15px; border-radius: 10px; 
        border: 1px solid #bfdbfe; color: #1e40af; font-size: 0.95em; margin-bottom: 20px;
    }
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 10px; text-align: center;
    }
    
    /* 텍스트 강조 */
    .ng-text { color: #e11d48; font-weight: bold; }
    .ok-text { color: #10b981; font-weight: bold; }
    .report-text { font-size: 1.05em; line-height: 1.8; color: #1e293b; white-space: pre-wrap; }
    
    /* 버튼 스타일 */
    div.stDownloadButton > button {
        width: 100% !important; font-weight: bold !important;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False

# --- 2. 초기화 및 공통 함수 ---
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

def reset_app():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 3. 사이드바 구성 ---
st.sidebar.title("🛠️ 분석 도구함")
menu = st.sidebar.radio("📋 메뉴 선택", 
    ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"])

if st.sidebar.button("🧹 전체 초기화 (Reset)", use_container_width=True):
    reset_app()

# --- 🔄 메뉴 1: 데이터 변환기 (섹션 1 통합) ---
if menu == "🔄 데이터 변환기":
    st.title("🔄 좌표 데이터 변환기")
    st.markdown('<div class="guide-box"><b>💡 가이드:</b> Z, X, Y 순서로 1열 정렬이 필요한 데이터를 처리합니다.</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 10, "Y": [""] * 10, "Z": [""] * 10})
    
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")
    
    if st.button("🚀 ZXY 시퀀스 생성", use_container_width=True):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row.get("X","")).strip(), str(row.get("Y","")).strip(), str(row.get("Z","")).strip()
            if x and y and z: results.extend([z, x, y])
        if results:
            res_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(res_df, use_container_width=True)
            st.download_button("📂 결과 CSV 다운로드", res_df.to_csv(index=True).encode("utf-8-sig"), "zxy_result.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 📈 메뉴 2: 멀티 캐비티 분석 (섹션 2 통합) ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📈 멀티 캐비티 통합 분석")
    
    def get_cavity_template():
        df_temp = pd.DataFrame({
            "Point": list(range(1, 11)), "SPEC_MIN": [30.00]*10, "SPEC_MAX": [30.50]*10,
            "Cavity_1": [30.2]*10, "Cavity_2": [30.22]*10, "Cavity_3": [30.18]*10, "Cavity_4": [30.25]*10
        })
        out = BytesIO(); 
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df_temp.to_excel(writer, index=False)
        return out.getvalue()

    col_f1, col_f2 = st.columns([3, 1])
    with col_f2: st.download_button("📄 분석 템플릿 받기", get_cavity_template(), "Cavity_Template.xlsx")
    with col_f1: uploaded_file = st.file_uploader("파일 업로드", type=["xlsx", "csv"], key=f"cav_{st.session_state.reset_key}")

    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        
        # 1. 상세 분포 (개별 그래프)
        st.subheader("🔍 캐비티별 상세 분포")
        c_grid = st.columns(2)
        summary_results = []
        cav_colors = ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6']
        
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            with c_grid[i % 2]:
                st.markdown('<div class="stBox">', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                colors = ['#ef4444' if p == "NG" else cav_colors[i % 4] for p in df[f"{cav}_판정"]]
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=colors, name=cav))
                fig.update_layout(title=f"<b>{cav} 분석</b>", height=300, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)
                summary_results.append({"cav": cav, "ng": len(df[df[f"{cav}_판정"]=="NG"]), "total": len(df), "color": cav_colors[i % 4]})
                st.markdown('</div>', unsafe_allow_html=True)

        # 2. 요약 대시보드
        st.subheader("📋 실시간 품질 현황")
        d_cols = st.columns(len(summary_results))
        for i, res in enumerate(summary_results):
            rate = ((res['total'] - res['ng']) / res['total']) * 100
            d_cols[i].markdown(f'<div class="summary-card" style="border-top-color: {res["color"]};">'
                               f'<small>{res["cav"]}</small><br><span class="{"ok-text" if rate==100 else "ng-text"}" style="font-size:1.5em;">{rate:.1f}%</span><br>'
                               f'<small>NG: {res["ng"]}</small></div>', unsafe_allow_html=True)

        # 3. 평균 Trend 및 통합 엑셀 다운로드
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        df['Average'] = df[cav_cols].mean(axis=1)
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Average'], name="평균 Trend", line=dict(color="black", width=3)))
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', marker=dict(size=6, opacity=0.4)))
        st.plotly_chart(fig_total, use_container_width=True)
        
        # 엑셀 보고서 생성
        output_res = BytesIO()
        with pd.ExcelWriter(output_res, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Analysis')
        st.download_button("📥 통합 분석 보고서(XLSX) 저장", output_res.getvalue(), "Cavity_Report.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 🎯 메뉴 3: 위치도(MMC) 분석 (섹션 3 통합) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 및 MMC 정밀 분석")
    
    def get_mmc_template():
        df_temp = pd.DataFrame({"측정포인트": range(1, 9), "기본공차": [0.3]*8, "도면치수_X": [0.0]*8, "도면치수_Y": [0.0]*8, "측정치_X": [0.01]*8, "측정치_Y": [-0.01]*8, "실측지름_MMC용": [0.55]*8})
        out = BytesIO(); 
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df_temp.to_excel(writer, index=False)
        return out.getvalue()

    st.markdown("""<div class="guide-box"><b>과녁 가이드:</b> 🔵기본규격 | 🟣MMC보너스 합격선 | 🔴NG 마지노선</div>""", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.download_button("📥 위치도 양식 받기", get_mmc_template(), "MMC_Template.xlsx")
        mmc_base = st.number_input("MMC 기준값(Min 지름)", value=0.500, format="%.3f")
    with c2:
        file = st.file_uploader("데이터 업로드", type=["xlsx"], key=f"mmc_{st.session_state.reset_key}")

    if file: df_m = pd.read_excel(file)
    else: df_m = pd.DataFrame({"측정포인트": [1], "기본공차": [0.3], "도면치수_X": [0], "도면치수_Y": [0], "측정치_X": [0.05], "측정치_Y": [0.08], "실측지름_MMC용": [0.52]})

    # 계산
    df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
    df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
    df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
    df_m['보너스'] = (df_m['실측지름_MMC용'] - mmc_base).clip(lower=0)
    df_m['최종공차'] = df_m['기본공차'] + df_m['보너스']
    df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

    # 그래프
    fig_m = go.Figure()
    fig_m.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#eee')
    fig_m.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#eee')
    
    # 공차 원들
    fig_m.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, line=dict(color="Blue", dash="dot"))
    max_t = df_m['최종공차'].max() / 2
    fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=2), fillcolor="rgba(147, 112, 219, 0.1)")
    fig_m.add_shape(type="circle", x0=-(max_t+0.02), y0=-(max_t+0.02), x1=(max_t+0.02), y1=(max_t+0.02), line=dict(color="Red", dash="dashdot"))

    for _, row in df_m.iterrows():
        color = '#10b981' if row['판정'] == "OK" else '#ef4444'
        fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', text=[f"<b>{row['측정포인트']}</b>"], textposition="top center", marker=dict(size=12, color=color, line=dict(width=1, color='white'))))
    
    fig_m.update_layout(xaxis_range=[-0.35, 0.35], yaxis_range=[-0.35, 0.35], height=600, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_m, use_container_width=True)
    
    st.dataframe(df_m.style.map(lambda x: 'color:red; font-weight:bold' if x == 'NG' else '', subset=['판정']), use_container_width=True)

# --- 🧮 메뉴 4: 품질 계산기 (섹션 1 통합) ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 현장용 간편 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    tabs = st.tabs(["🎯 MMC 보너스", "⚖️ 공차 판정", "🔧 토크 변환", "📏 단위 변환", "📊 기초 통계"])
    
    with tabs[0]:
        c1, c2 = st.columns(2)
        m_type = c1.radio("유형", ["구멍 (Hole)", "축 (Shaft)"], horizontal=True)
        m_geo = c2.number_input("도면 기하공차", value=0.05, format="%.3f")
        m_mmc, m_act = st.number_input("MMC 규격 지름", value=10.0), st.number_input("실측 지름", value=10.02)
        bonus = max(0.0, m_act - m_mmc if "구멍" in m_type else m_mmc - m_act)
        st.metric("최종 허용 공차 (기하+보너스)", f"{m_geo + bonus:.4f}")
        
    with tabs[1]:
        p1, p2, p3, p4 = st.columns(4)
        base = p1.number_input("기준치", value=10.0)
        u_t = p2.number_input("상한(+)", value=0.1)
        l_t = p3.number_input("하한(-)", value=-0.1)
        ms = p4.number_input("측정치", value=10.05)
        if (base + l_t) <= ms <= (base + u_t): st.success("✅ 규격 이내 (OK)")
        else: st.error("🚨 규격 이탈 (NG)")
        
    with tabs[2]:
        v = st.number_input("수치 입력", value=1.0)
        m = st.selectbox("변환 선택", ["N·m → kgf·m", "kgf·m → N·m"])
        res = v * 0.101972 if "kgf" in m else v * 9.80665
        st.info(f"계산 결과: {res:.4f}")

    with tabs[4]:
        data_str = st.text_area("데이터 입력 (쉼표로 구분, 예: 10.1, 10.2, 9.9)")
        if data_str:
            try:
                nums = [float(x.strip()) for x in data_str.split(",") if x.strip()]
                st.write(f"**평균:** {np.mean(nums):.4f}  |  **범위(R):** {np.ptp(nums):.4f}  |  **표준편차:** {np.std(nums):.4f}")
            except: st.error("숫자 형식을 확인해주세요.")
    st.markdown('</div>', unsafe_allow_html=True)
