import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import google.generativeai as genai
import json
import random
import hashlib
import os

# --- 1. CONFIGURACIÓN E INITIAL STATE ---
st.set_page_config(page_title="TechPrice Auditor", layout="wide", initial_sidebar_state="collapsed")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'watchlist' not in st.session_state:
    st.session_state['watchlist'] = []

# --- INYECCIÓN DE CSS PREMIUM (ULTRA MINIMALISTA) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 95%; }
    p, h1, h2, h3, h4, h5, h6, span, div, label { color: #e2e8f0; font-family: 'Inter', sans-serif; }
    
    .title-gradient { font-size: 3.2rem; font-weight: 900; background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0px; padding-bottom: 0px; line-height: 1.2; }
    .subtitle-header { color: #9ca3af; font-size: 1.1rem; font-weight: 500; margin-top: -5px; margin-bottom: 20px;}
    
    .product-card { background: linear-gradient(145deg, #111827, #1f2937); padding: 25px; border-radius: 16px; border: 1px solid #374151; margin-bottom: 25px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); }
    .alert-danger-box { background: linear-gradient(90deg, rgba(153, 27, 27, 0.2) 0%, rgba(0,0,0,0) 100%); border-left: 4px solid #ef4444; color: #fca5a5; padding: 15px; border-radius: 6px; font-weight: 600; margin-bottom: 15px; }
    .alert-success-box { background: linear-gradient(90deg, rgba(6, 78, 59, 0.2) 0%, rgba(0,0,0,0) 100%); border-left: 4px solid #10b981; color: #6ee7b7; padding: 15px; border-radius: 6px; font-weight: 600; margin-bottom: 15px; }
    .store-card { background-color: #1f2937; border: 1px solid #374151; padding: 18px; border-radius: 12px; margin-bottom: 12px; transition: all 0.3s ease; }
    .store-card:hover { transform: translateY(-3px); border-color: #3b82f6; box-shadow: 0 8px 20px rgba(59, 130, 246, 0.15); }
    .image-placeholder { background: radial-gradient(circle, #1f2937 0%, #111827 100%); border: 2px dashed #4b5563; height: 250px; border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #9ca3af; text-align: center; }
    
    .wa-btn { background-color: transparent; color: #10b981 !important; border: 1px solid #10b981; padding: 8px 15px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 13px; text-decoration: none; display: block; margin-top: 5px; transition: all 0.2s; }
    .wa-btn:hover { background-color: rgba(16, 185, 129, 0.1); transform: translateY(-2px); }
    
    .paypal-btn { background-color: transparent; color: #ffc439 !important; border: 1px solid #ffc439; padding: 8px 15px; border-radius: 8px; text-align: center; font
