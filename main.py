import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import re  # <--- [추가] 텍스트에서 숫자/글자 패턴 찾을 때 필수!
from io import BytesIO

# ==========================================
# 1. 전역 설정 및 스타일 (공통)
# ==========================================
def set_global_style():
    st.set_page_config(page_title="품질 통합 분석 시스템 v9.5", layout="wide")
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        [data-testid="stSidebar"] { background-color: #0f172a !important; }
        [data-testid="stSidebar"] * { color: #f8fafc !important; }
        .stButton > button {
            background-color: #ef4444 !important; color: white !important;
            font-weight: bold !important; width: 100%; border-radius: 8px;
        }
        .capture-info {
            background-color: #e0f2fe; padding: 10px; border-radius: 5px; 
            border: 1px solid #7dd3fc; color: #0369a1; font-size: 0.9em;
            margin-bottom: 20px; text-align: center;
        }
        .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); margin-bottom: 25px; }
        .report-card { background-color: #f1f5f9; padding: 20px; border-left: 10px solid #3b82f6; border-radius: 8px; line-height: 2.0; font-size: 1.1em; }
        .guide-box { padding: 15px; background-color: #f8fafc; border-radius: 10px; border: 1px dashed #cbd5e1; margin-bottom: 15px; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 메뉴별 독립 기능 (함수화)
# ==========================================

import streamlit as st
import pandas as pd
import re

def clean_float(value):
    """문자열에서 숫자만 추출하여 실수로 변환"""
    try:
        cleaned = re.sub(r'[^0-9\.\-]', '', str(value))
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0

def run_data_converter():
    st.header("🔄 성적서 데이터 자동 변환기")
    
    # 1. 캐비티 수 선택 (유저가 직접 지정하여 오류 방지)
    col1, col2 = st.columns([1, 2])
    with col1:
        sample_count = st.number_input("🔢 샘플(캐비티) 수", min_value=1, max_value=20, value=4)
    with col2:
        st.info(f"💡 현재 **{sample_count}개**의 샘플을 추출하도록 설정되었습니다.")

    # 2. 데이터 입력창
    raw_data = st.text_area(
        "성적서 데이터를 붙여넣으세요", 
        height=300, 
        placeholder="Nominal 열부터 끝까지 복사해서 붙여넣으세요."
    )

    if st.button("🚀 분석 데이터로 변환"):
        if raw_data:
            try:
                lines = [line.split('\t') for line in raw_data.strip().split('\n')]
                if len(lines[0]) <= 1:
                    lines = [re.split(r'\s{2,}', line.strip()) for line in raw_data.strip().split('\n')]

                processed_results = []
                
                for i in range(0, len(lines), 4):
                    if i + 3 >= len(lines): break 
                    
                    try:
                        pin_line = lines[i]
                        x_line = lines[i+2]
                        y_line = lines[i+3]
                        
                        # 도면치수(Nominal)는 항상 줄의 맨 앞 숫자
                        # 공차 숫자가 섞이지 않도록 리스트의 첫 번째 숫자만 추출
                        all_nums_x = [clean_float(v) for v in x_line if re.search(r'\d', str(v))]
                        nom_x = all_nums_x[0] if all_nums_x else 0.0
                        
                        all_nums_y = [clean_float(v) for v in y_line if re.search(r'\d', str(v))]
                        nom_y = all_nums_y[0] if all_nums_y else 0.0

                        # [핵심] 사용자가 설정한 개수만큼만 '뒤에서부터' 가져오기
                        # 이렇게 하면 앞쪽에 공차(-100, 100 등)가 있어도 무시하고 진짜 데이터만 가져옵니다.
                        for s in range(sample_count):
                            idx = -(sample_count - s) 
                            
                            act_x = clean_float(x_line[idx])
                            act_y = clean_float(y_line[idx])
                            # MMC 지름 라인(i+1)도 동일하게 뒤에서 추출
                            act_dia = clean_float(lines[i+1][idx]) if len(lines[i+1]) >= abs(idx) else 0.35
                            
                            pin_name = next((str(x) for x in pin_line if "PIN" in str(x)), f"POINT_{i//4 + 1}")

                            processed_results.append({
                                "측정포인트": f"{pin_name}_S{s+1}",
                                "기본공차": 0.35,
                                "도면치수_X": nom_x,
                                "도면치수_Y": nom_y,
                                "측정치_X": act_x,
                                "측정치_Y": act_y,
                                "실측지름_MMC용": act_dia
                            })
                    except Exception:
                        continue

                # 3. 결과 출력
                if processed_results:
                    df_result = pd.DataFrame(processed_results)
                    df_result.index = df_result.index + 1 # 1번부터 표시
                    
                    st.success(f"✅ 변환 완료! (포인트당 {sample_count}개씩 총 {len(processed_results)}개)")
                    st.dataframe(df_result, use_container_width=True)
                    
                    st.session_state.data = df_result
                    st.balloons()
                    st.info("🎯 상단의 **'📊 Step 2. 위치도 결과 분석'** 탭으로 이동하세요.")
                else:
                    st.error("데이터를 분석할 수 없습니다.")

            except Exception as e:
                st.error(f"오류 발생: {e}")
                        
               # 3. 결과 출력
                if processed_results:
                    df_result = pd.DataFrame(processed_results)
                    
                    # 사용자가 보기 편하게 인덱스를 0이 아닌 1부터 시작하도록 수정
                    df_result.index = df_result.index + 1
                    
                    st.success(f"✅ 총 {len(processed_results)}개의 샘플 데이터를 변환했습니다! (캐비티 수: {sample_count}개)")
                    
                    # 표 출력 (인덱스가 1, 2, 3... 순으로 보입니다)
                    st.dataframe(df_result, use_container_width=True)
                    
                    # 분석 세션에 데이터 저장 (인덱스 보정된 상태 그대로 저장됨)
                    st.session_state.data = df_result
                    
                    st.balloons()
                    st.info("🎯 변환 완료! 이제 상단의 **'📊 Step 2. 위치도 결과 분석'** 탭을 클릭하세요.")
                else:
                    st.error("데이터를 분석할 수 없습니다. 성적서 형식을 다시 확인해주세요.")

            except Exception as e:
                st.error(f"⚠️ 변환 중 오류가 발생했습니다: {e}")
        else:
            st.warning("내용을 입력해주세요. (Nominal 열부터 끝까지 복사)")

def run_xyz_transformer():
    """메뉴 1: XYZ 좌표 데이터 변환기 """
    st.header("📐 XYZ 좌표 데이터 변환기")
    st.info("💡 X, Y, Z 좌표 데이터를 입력하고 오프셋(Offset) 연산 등을 수행합니다.")

    # 1. 오프셋 설정 입력
    col1, col2, col3 = st.columns(3)
    with col1:
        off_x = st.number_input("X 오프셋", value=0.0, format="%.3f")
    with col2:
        off_y = st.number_input("Y 오프셋", value=0.0, format="%.3f")
    with col3:
        off_z = st.number_input("Z 오프셋", value=0.0, format="%.3f")

    # 2. 데이터 입력창
    raw_xyz = st.text_area("XYZ 데이터를 붙여넣으세요 (형식: 이름 X Y Z)", height=250, 
                          placeholder="P1  10.521  20.332  5.001\nP2  11.244  20.115  5.102")

    if st.button("🔄 좌표 연산 및 데이터 저장"):
        if raw_xyz:
            try:
                # 공백으로 데이터 분리
                lines = [re.split(r'\s+', line.strip()) for line in raw_xyz.strip().split('\n')]
                
                processed_xyz = []
                for l in lines:
                    if len(l) >= 4:  # 이름, X, Y, Z 최소 4개 항목 필요
                        name = l[0]
                        orig_x = clean_float(l[1])
                        orig_y = clean_float(l[2])
                        orig_z = clean_float(l[3])
                        
                        processed_xyz.append({
                            "측정포인트": name,
                            "기본공차": 0.35,
                            "도면치수_X": 0.0, # 필요시 수정
                            "도면치수_Y": 0.0,
                            "측정치_X": orig_x + off_x,
                            "측정치_Y": orig_y + off_y,
                            "측정치_Z": orig_z + off_z, # Z값 저장
                            "실측지름_MMC용": 0.35
                        })
                
                if processed_xyz:
                    df_xyz = pd.DataFrame(processed_xyz)
                    st.success(f"✅ {len(processed_xyz)}개의 좌표를 변환했습니다.")
                    st.dataframe(df_xyz)
                    
                    # 세션에 저장 (위치도 분석에서 사용 가능하도록)
                    st.session_state.data = df_xyz
                    st.balloons()
                else:
                    st.error("데이터 형식을 확인해주세요. (이름 X Y Z)")
            except Exception as e:
                st.error(f"오류 발생: {e}")

def run_cavity_analysis():
    """메뉴 2: 멀티 캐비티 분석"""
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    def get_cav_template():
        df_t = pd.DataFrame({"Point": range(1,6), "SPEC_MIN": [30.1]*5, "SPEC_MAX": [30.5]*5, "Cavity_1": [30.2]*5, "Cavity_2": [30.3]*5, "Cavity_3": [30.2]*5, "Cavity_4": [30.4]*5})
        out = BytesIO(); writer = pd.ExcelWriter(out, engine='xlsxwriter'); df_t.to_excel(writer, index=False); writer.close()
        return out.getvalue()
    
    st.download_button("📄 분석용 템플릿 다운로드", get_cav_template(), "Multi_Cavity_Template.xlsx")
    up = st.file_uploader("파일 업로드", type=["xlsx", "csv"])
    
    if up:
        df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_min, y_max = np.nanmin(all_vals) - 0.03, np.nanmax(all_vals) + 0.03
        
        c_grid = st.columns(2)
        summary_items = []
        for i, cav in enumerate(cav_cols):
            color = cav_colors[i % len(cav_colors)]
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            summary_items.append(f"✅ **{cav}**: 합격률 **{((len(df)-len(df[df[f'{cav}_판정']=='NG']))/len(df))*100:.1f}%**")
            with c_grid[i % 2]:
                st.markdown(f'<div class="stBox"><b style="color:{color}; font-size:1.1em;">{cav}</b>', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=color, name="실측"))
                fig.update_layout(height=280, yaxis_range=[y_min, y_max], margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 트렌드 분석")
        df['Avg'] = df[cav_cols].mean(axis=1)
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="MIN", line=dict(color="blue", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="MAX", line=dict(color="red", dash="dot")))
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], mode='markers', name=cav, marker=dict(color=cav_colors[i%len(cav_colors)], size=10)))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Avg'], name="전체평균", line=dict(color="black", width=3)))
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('<div class="capture-info">📸 그래프 우측 상단 <b>카메라 아이콘</b>을 누르면 이미지가 즉시 저장됩니다.</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-card">{"<br>".join(summary_items)}</div>', unsafe_allow_html=True)
        out_cav = BytesIO(); writer = pd.ExcelWriter(out_cav, engine='xlsxwriter'); df.to_excel(writer, index=False); writer.close()
        st.download_button("📥 분석 결과 엑셀 저장", out_cav.getvalue(), "Cavity_Result.xlsx")
        st.markdown('</div>', unsafe_allow_html=True)

