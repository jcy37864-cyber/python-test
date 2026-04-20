import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v7.4", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #ef4444 !important; color: white !important; font-weight: bold !important;
        height: 3.5em !important; margin-top: 20px !important; border-radius: 8px;
    }
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    .report-text { font-size: 1.05em; line-height: 1.6; color: #1e293b; white-space: pre-wrap; }
    </style>
""", unsafe_allow_html=True)

# 초기화
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- 2. 사이드바 메뉴 ---
st.sidebar.title("🚀 품질 분석 메뉴")
menu = st.sidebar.radio("📋 업무 선택", ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"])

if st.sidebar.button("🧹 전체 초기화", use_container_width=True):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- [메뉴 1] 데이터 변환기 ---
if menu == "🔄 데이터 변환기":
    st.title("🔄 좌표 데이터 변환기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    df_input = st.data_editor(pd.DataFrame({"X": [""]*10, "Y": [""]*10, "Z": [""]*10}), num_rows="dynamic", use_container_width=True)
    if st.button("🚀 변환 실행", use_container_width=True):
        res = []
        for _, r in df_input.iterrows():
            if str(r['X']).strip(): res.extend([r['Z'], r['X'], r['Y']])
        if res:
            df_res = pd.DataFrame(res, columns=["변환 데이터 (Z-X-Y)"])
            st.dataframe(df_res, use_container_width=True)
            st.download_button("📥 CSV 다운로드", df_res.to_csv(index=False).encode('utf-8-sig'), "converted_coords.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 2] 멀티 캐비티 분석 ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    def get_cav_template():
        df_t = pd.DataFrame({"Point": range(1,6), "SPEC_MIN": [30.1]*5, "SPEC_MAX": [30.5]*5, "Cavity_1": [30.2]*5, "Cavity_2": [30.3]*5})
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df_t.to_excel(writer, index=False)
        return out.getvalue()
    st.download_button("📄 멀티캐비티 템플릿 받기", get_cav_template(), "Multi_Cavity_Template.xlsx", use_container_width=True)
    
    up = st.file_uploader("분석 파일 업로드", type=["xlsx", "csv"])
    if up:
        df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_min, y_max = np.nanmin(all_vals) - 0.02, np.nanmax(all_vals) + 0.02
        
        c_grid = st.columns(2)
        summary_info = []
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            ng_count = len(df[df[f"{cav}_판정"]=="NG"])
            summary_info.append(f"• {cav}: 합격률 {((len(df)-ng_count)/len(df))*100:.1f}% (불량 {ng_count}건)")
            with c_grid[i % 2]:
                st.markdown(f'<div class="stBox"><b>{cav} 정밀 시각화</b>', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=['#ef4444' if p=="NG" else '#1f77b4' for p in df[f"{cav}_판정"]]))
                fig.update_layout(height=280, yaxis_range=[y_min, y_max], margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 트렌드 및 요약")
        df['Avg'] = df[cav_cols].mean(axis=1)
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Avg'], name="평균선", line=dict(color="black", width=3)))
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown(f'<div class="report-text">{"/n".join(summary_info)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 (템플릿 및 이미지 기능 복구) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 (MMC)")
    
    # [복구] 위치도 전용 템플릿 다운로드 버튼
    def get_pos_template():
        df_pt = pd.DataFrame({
            "측정포인트": [1, 2, 3], 
            "기본공차": [0.3]*3, 
            "도면치수_X": [10.0, 20.0, 30.0], 
            "도면치수_Y": [10.0, 20.0, 30.0], 
            "측정치_X": [10.02, 20.05, 30.15], 
            "측정치_Y": [10.01, 20.03, 30.08], 
            "실측지름_MMC용": [0.52, 0.55, 0.58]
        })
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df_pt.to_excel(writer, index=False)
        return out.getvalue()
    
    st.download_button("📄 위치도 분석 템플릿 받기", get_pos_template(), "Position_Analysis_Template.xlsx", use_container_width=True)

    c1, c2 = st.columns([1, 2])
    with c1: mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
    with c2: file = st.file_uploader("데이터 업로드 (위 템플릿 양식)", type=["xlsx"])

    if file:
        df_m = pd.read_excel(file)
        df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
        df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
        df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
        df_m['최종공차'] = df_m['기본공차'] + (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
        df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🎯 분석 결과 시각화")
        fig_m = go.Figure()
        fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinecolor='black')
        fig_m.update_xaxes(zeroline=True, zerolinecolor='black')
        
        # 가이드라인 (Blue, Purple, Red)
        max_t = df_m['최종공차'].max() / 2
        fig_m.add_shape(type="circle", x0=-0.05, y0=-0.05, x1=0.05, y1=0.05, line=dict(color="Blue", width=1, dash="dot"))
        fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=3), fillcolor="rgba(147, 112, 219, 0.1)")
        fig_m.add_shape(type="circle", x0=-(max_t+0.05), y0=-(max_t+0.05), x1=(max_t+0.05), y1=(max_t+0.05), line=dict(color="Red", width=1, dash="dash"))
        
        for _, row in df_m.iterrows():
            p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
            fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', text=[f"<b>{int(row['측정포인트'])}</b>"], textposition="top center", marker=dict(size=12, color=p_c, line=dict(width=1, color='white'))))
        
        st.info("💡 데이터 업로드 시 아래 그래프가 자동으로 생성됩니다. 우측 상단 카메라 아이콘으로 PNG 저장이 가능합니다.")
        st.plotly_chart(fig_m, use_container_width=False, config={'toImageButtonOptions': {'format': 'png', 'filename': 'target_chart', 'scale': 2}})
        
        # 결과 표 및 엑셀 다운로드
        st.dataframe(df_m.style.map(lambda x: 'background-color: #d1fae5' if x == 'OK' else 'background-color: #fee2e2', subset=['판정']), use_container_width=True)
        out_pos = BytesIO()
        with pd.ExcelWriter(out_pos, engine='xlsxwriter') as writer: df_m.to_excel(writer, index=False)
        st.download_button("📥 분석 결과 엑셀 저장", out_pos.getvalue(), "Position_Result.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 4] 품질 계산기 (복구) ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🎯 MMC 보너스", "🔧 단위 환산", "⚖️ 공차 판정"])
    with t1:
        c1, c2 = st.columns(2)
        base = c2.number_input("기본 기하공차", value=0.05)
        spec = st.number_input("MMC 규격", value=10.0)
        act = st.number_input("실측치", value=10.02)
        bonus = max(0, act - spec)
        st.metric("최종 허용 공차", f"{base + bonus:.4f}")
    with t2:
        val = st.number_input("입력값", value=1.0)
        mode = st.selectbox("변환", ["mm ➔ inch", "inch ➔ mm", "kgf·m ➔ N·m"])
        res = val/25.4 if "inch" in mode[:4] else val*25.4 if "mm" in mode[7:] else val*9.80665
        st.success(f"결과: {res:.4f}")
    with t3:
        target, u, l = st.number_input("기준"), st.number_input("상한"), st.number_input("하한")
        m = st.number_input("측정값 ")
        if (target+l) <= m <= (target+u): st.success("✅ 합격")
        else: st.error("🚨 불합격")
    st.markdown('</div>', unsafe_allow_html=True)
