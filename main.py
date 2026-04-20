import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v8.1", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
    .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); margin-bottom: 25px; }
    
    /* 리포트 강조 디자인 */
    .report-card {
        background-color: #f1f5f9; padding: 20px; border-left: 10px solid #3b82f6;
        border-radius: 8px; line-height: 2.0; font-size: 1.1em; color: #1e293b;
    }
    .ok-badge { background-color: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .ng-badge { background-color: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- 2. 사이드바 ---
st.sidebar.title("💎 품질 통합 플랫폼 v8.1")
menu = st.sidebar.radio("📋 업무 선택", ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"], key=f"m_{st.session_state.reset_key}")

if st.sidebar.button("🧹 모든 데이터 초기화", use_container_width=True):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.reset_key += 1
    st.rerun()

# --- [메뉴 1] 데이터 변환기 ---
if menu == "🔄 데이터 변환기":
    st.title("🔄 좌표 데이터 변환기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    df_input = st.data_editor(pd.DataFrame({"X": [""]*10, "Y": [""]*10, "Z": [""]*10}), num_rows="dynamic", use_container_width=True)
    if st.button("🚀 데이터 변환 실행", use_container_width=True):
        res = []
        for _, r in df_input.iterrows():
            if str(r['X']).strip(): res.extend([r['Z'], r['X'], r['Y']])
        if res:
            df_res = pd.DataFrame(res, columns=["변환 데이터 (Z-X-Y)"])
            st.dataframe(df_res, use_container_width=True)
            st.download_button("📥 결과 CSV 저장", df_res.to_csv(index=False).encode('utf-8-sig'), "converted_data.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 2] 멀티 캐비티 분석 (색상 동기화 및 리포트 강화) ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    
    def get_cav_template():
        df_t = pd.DataFrame({"Point": range(1,6), "SPEC_MIN": [30.1]*5, "SPEC_MAX": [30.5]*5, "Cavity_1": [30.2]*5, "Cavity_2": [30.3]*5, "Cavity_3": [30.2]*5, "Cavity_4": [30.4]*5})
        out = BytesIO(); writer = pd.ExcelWriter(out, engine='xlsxwriter'); df_t.to_excel(writer, index=False); writer.close()
        return out.getvalue()
    st.download_button("📄 분석용 템플릿 다운로드", get_cav_template(), "Multi_Cavity_Template.xlsx", use_container_width=True)
    
    up = st.file_uploader("파일 업로드", type=["xlsx", "csv"])
    if up:
        df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'] # 고정 색상 팔레트
        
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_min, y_max = np.nanmin(all_vals) - 0.03, np.nanmax(all_vals) + 0.03
        
        c_grid = st.columns(2)
        summary_items = []
        
        for i, cav in enumerate(cav_cols):
            color = cav_colors[i % len(cav_colors)]
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            ng_cnt = len(df[df[f"{cav}_판정"]=="NG"])
            rate = ((len(df)-ng_cnt)/len(df))*100
            
            badge = f'<span class="ok-badge">OK</span>' if ng_cnt == 0 else f'<span class="ng-badge">NG {ng_cnt}</span>'
            summary_items.append(f"✅ **{cav}**: 합격률 **{rate:.1f}%** ({badge})")
            
            with c_grid[i % 2]:
                st.markdown(f'<div class="stBox"><b style="color:{color}; font-size:1.2em;">{cav}</b>', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                # 실측 바 그래프 (개별 색상 적용)
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=color, name=f"{cav} 실측"))
                fig.update_layout(height=280, yaxis_range=[y_min, y_max], margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 트렌드 분석 (캐비티별 색상 매칭)")
        fig_total = go.Figure()
        df['Avg'] = df[cav_cols].mean(axis=1)
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="MIN", line=dict(color="blue", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="MAX", line=dict(color="red", dash="dot")))
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], mode='markers', name=cav, marker=dict(color=cav_colors[i%len(cav_colors)], size=10)))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Avg'], name="전체평균", line=dict(color="black", width=3)))
        fig_total.update_layout(height=450, yaxis_range=[y_min, y_max])
        st.plotly_chart(fig_total, use_container_width=True)
        
        # 종합 리포트 레이아웃 강화
        st.subheader("📝 종합 분석 리포트")
        report_html = "<br>".join(summary_items)
        st.markdown(f'<div class="report-card">{report_html}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 (다운로드 버튼 복구 및 강화) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 (MMC)")
    def get_pos_template():
        df_pt = pd.DataFrame({"측정포인트": [1], "기본공차": [0.3], "도면치수_X": [10.0], "도면치수_Y": [10.0], "측정치_X": [10.02], "측정치_Y": [10.01], "실측지름_MMC용": [0.52]})
        out = BytesIO(); writer = pd.ExcelWriter(out, engine='xlsxwriter'); df_pt.to_excel(writer, index=False); writer.close()
        return out.getvalue()
    st.download_button("📄 위치도 템플릿 다운로드", get_pos_template(), "Position_Template.xlsx", use_container_width=True)

    c1, c2 = st.columns([1, 2])
    with c1: mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
    with c2: file = st.file_uploader("파일 업로드", type=["xlsx"])

    if file:
        df_m = pd.read_excel(file)
        df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
        df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
        df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
        df_m['최종공차'] = df_m['기본공차'] + (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
        df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        fig_m = go.Figure()
        fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinecolor='black')
        fig_m.update_xaxes(zeroline=True, zerolinecolor='black')
        max_t = df_m['최종공차'].max() / 2
        fig_m.add_shape(type="circle", x0=-0.05, y0=-0.05, x1=0.05, y1=0.05, line=dict(color="Blue", width=1, dash="dot"))
        fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=3), fillcolor="rgba(147, 112, 219, 0.1)")
        fig_m.add_shape(type="circle", x0=-(max_t+0.05), y0=-(max_t+0.05), x1=(max_t+0.05), y1=(max_t+0.05), line=dict(color="Red", width=1, dash="dash"))
        for _, r in df_m.iterrows():
            p_c = '#10b981' if r['판정']=="OK" else '#ef4444'
            fig_m.add_trace(go.Scatter(x=[r['X편차']], y=[r['Y편차']], mode='markers+text', text=[f"<b>{int(r['측정포인트'])}</b>"], textposition="top center", marker=dict(size=12, color=p_c, line=dict(width=1, color='white'))))
        
        st.plotly_chart(fig_m, config={'toImageButtonOptions': {'format': 'png', 'filename': 'Position_Target'}})
        
        # [복구] 엑셀 다운로드 (데이터 및 판정 포함)
        out_res = BytesIO()
        writer = pd.ExcelWriter(out_res, engine='xlsxwriter')
        df_m.to_excel(writer, index=False, sheet_name='위치도결과')
        writer.close()
        st.download_button("📥 분석 결과 엑셀 저장", out_res.getvalue(), "Position_Analysis_Result.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 4] 품질 계산기 (토크 변환기 독립) ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    tabs = st.tabs(["🎯 MMC 보너스", "🔧 일반 단위환산", "⚙️ 토크(Torque) 변환", "⚖️ 합격 판정"])
    
    with tabs[0]:
        base_g = st.number_input("기본 기하공차", value=0.05)
        mmc_s = st.number_input("MMC 규격", value=10.00)
        act_s = st.number_input("현재 실측", value=10.02)
        st.metric("최종 공차", f"{base_g + max(0, act_s - mmc_s):.4f}")
        
    with tabs[1]:
        v = st.number_input("값", value=1.0, key="unit_val")
        m = st.selectbox("종류", ["mm ➔ inch", "inch ➔ mm"])
        st.success(f"결과: {v/25.4:.4f}" if "inch" in m[:4] else f"결과: {v*25.4:.4f}")
        
    with tabs[2]:
        st.subheader("⚙️ 토크 변환기")
        t_v = st.number_input("토크 값 입력", value=1.0)
        t_m = st.selectbox("단위 선택", ["N·m ➔ kgf·m", "kgf·m ➔ N·m", "N·m ➔ kgf·cm", "kgf·cm ➔ N·m"])
        if t_m == "N·m ➔ kgf·m": res = t_v * 0.10197
        elif t_m == "kgf·m ➔ N·m": res = t_v * 9.80665
        elif t_m == "N·m ➔ kgf·cm": res = t_v * 10.197
        else: res = t_v * 0.09806
        st.info(f"변환 결과: {res:.4f}")
        
    with tabs[3]:
        spec = st.number_input("기준")
        u, l = st.number_input("상한"), st.number_input("하한")
        m_v = st.number_input("측정")
        if (spec+l) <= m_v <= (spec+u): st.success("✅ 합격")
        else: st.error("🚨 불합격")
    st.markdown('</div>', unsafe_allow_html=True)