import matplotlib.pyplot as plt

def run_position_analysis():
    st.header("📊 Step 2. 위치도 결과 분석")

    if 'data' not in st.session_state or st.session_state.data is None:
        st.warning("⚠️ Step 1에서 데이터를 먼저 준비해주세요.")
        return

    df_m = st.session_state.data.copy()

    # 데이터 수치화 (강제 변환)
    numeric_cols = ['기본공차', '도면치수_X', '도면치수_Y', '측정치_X', '측정치_Y', '실측지름_MMC용']
    for col in numeric_cols:
        if col in df_m.columns:
            df_m[col] = pd.to_numeric(df_m[col], errors='coerce').fillna(0.0)

    st.subheader("⚙️ 분석 설정")
    mmc_val = st.number_input("📏 MMC 기준값 (최대 실체 조건 지름)", value=0.35, step=0.001, format="%.3f")

    if st.button("🔍 위치도 분석 및 시각화 실행"):
        try:
            # 1. 계산 로직
            df_m['위치도결과'] = (((df_m['측정치_X'] - df_m['도면치수_X'])**2 + (df_m['측정치_Y'] - df_m['도면치수_Y'])**2)**0.5 * 2).round(4)
            df_m['보너스공차'] = (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0).round(4)
            df_m['최종공차'] = (df_m['기본공차'] + df_m['보너스공차']).round(4)
            df_m['판정'] = df_m.apply(lambda x: "✅ OK" if x['위치도결과'] <= x['최종공차'] else "❌ NG", axis=1)

            # 2. 결과 보고서 출력
            st.divider()
            st.subheader("📝 분석 결과 보고서")
            
            display_cols = ['측정포인트', '도면치수_X', '도면치수_Y', '측정치_X', '측정치_Y', '위치도결과', '최종공차', '판정']
            final_display = df_m[[c for c in display_cols if c in df_m.columns]]
            
            def highlight_pass_fail(val):
                color = '#DFF2BF' if 'OK' in str(val) else '#FFBABA'
                return f'background-color: {color}'

            try:
                st.dataframe(final_display.style.map(highlight_pass_fail, subset=['판정']), use_container_width=True)
            except AttributeError:
                st.dataframe(final_display.style.applymap(highlight_pass_fail, subset=['판정']), use_container_width=True)

           # 3. 🎨 위치도 산포도 분석 (영역 구분 버전)
            st.divider()
            st.subheader("🎯 위치도 산포도 분석 (Basic vs MMC Zone)")
            
            fig, ax = plt.subplots(figsize=(8, 8))
            
            # 데이터 편차 계산
            dev_x = df_m['측정치_X'] - df_m['도면치수_X']
            dev_y = df_m['측정치_Y'] - df_m['도면치수_Y']
            
            # 🔵 1. 기본 공차 영역 (Ø0.35)
            basic_radius = 0.35 / 2
            circle_basic = plt.Circle((0, 0), basic_radius, color='#3498db', fill=True, 
                                      alpha=0.15, linestyle='--', label='Basic Tolerance (Ø0.35)')
            ax.add_patch(circle_basic)
            # 기본 공차 테두리
            ax.add_patch(plt.Circle((0, 0), basic_radius, color='#3498db', fill=False, linestyle='--', linewidth=1.5))

            # 🔴 2. MMC 확장 공차 영역 (최종 공차)
            # 샘플 중 가장 큰 공차를 시각적 기준으로 표시
            max_final_tol = df_m['최종공차'].max()
            max_radius = max_final_tol / 2
            circle_mmc = plt.Circle((0, 0), max_radius, color='#e74c3c', fill=False, 
                                    linewidth=2, label=f'Max MMC Allowed (Ø{max_final_tol:.3f})')
            ax.add_patch(circle_mmc)
            
            # 🟢 3. 측정 데이터 포인트
            # 판정에 따라 점 색상 변경
            colors = df_m['판정'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
            ax.scatter(dev_x, dev_y, c=colors, s=70, edgecolors='white', zorder=5, label='Measured Points')
            
            # 그래프 레이아웃 설정
            ax.axhline(0, color='black', linewidth=1.2) # X축 중심선
            ax.axvline(0, color='black', linewidth=1.2) # Y축 중심선
            ax.set_xlabel("Deviation X", fontsize=12)
            ax.set_ylabel("Deviation Y", fontsize=12)
            ax.set_title("Position Error: Basic vs MMC Extension", fontsize=14, fontweight='bold', pad=20)
            
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.set_aspect('equal') # 1:1 비율 유지 (원형 보존)
            
            # 범례 표시
            ax.legend(loc='upper right', frameon=True, shadow=True)
            
            # 축 범위 자동 설정 (공차 영역보다 20% 여유 있게)
            limit = max_radius * 1.2
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
            
            st.pyplot(fig)
            # 통계 출력
            ok_count = (df_m['판정'] == "✅ OK").sum()
            st.success(f"✅ 분석 완료: 전체 {len(df_m)}개 중 {ok_count}개 합격")

        except Exception as e:
            st.error(f"⚠️ 그래프 생성 중 오류 발생: {e}")
            
def run_quality_calculator():
    """메뉴 4: 품질 계산기"""
    st.title("🧮 품질 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    tabs = st.tabs(["🎯 MMC 보너스", "🔧 일반 단위환산", "⚙️ 토크 변환", "⚖️ 합격 판정"])
    
    with tabs[0]:
        base_g = st.number_input("기본 기하공차", value=0.05)
        mmc_s = st.number_input("MMC 규격", value=10.00)
        act_s = st.number_input("현재 실측", value=10.02)
        st.metric("최종 공차", f"{base_g + max(0, act_s - mmc_s):.4f}")
    with tabs[1]:
        v = st.number_input("값", value=1.0)
        m = st.selectbox("종류", ["mm ➔ inch", "inch ➔ mm"])
        st.success(f"결과: {v/25.4:.4f}" if "inch" in m[:4] else f"결과: {v*25.4:.4f}")
    with tabs[2]:
        t_v = st.number_input("토크 값 입력", value=1.0)
        t_m = st.selectbox("단위", ["N·m ➔ kgf·m", "kgf·m ➔ N·m", "N·m ➔ kgf·cm", "kgf·cm ➔ N·m"])
        res = t_v * 0.10197 if "kgf·m" in t_m else (t_v * 9.80665 if "N·m" in t_m and "kgf·m" in t_m[:5] else (t_v * 10.197 if "kgf·cm" in t_m else t_v * 0.09806))
        st.info(f"변환 결과: {res:.4f}")
    with tabs[3]:
        spec = st.number_input("기준")
        u, l = st.number_input("상한"), st.number_input("하한")
        m_v = st.number_input("측정")
        if (spec+l) <= m_v <= (spec+u): st.success("✅ 합격")
        else: st.error("🚨 불합격")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 3. 메인 프로그램 제어 (Main Loop)
# ==========================================
def main():
    # 1. 세션 상태 초기화 (데이터 및 리셋 키)
    if 'reset_key' not in st.session_state:
        st.session_state.reset_key = 0
    if 'data' not in st.session_state:
        st.session_state.data = None

    # 전역 스타일 적용
    set_global_style()
    
    # 2. 사이드바 메뉴 (불필요한 설명을 제거하여 깔끔하게 구성)
    st.sidebar.title("💎 QUALITY HUB v9.5")
    
    menu = st.sidebar.radio(
        "📂 분석 카테고리", 
        [
            "🎯 위치도 정밀 분석",    # 하위 메뉴(탭) 포함
            "📈 멀티 캐비티 분석",
            "📐 XYZ 좌표 변환기",
            "🧮 품질 통합 계산기"
        ], 
        key=f"m_{st.session_state.reset_key}"
    )
    
    st.sidebar.markdown("---")
    
    # 데이터 초기화 버튼
    if st.sidebar.button("🗑️ 모든 데이터 리셋"):
        st.session_state.reset_key += 1
        st.session_state.data = None
        st.rerun()

    # 3. 선택된 메뉴에 따른 본문 출력
    if menu == "🎯 위치도 정밀 분석":
        st.title("🎯 위치도 정밀 분석 시스템")
        st.caption("📍 성적서 데이터를 변환한 후, MMC 기반의 위치도 합불 판정을 수행합니다.")
        
        # --- 하위 폴더(탭) 구조 구현 ---
        tab_convert, tab_analysis = st.tabs([
            "📁 Step 1. 성적서 데이터 변환", 
            "📊 Step 2. 위치도 결과 분석"
        ])
        
        with tab_convert:
            # 1번 메뉴였던 성적서 변환기를 이곳으로 배치
            run_data_converter()
            
        with tab_analysis:
            # 변환된 데이터가 있을 때만 분석 화면 표시
            if st.session_state.data is not None:
                run_position_analysis()
            else:
                st.info("💡 'Step 1' 탭에서 데이터를 먼저 변환하거나 저장해 주세요.")
                # 예시를 위해 템플릿 다운로드 버튼이라도 보여주고 싶다면 아래 함수 실행
                # run_position_analysis() # 데이터 없을 때 내부 처리가 되어있다면 바로 호출 가능

    elif menu == "📈 멀티 캐비티 분석":
        st.caption("📍 핀 높이 등 여러 캐비티의 통합 데이터 트렌드를 분석합니다.")
        run_cavity_analysis()
        
    elif menu == "📐 XYZ 좌표 변환기":
        st.caption("📍 수동 좌표 입력 및 Z축 오프셋(Offset) 연산을 지원합니다.")
        run_xyz_transformer()
        
    elif menu == "🧮 품질 통합 계산기":
        st.caption("📍 단위 환산, 토크 변환 등 공정 필수 계산 도구 모음입니다.")
        run_quality_calculator()

# 프로그램 실행
if __name__ == "__main__":
    main()
