import os
import streamlit as st

api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if api_key:
    st.success("Gemini API 키가 정상적으로 설정되었습니다.")
else:
    st.warning("GEMINI_API_KEY가 설정되지 않았습니다.")
