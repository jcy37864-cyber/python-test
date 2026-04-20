import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.9", layout="wide")

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
    .report-text { font-size: 1.1em; line-height: 1.8; color: #1e293b; white-space: pre-wrap; font-family: 'Malgun Gothic', sans-serif; }
    .ok-text { color: #10b981; font-weight: bold; }
    .ng-text { color: #e11d48; font-weight: bold; }
    
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); text-align: center; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 초기화
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

# --- [메뉴 2] 멀티 캐비티 분석 (리포트 복구) ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    uploaded_file = st.file_uploader("분석 파일 업로드", type=["xlsx", "csv"], key=f"cav_{st.session_state.reset_key}")

    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(np.nanmin(all_vals)) - 0.02, float(np.nanmax(all_vals)) + 0.02]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']

        # 요약 카드
        summary_results = []
        d_cols = st.columns(len(cav_cols))
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            ng_c = len(df[df[f"{cav}_판정"]=="NG"])
            rate = ((len(df)-ng_c)/len(df))*100
            d_cols[i].markdown(f'<div class="summary-card" style="border-top-color: {cav_colors[i%4]};"><b>{cav}</b><br><span class="{"ok-text" if rate==100 else "ng-text"}" style="font-size:1.6em;">{rate:.1f}%</span><br><small>NG: {ng_c} EA</small></div>', unsafe_allow_html=True)
            summary_results.append({"cav": cav, "ng": ng_c, "total": len(df)})

        # 그래프 및 트렌드
        st.subheader("🔍 데이터 분포 및 경향")
        c_grid = st.columns(2)
        for i, cav in enumerate(cav_cols):
            with c_grid[i % 2]:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                b_colors = ['#ef4444' if p == "NG" else cav_colors[i%4] for p in df[f"{cav}_판정"]]
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors, name=cav))
                fig.update_layout(title=f"<b>{cav} 상세</b>", yaxis_range=y_range, height=300)
                st.plotly_chart(fig, use_container_width=True)

        # [복구] 하단 상세 리포트
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📝 품질 분석 상세 리포트")
        total_ng = sum(r['ng'] for r in summary_results)
        report_txt = f"⚠️ 종합 판정: {'❌ 부적합' if total_ng > 0 else '✅ 양호'}\n\n"
        for res in summary_results:
            report_txt += f"• {res['cav']}: 합격률 {((res['total']-res['ng'])/res['total'])*100:.1f}% (불량: {res['ng']}건)\n"
        st.markdown(f'<div class="report-text">{report_txt}</div>', unsafe_allow_html=True)
        
        out_cav = BytesIO()
        with pd.ExcelWriter(out_cav, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
        st.download_button("📥 전체 결과(엑셀) 저장", out_cav.getvalue(), "Quality_Full_Report.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 (엑셀 이미지 저장 복구) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 및 보고서")
    
    with st.expander("📂 데이터 설정", expanded=True):
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

    # 과녁 시각화
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    fig_m = go.Figure()
    fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, tickfont=dict(size=14))
    fig_m.update_xaxes(zeroline=True, tickfont=dict(size=14))
    
    max_t = df_m['최종공차'].max() / 2
    fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=3), fillcolor="rgba(147, 112, 219, 0.1)")
    fig_m.add_shape(type="circle", x0=-(max_t+0.05), y0=-(max_t+0.05), x1=(max_t+0.05), y1=(max_t+0.05), line=dict(color="Red", width=1, dash="dot"))
    
    for _, row in df_m.iterrows():
        p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
        fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', 
                                   text=[f"<b>{int(row['측정포인트'])}</b>"], textposition="top center",
                                   textfont=dict(size=15, color="black"),
                                   marker=dict(size=12, color=p_c, line=dict(width=1, color='white'))))
    
    fig_m.update_layout(title="🎯 위치도 분석 과녁 (정원 유지)", width=650, height=650, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_m, use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    # 데이터 시트 및 [복구] 이미지 포함 엑셀 저장
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📋 분석 데이터 및 보고서 생성")
    st.dataframe(df_m.style.map(lambda x: 'background-color: #d1fae5' if x == 'OK' else 'background-color: #fee2e2', subset=['판정']), use_container_width=True)
    
    # 엑셀 다운로드 로직 (이미지 포함)
    def create_mmc_report(dataframe, plotly_fig):
        output = BytesIO()
        try: img_bytes = plotly_fig.to_image(format="png", width=700, height=700)
        except: img_bytes = None
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, sheet_name='Result', index=False)
            if img_bytes:
                worksheet = writer.sheets['Result']
                worksheet.insert_image('I2', 'graph.png', {'image_data': BytesIO(img_bytes), 'x_scale': 0.6, 'y_scale': 0.6})
        return output.getvalue()

    st.download_button("🚀 그래프 포함 엑셀 보고서 저장", create_mmc_report(df_m, fig_m), "Position_Final_Report.xlsx", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 4] 품질 계산기 ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 현장 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    t = st.tabs(["🎯 MMC 보너스", "🔧 환산도구", "⚖️ 공차 판정"])
    with t[0]:
        c1, c2 = st.columns(2)
        type_m = c1.radio("대상", ["구멍", "축"])
        geo_m = c2.number_input("도면 기하공차", value=0.05)
        mmc_s, act_s = st.number_input("MMC 규격", value=10.0), st.number_input("실측치", value=10.02)
        bonus = max(0.0, act_s - mmc_s if "구멍" in type_m else mmc_s - act_s)
        st.metric("최종 허용 공차", f"{geo_m + bonus:.4f}")
    with t[1]:
        v = st.number_input("값 입력", value=1.0)
        mode = st.selectbox("변환", ["N·m → kgf·m", "kgf·m → N·m", "mm → inch", "inch → mm"])
        if "N·m →" in mode: res = v * 0.10197
        elif "kgf·m" in mode: res = v * 9.80665
        elif "mm →" in mode: res = v / 25.4
        else: res = v * 25.4
        st.info(f"결과: {res:.4f}")
    with t[2]:
        p1, p2, p3 = st.columns(3)
        b, u, l = p1.number_input("기준"), p2.number_input("상한(+)"), p3.number_input("하한(-)")
        val = st.number_input("측정값")
        if (b+l) <= val <= (b+u): st.success("✅ 합격 (OK)")
        else: st.error("🚨 불합격 (NG)")
    st.markdown('</div>', unsafe_allow_html=True)
