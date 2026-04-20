import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.8", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
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
    .ok-text { color: #10b981; font-weight: bold; }
    .ng-text { color: #e11d48; font-weight: bold; }
    
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); text-align: center; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

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

# --- [메뉴 1] 데이터 변환기 ---
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
            st.session_state.trans_res = pd.DataFrame(results, columns=["변환 결과"])

    if "trans_res" in st.session_state:
        st.dataframe(st.session_state.trans_res, use_container_width=True)
        st.download_button("📂 CSV 다운로드", st.session_state.trans_res.to_csv(index=False).encode('utf-8-sig'), "converted_data.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 2] 멀티 캐비티 분석 ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    
    col_file, col_temp = st.columns([3, 1])
    with col_file: uploaded_file = st.file_uploader("분석 파일 업로드", type=["xlsx", "csv"], key=f"cav_{st.session_state.reset_key}")

    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(np.nanmin(all_vals)) - 0.02, float(np.nanmax(all_vals)) + 0.02]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']

        # 요약 카드 대시보드
        d_cols = st.columns(len(cav_cols))
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            ng_c = len(df[df[f"{cav}_판정"]=="NG"])
            rate = ((len(df)-ng_c)/len(df))*100
            d_cols[i].markdown(f'<div class="summary-card" style="border-top-color: {cav_colors[i%4]};"><b>{cav}</b><br><span class="{"ok-text" if rate==100 else "ng-text"}" style="font-size:1.6em;">{rate:.1f}%</span><br><small>NG: {ng_c} EA</small></div>', unsafe_allow_html=True)

        # 개별 그래프
        st.subheader("🔍 캐비티별 상세 분포")
        c_grid = st.columns(2)
        for i, cav in enumerate(cav_cols):
            with c_grid[i % 2]:
                st.markdown('<div class="stBox">', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                b_colors = ['#ef4444' if p == "NG" else cav_colors[i%4] for p in df[f"{cav}_판정"]]
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors, name="Data"))
                fig.update_layout(title=f"<b>{cav} 분석</b>", yaxis_range=y_range, height=300)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # [복구] 통합 트렌드
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 경향성 분석")
        fig_total = go.Figure()
        df['Avg'] = df[cav_cols].mean(axis=1)
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="MIN", line=dict(color="blue", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="MAX", line=dict(color="red", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Avg'], name="평균", line=dict(color="black", width=3)))
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', marker=dict(color=cav_colors[i%4], opacity=0.4)))
        fig_total.update_layout(height=450, template="plotly_white")
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 (에러 해결 & 과녁 복구) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 시스템")
    
    with st.expander("📂 데이터 입력", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1: mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
        with c2: file = st.file_uploader("엑셀 업로드", type=["xlsx"], key=f"mmc_up_{st.session_state.reset_key}")

    if file: df_m = pd.read_excel(file)
    else:
        df_m = pd.DataFrame({"측정포인트": [1, 2, 3, 4, 5, 6, 7, 8], "기본공차": [0.30] * 8, "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1], "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3], "측정치_X": [-55.71, -35.79, -14.81, 5.10, -45.52, -5.09, -55.74, 5.11], "측정치_Y": [-38.82, -38.80, -38.79, -38.81, -54.72, -54.68, -70.32, -70.31], "실측지름_MMC용": [0.55, 0.52, 0.53, 0.55, 0.51, 0.50, 0.56, 0.54]})

    df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
    df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
    df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
    df_m['최종공차'] = df_m['기본공차'] + (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
    df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    fig_m = go.Figure()
    fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinewidth=2, zerolinecolor='black', tickfont=dict(size=15, color="black"))
    fig_m.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', tickfont=dict(size=15, color="black"))
    
    # [복구] 과녁 컬러 가이드
    max_t = df_m['최종공차'].max() / 2
    fig_m.add_shape(type="circle", x0=-0.05, y0=-0.05, x1=0.05, y1=0.05, line=dict(color="Blue", width=1, dash="dot"))
    fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=3), fillcolor="rgba(147, 112, 219, 0.1)")
    fig_m.add_shape(type="circle", x0=-(max_t+0.05), y0=-(max_t+0.05), x1=(max_t+0.05), y1=(max_t+0.05), line=dict(color="Red", width=1.5, dash="dashdot"))
    
    for _, row in df_m.iterrows():
        p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
        fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', 
                                   text=[f"<b>{int(row['측정포인트'])}</b>"], textposition="top center",
                                   textfont=dict(size=16, color="black"),
                                   marker=dict(size=14, color=p_c, line=dict(width=1, color='white'))))
    
    fig_m.update_layout(title="🎯 위치도 분석 과녁 (색상 복구 완료)", width=700, height=700, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_m, use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    # [에러수정] applymap -> map으로 변경
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📋 상세 분석 데이터")
    def color_ok_ng(val):
        return 'background-color: #d1fae5' if val == 'OK' else 'background-color: #fee2e2'
    st.dataframe(df_m.style.map(color_ok_ng, subset=['판정']), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 4] 품질 계산기 ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 현장 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    t = st.tabs(["🎯 MMC 보너스", "🔧 토크/단위 환산", "⚖️ 공차 판정", "📊 통계분석"])
    
    with t[0]:
        c1, c2 = st.columns(2)
        type_m = c1.radio("대상", ["구멍", "축"])
        geo_m = c2.number_input("기본 기하공차", value=0.05)
        mmc_s, act_s = st.number_input("MMC 규격", value=10.0), st.number_input("실측치", value=10.02)
        bonus = max(0.0, act_s - mmc_s if "구멍" in type_m else mmc_s - act_s)
        st.metric("최종 허용 공차", f"{geo_m + bonus:.4f}")
        
    with t[1]:
        col1, col2 = st.columns(2)
        with col1:
            v_t = st.number_input("토크값", value=1.0, key="tk")
            unit_t = st.selectbox("변환", ["N·m → kgf·m", "kgf·m → N·m"])
            st.success(f"결과: {v_t * 0.10197:.4f}" if "kgf" in unit_t else f"결과: {v_t * 9.80665:.4f}")
        with col2:
            v_u = st.number_input("길이값", value=1.0, key="ln")
            unit_u = st.selectbox("항목", ["mm → inch", "inch → mm", "mm → μm"])
            if "inch" in unit_u: res = v_u / 25.4 if "mm" in unit_u[:2] else v_u * 25.4
            else: res = v_u * 1000
            st.success(f"결과: {res:.4f}")
    
    with t[2]:
        p1, p2, p3 = st.columns(3)
        b, u, l = p1.number_input("기준"), p2.number_input("상한(+)"), p3.number_input("하한(-)")
        val = st.number_input("측정값")
        if (b+l) <= val <= (b+u): st.success("✅ 합격 (OK)")
        else: st.error("🚨 불합격 (NG)")

    with t[3]:
        raw = st.text_area("데이터 (쉼표 구분)")
        if raw:
            try:
                ns = [float(x.strip()) for x in raw.split(",") if x.strip()]
                st.write(f"평균: {np.mean(ns):.4f} | σ: {np.std(ns):.4f}")
            except: st.error("숫자 형식이 아닙니다.")
    st.markdown('</div>', unsafe_allow_html=True)
