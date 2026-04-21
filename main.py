import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 초기 설정
st.set_page_config(page_title="Quality Hub Pro v2.7", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #d32f2f; color: white; }
        .ng-box { height: 180px; overflow-y: auto; border: 2px solid #ff0000; padding: 15px; border-radius: 8px; background-color: #fff5f5; }
        .ok-box { padding: 10px; border-radius: 8px; background-color: #e8f5e9; color: #2e7d32; font-weight: bold; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

def run_analysis():
    set_style()
    st.title("🎯 품질 측정 위치도 분석 리포트")

    with st.sidebar:
        st.header("📋 설정")
        mode = st.radio("성적서 유형", ["유형 B (가로형)", "유형 A (3줄 세트)"])
        sc = st.number_input("시료 수(Sample)", min_value=1, value=4)
        tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("MMC 기준값", value=0.060 if mode == "유형 A (3줄 세트)" else 0.350, format="%.3f")

    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=250)
    
    if st.button("📊 분석 보고서 생성") and raw_input:
        try:
            results = []
            
            if mode == "유형 B (가로형)":
                lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i + 3 >= len(lines): break
                    
                    def clean_v(lst, idx):
                        v = re.sub(r'[^0-9\.\-]', '', lst[idx])
                        return float(v) if v and v != '-' else 0.0

                    try:
                        nx, ny = clean_v(lines[i+2], 0), clean_v(lines[i+3], 0)
                        lbl = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                        for s in range(sc):
                            idx = -(sc - s)
                            ax, ay = clean_v(lines[i+2], idx), clean_v(lines[i+3], idx)
                            dv = clean_v(lines[i+1], idx) if len(lines[i+1]) > abs(idx) else 0.35
                            results.append({"ID": f"{lbl}_S{s+1}", "NX": nx, "NY": ny, "AX": ax, "AY": ay, "DIA": dv})
                    except Exception: continue

            else:
                lines = [l.strip() for l in raw_input.split('\n') if l.strip()]
                rows = []
                for l in lines:
                    nums = [float(v) for v in re.findall(r'[-+]?\d*\.\d+|\d+', l)]
                    rows.append([v if abs(v) < 150 else v % 100 for v in nums])
                rows = [r for r in rows if r]
                for i in range(0, len(rows) // 3 * 3, 3):
                    for s in range(1, len(rows[i+1])):
                        results.append({"ID": f"P{(i//3)+1}_S{s}", "NX": rows[i+1][0], "NY": rows[i+
