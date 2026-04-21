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
    st.set_page_config(
    page_title="Position Analysis Tool",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "# 본 프로그램의 소유권은 제작자에게 있습니다."
    }
)
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
    
    col_opt1, col_opt2 = st.columns([1, 2])
    with col_opt1:
        input_method = st.radio("입력 방식 선택", ["텍스트 붙여넣기", "엑셀/CSV 업로드"])
        sample_count = st.number_input("🔢 샘플(캐비티) 수", min_value=1, max_value=20, value=4)
    with col_opt2:
        st.info(f"💡 현재 **{sample_count}개**의 샘플을 추출하도록 설정되었습니다.")

    processed_results = []

    if input_method == "텍스트 붙여넣기":
        raw_data = st.text_area("성적서 데이터를 붙여넣으세요", height=300)
        
        if st.button("🚀 데이터 변환 실행"):
            if raw_data:
                # 1. 텍스트를 줄 단위로 나누고, 빈 칸을 제거한 실제 값만 리스트로 만듦
                all_lines = []
                for line in raw_data.strip().split('\n'):
                    # 탭 또는 공백 2개 이상으로 분리 후 빈 값 제거
                    cols = [c.strip() for c in re.split(r'\t|\s{2,}', line) if c.strip()]
                    all_lines.append(cols)
                
                # 2. 데이터 탐색
                for i in range(len(all_lines)):
                    line = all_lines[i]
                    if not line: continue
                    
                    # [핵심] 줄 안에 'A', 'B', 'C' 같은 한 글자 항목명이 있는지 확인
                    item_name = ""
                    item_index = -1
                    for idx, val in enumerate(line):
                        if len(val) == 1 and val.isalpha(): # 한 글자 알파벳 찾기
                            item_name = val
                            item_index = idx
                            break
                    
                    # 항목명을 찾았고, 아래에 X, Y줄이 더 있다면
                    if item_name and i + 2 < len(all_lines):
                        try:
                            # 현재 줄(위치도), 다음줄(X), 그 다음줄(Y)
                            row_pos = all_lines[i]
                            row_x = all_lines[i+1]
                            row_y = all_lines[i+2]
                            
                            # 데이터 추출 (항목명 바로 다음 칸부터 샘플 데이터라고 가정)
                            # 만약 위치가 밀린다면 row_x[item_index + 1] 방식으로 접근
                            for s in range(sample_count):
                                processed_results.append({
                                    "측정포인트": f"{item_name}_S{s+1}",
                                    "기본공차": 0.35,
                                    "도면치수_X": clean_float(row_x[item_index]), 
                                    "도면치수_Y": clean_float(row_y[item_index]),
                                    "측정치_X": clean_float(row_x[item_index + s + 1]),
                                    "측정치_Y": clean_float(row_y[item_index + s + 1]),
                                    "실측지름_MMC용": clean_float(row_pos[item_index + s + 1])
                                })
                        except: continue

    else:
        up_file = st.file_uploader("CSV 파일을 업로드하세요", type=['csv'])
        if up_file:
            df = pd.read_csv(up_file, header=None).fillna("")
            if st.button("🚀 파일 변환 실행"):
                for i in range(len(df)):
                    for col in range(df.shape[1]):
                        val = str(df.iloc[i, col]).strip()
                        # 한 글자 알파벳 항목명 찾기
                        if len(val) == 1 and val.isalpha():
                            try:
                                item_name = val
                                for s in range(sample_count):
                                    processed_results.append({
                                        "측정포인트": f"{item_name}_S{s+1}",
                                        "기본공차": 0.35, "도면치수_X": 0.0, "도면치수_Y": 0.0,
                                        "측정치_X": clean_float(df.iloc[i+1, col+s+1]),
                                        "측정치_Y": clean_float(df.iloc[i+2, col+s+1]),
                                        "실측지름_MMC용": clean_float(df.iloc[i, col+s+1])
                                    })
                            except: continue

    if processed_results:
        df_res = pd.DataFrame(processed_results)
        df_res.index = df_res.index + 1
        st.success(f"✅ {len(processed_results)}개 변환 성공!")
        st.dataframe(df_res, use_container_width=True)
        st.session_state.data = df_res
        st.balloons()
    elif (input_method == "텍스트 붙여넣기" and 'raw_data' in locals() and raw_data):
        st.warning("데이터를 찾지 못했습니다. 알파벳 항목명(A, B, C...)이 포함되었

    # --- 방식 2: 엑셀/CSV 업로드 (파일 내부 구조에 맞춰 정밀 수정) ---
    else:
        up_file = st.file_uploader("CSV 파일을 업로드하세요", type=['csv'])
        if up_file:
            df_csv = pd.read_csv(up_file, header=None)
            if st.button("🚀 파일 변환 실행"):
                for i in range(len(df_csv)):
                    # 열을 순회하며 A, B, C 같은 항목명 찾기
                    for col in range(df_csv.shape[1]):
                        val = str(df_csv.iloc[i, col]).strip()
                        if len(val) == 1 and val.isalpha():
                            try:
                                item_name = val
                                # 항목명 오른쪽 칸부터 데이터 시작
                                for s in range(sample_count):
                                    processed_results.append({
                                        "측정포인트": f"{item_name}_S{s+1}",
                                        "기본공차": 0.35, "도면치수_X": 0.0, "도면치수_Y": 0.0,
                                        "측정치_X": clean_float(df_csv.iloc[i+1, col+s+1]),
                                        "측정치_Y": clean_float(df_csv.iloc[i+2, col+s+1]),
                                        "실측지름_MMC용": clean_float(df_csv.iloc[i, col+s+1])
                                    })
                                break # 항목 찾았으면 다음 행으로
                            except: continue

    # 공통 출력
    if processed_results:
        df_result = pd.DataFrame(processed_results)
        df_result.index = df_result.index + 1
        st.success(f"✅ {len(processed_results)}개 데이터 변환 성공!")
        st.dataframe(df_result, use_container_width=True)
        st.session_state.data = df_result
        st.balloons()
    else:
        st.warning("데이터를 찾지 못했습니다. 복사 범위를 확인해 주세요.")

    # --- 방식 2: 엑셀/CSV 업로드 (기본 구조는 유지하되 검증 강화) ---
    else:
        up_file = st.file_uploader("CSV 파일을 업로드하세요", type=['csv'])
        if up_file:
            try:
                df_csv = pd.read_csv(up_file, header=None)
                if st.button("🚀 파일 변환 실행"):
                    for i in range(len(df_csv)):
                        # 항목명 찾기 (첫 번째 열이 항목명인 경우)
                        item_name = str(df_csv.iloc[i, 0]).strip()
                        if item_name and not re.match(r'^-?\d', item_name) and item_name != 'nan':
                            if i + 2 < len(df_csv):
                                for s in range(sample_count):
                                    col_idx = s + 1 # 1번 열부터 시료 데이터
                                    processed_results.append({
                                        "측정포인트": f"{item_name}_S{s+1}",
                                        "기본공차": 0.35, "도면치수_X": 0.0, "도면치수_Y": 0.0,
                                        "측정치_X": clean_float(df_csv.iloc[i+1, col_idx]),
                                        "측정치_Y": clean_float(df_csv.iloc[i+2, col_idx]),
                                        "실측지름_MMC용": clean_float(df_csv.iloc[i, col_idx])
                                    })
            except:
                st.error("파일 형식이 올바르지 않습니다.")

    # [공통 출력]
    if processed_results:
        df_result = pd.DataFrame(processed_results)
        df_result.index = df_result.index + 1
        st.success(f"✅ {len(processed_results)}개 데이터 변환 성공!")
        st.dataframe(df_result, use_container_width=True)
        st.session_state.data = df_result
        st.balloons()
    elif (input_method == "텍스트 붙여넣기" and 'raw_data' in locals() and raw_data):
        st.error("항목명(A, B, C...)을 찾을 수 없습니다. 범위를 확인해주세요.")

    # 공통 출력 부분
    if processed_results:
        df_result = pd.DataFrame(processed_results)
        df_result.index = df_result.index + 1
        st.success(f"✅ {len(processed_results)}개 데이터 변환 성공!")
        st.dataframe(df_result, use_container_width=True)
        st.session_state.data = df_result
        st.balloons()
    elif (input_method == "텍스트 붙여넣기" and 'raw_data' in locals() and raw_data) or \
         (input_method == "엑셀/CSV 업로드" and 'up_file' in locals() and up_file):
        st.error("데이터를 분석할 수 없습니다. 항목명(A, B, C...)이 포함되도록 다시 복사해주세요.")

    # 공통 결과 출력 (함수 가장 하단)
    if processed_results:
        df_result = pd.DataFrame(processed_results)
        df_result.index = df_result.index + 1
        st.success(f"✅ {len(processed_results)}개 데이터 변환 완료!")
        st.dataframe(df_result, use_container_width=True)
        st.session_state.data = df_result
        st.balloons()
    elif (input_method == "텍스트 붙여넣기" and raw_data) or (input_method == "엑셀/CSV 업로드" and up_file):
        st.error("데이터를 분석할 수 없습니다. 복사 범위를 다시 확인해주세요.")

    # --- 방식 2: 엑셀/CSV 업로드 (오늘 추가된 덕인 좌표형 로직) ---
    else:
        up_file = st.file_uploader("덕인 좌표형 CSV 파일을 업로드하세요", type=['csv'])
        if up_file:
            df_csv = pd.read_csv(up_file, header=None)
            st.write("📂 파일 로드 완료")
            if st.button("🚀 파일 데이터 변환"):
                # 3행 1세트 로직 가동
                for i in range(0, len(df_csv), 3):
                    try:
                        item_name = str(df_csv.iloc[i, 0]).strip()
                        if item_name == 'nan' or item_name == "": continue
                        
                        for s in range(sample_count):
                            # 첫 번째 열 이후부터 시료 데이터가 있다고 가정 (1번 열부터 sample_count만큼)
                            col_idx = s + 1 
                            processed_results.append({
                                "측정포인트": f"{item_name}_S{s+1}",
                                "기본공차": 0.35,
                                "도면치수_X": 0.0, # 필요시 엑셀 내 도면치수 행을 찾아 연결 가능
                                "도면치수_Y": 0.0,
                                "측정치_X": clean_float(df_csv.iloc[i+1, col_idx]),
                                "측정치_Y": clean_float(df_csv.iloc[i+2, col_idx]),
                                "실측지름_MMC용": clean_float(df_csv.iloc[i, col_idx])
                            })
                    except: continue

    # [공통 결과 출력 부분] - 함수의 가장 아래쪽에 위치하게 합니다.
    if processed_results:
        # 리스트를 표(DataFrame)로 변환
        df_result = pd.DataFrame(processed_results)
        
        # 사용자가 보기 편하게 순번(Index)을 1번부터 표시
        df_result.index = df_result.index + 1 
        
        st.success(f"✅ 변환 완료! (총 {len(processed_results)}개의 데이터가 준비되었습니다.)")
        
        # 1. 화면에 표 출력
        st.dataframe(df_result, use_container_width=True)
        
        # 2. [중요] 세션 스테이트에 데이터 저장 (그래프 분석 탭에서 사용하기 위함)
        st.session_state.data = df_result
        
        # 3. 성공 알림 (풍선 효과)
        st.balloons()
        st.info("🎯 변환된 데이터를 확인하신 후, 상단의 **'📊 Step 2. 위치도 결과 분석'** 탭으로 이동하세요.")
    
    elif 'raw_data' in locals() and raw_data or 'up_file' in locals() and up_file:
        # 데이터는 입력했는데 결과가 비어있는 경우
        st.error("데이터를 분석할 수 없습니다. 양식이나 샘플(캐비티) 수를 다시 확인해주세요.")
        
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

           # 3. 🎨 위치도 산포도 분석 (정상 스케일링 버전)
            st.divider()
            st.subheader("🎯 위치도 산포도 분석 (Basic vs MMC Zone)")
            
            fig, ax = plt.subplots(figsize=(8, 8))
            
            # 편차 계산
            dev_x = df_m['측정치_X'] - df_m['도면치수_X']
            dev_y = df_m['측정치_Y'] - df_m['도면치수_Y']
            
            # 🔵 1. 기본 공차 영역 (Ø0.35)
            basic_radius = 0.35 / 2
            ax.add_patch(plt.Circle((0, 0), basic_radius, color='#3498db', fill=True, alpha=0.15, linestyle='--'))
            ax.add_patch(plt.Circle((0, 0), basic_radius, color='#3498db', fill=False, linestyle='--', linewidth=1.5, label='Basic Tol (Ø0.35)'))

            # 🔴 2. MMC 확장 공차 영역 (최종 공차)
            # [수정] max() 대신 median()이나 평균을 사용하거나, 데이터에 따라 다르게 표현하는 것이 정석이나,
            # 현재 스케일 문제 해결을 위해 median()을 임시 사용
            representative_final_tol = df_m['최종공차'].median() 
            mmc_radius = representative_final_tol / 2
            ax.add_patch(plt.Circle((0, 0), mmc_radius, color='#e74c3c', fill=False, linewidth=2, label=f'Median MMC Tol (Ø{representative_final_tol:.3f})'))
            
            # 🟢 3. 측정 데이터 포인트
            colors = df_m['판정'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
            ax.scatter(dev_x, dev_y, c=colors, s=60, edgecolors='white', zorder=5, label='Measured Points')
            
            # 그래프 꾸미기
            ax.axhline(0, color='black', linewidth=1.2)
            ax.axvline(0, color='black', linewidth=1.2)
            ax.set_xlabel("Deviation X", fontsize=12)
            ax.set_ylabel("Deviation Y", fontsize=12)
            ax.set_title("Position Error: Basic vs MMC Extension", fontsize=14, fontweight='bold', pad=20)
            
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.set_aspect('equal')
            
            # 범례 추가
            ax.legend(loc='upper right', frameon=True, shadow=True)
            
            # --- [핵심 수정] 축 범위 자동 설정 (스케일링 해결) ---
            # 공차 영역(Max, Basic)과 데이터 포인트 전체 영역 중 더 큰 값을 기준으로 설정
            
            # 1. 공차 영역 반경 (Max, Basic 중 큰 값)
            tol_radius = max(basic_radius, mmc_radius)
            
            # 2. 데이터 포인트 전체 영역 반경
            data_radius = pd.concat([dev_x, dev_y]).abs().max()
            
            # 3. 축 범위 설정 (두 영역 중 큰 값의 1.2배 여유)
            limit = max(tol_radius, data_radius) * 1.2
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
            
            # 1. 그래프 출력
            st.pyplot(fig)

            # 2. 💡 데이터 분석 가이드 (AI Summary)
            st.divider()
            st.subheader("💡 데이터 분석 가이드 (AI Summary)")
            
            # 통계 데이터 계산
            total_count = len(df_m)
            ok_count = (df_m['판정'].str.contains('OK')).sum()
            ng_count = total_count - ok_count
            ok_rate = (ok_count / total_count) * 100

            # X, Y 편차 평균 (밀림 방향 파악)
            avg_dev_x = dev_x.mean()
            avg_dev_y = dev_y.mean()

            # 요약 리포트 지표 출력
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("전체 샘플 수", f"{total_count}개")
            col_m2.metric("합격률", f"{ok_rate:.1f}%", delta=f"-{ng_count} NG" if ng_count > 0 else "All Pass", delta_color="inverse")
            col_m3.metric("평균 편차(X, Y)", f"{avg_dev_x:.3f}, {avg_dev_y:.3f}")
            
            # 밀림 방향 진단 텍스트
            dir_x = "오른쪽(+)" if avg_dev_x > 0 else "왼쪽(-)"
            dir_y = "위쪽(+)" if avg_dev_y > 0 else "아래쪽(-)"
            
            advice = f"""
            * **종합 판정:** 현재 전체 합격률은 **{ok_rate:.1f}%**입니다.
            * **경향성 분석:** 데이터가 전체적으로 **{dir_x}**으로 `{abs(avg_dev_x):.3f}mm`, **{dir_y}**으로 `{abs(avg_dev_y):.3f}mm` 밀려 있습니다.
            * **조치 권고:** 1. 그래프 상의 점들이 한쪽 방향으로 줄지어 있다면 **장비 원점(Offset) 보정**을 검토하세요.
                2. 특정 샘플만 튀는 경우 **지그(Jig) 고정력이나 이물질** 확인이 필요합니다.
            """
            st.info(advice)

            # 3. 💾 분석 결과 내보내기 (엑셀 & 이미지)
            st.divider()
            st.subheader("💾 분석 결과 저장")
            
            col_dl1, col_dl2 = st.columns(2)

            # (1) 엑셀 다운로드
            with col_dl1:
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_m.to_excel(writer, index=False, sheet_name='Position_Analysis')
                
                st.download_button(
                    label="📂 Excel 결과 다운로드",
                    data=excel_buffer.getvalue(),
                    file_name="Position_Analysis_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            # (2) 그래프 이미지 저장
            with col_dl2:
                img_buffer = BytesIO()
                fig.savefig(img_buffer, format="png", bbox_inches='tight', dpi=300)
                
                st.download_button(
                    label="🖼️ 그래프 이미지 저장",
                    data=img_buffer.getvalue(),
                    file_name="Position_Scatter_Plot.png",
                    mime="image/png",
                    use_container_width=True
                )

            # 최종 성공 메시지
            st.success(f"✅ 분석 완료: {total_count}개 중 {ok_count}개 합격 (불합격 {ng_count}개)")

        except Exception as e:
            st.error(f"⚠️ 분석 중 오류 발생: {e}")
            
def run_quality_calculator():
    """메뉴 4: 품질 계산기 - 함수 내부로 모든 탭을 집어넣었습니다."""
    st.title("🧮 품질 종합 계산기")
    
    # 박스 스타일 시작
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    
    # 1. 탭 정의 (함수 안으로 들어옴)
    tabs = st.tabs(["공차 계산", "단위 변환", "토크 변환", "합불 판정"])

    # --- 탭 0: 기하공차 계산 ---
    with tabs[0]:
        st.subheader("📏 기하공차 MMC 계산")
        base_g = st.number_input("기본 기하공차", value=0.05, key="calc_base_g")
        mmc_s = st.number_input("MMC 규격", value=10.00, key="calc_mmc_s")
        act_s = st.number_input("현재 실측", value=10.02, key="calc_act_s")
        st.metric("최종 허용 공차", f"{base_g + max(0, act_s - mmc_s):.4f}")

    # --- 탭 1: 길이 단위 변환 ---
    with tabs[1]:
        st.subheader("🔄 mm / inch 변환")
        v = st.number_input("값 입력", value=1.0, key="calc_length_v")
        m = st.selectbox("변환 종류", ["mm ➔ inch", "inch ➔ mm"], key="calc_length_m")
        if "inch" in m:
            st.success(f"결과: {v/25.4:.4f} inch")
        else:
            st.success(f"결과: {v*25.4:.4f} mm")

    # --- 탭 2: 토크 변환 ---
    with tabs[2]:
        st.subheader("🔧 토크 단위 변환")
        t_v = st.number_input("토크 값 입력", value=1.0, key="calc_torque_v")
        t_m = st.selectbox("단위 선택", ["N·m ➔ kgf·cm", "kgf·cm ➔ N·m"], key="calc_torque_m")

        if t_m == "N·m ➔ kgf·cm":
            st.success(f"결과: {t_v * 10.197:.2f} kgf·cm")
        elif t_m == "kgf·cm ➔ N·m":
            st.success(f"결과: {t_v / 10.197:.2f} N·m")

    # --- 탭 3: 합불 판정 ---
    with tabs[3]:
        st.subheader("✅ 합격/불합격 판정")
        spec = st.number_input("기준값(Spec)", value=0.0, key="calc_spec_v")
        u = st.number_input("상한 공차(+)", value=0.1, key="calc_upper_v")
        l = st.number_input("하한 공차(-)", value=-0.1, key="calc_lower_v")
        m_v = st.number_input("실제 측정값", value=0.0, key="calc_measure_v")
        
        if (spec + l) <= m_v <= (spec + u):
            st.success(f"결과: {m_v} 👉 ✅ 합격")
        else:
            st.error(f"결과: {m_v} 👉 🚨 불합격")

    # 박스 스타일 및 레이아웃 닫기
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
