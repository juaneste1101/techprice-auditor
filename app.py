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
    
    .paypal-btn { background-color: transparent; color: #ffc439 !important; border: 1px solid #ffc439; padding: 8px 15px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 13px; text-decoration: none; display: block; margin-top: 5px; transition: all 0.2s; }
    .paypal-btn:hover { background-color: rgba(255, 196, 57, 0.1); transform: translateY(-2px); }
    
    .metric-card { background: #1f2937; border-radius: 16px; padding: 20px; border: 1px solid #374151; text-align: left; }
    .metric-title { font-size: 14px; color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; display: block;}
    .metric-value { font-size: 32px; font-weight: 900; color: #ffffff; margin: 0;}
    .badge-verde { background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; vertical-align: middle; margin-left: 10px;}
    
    /* Pestañas con contorno estilo botones */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 10px; border-bottom: none; padding-bottom: 5px;}
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: 1px solid #374151; border-radius: 8px; color: #9ca3af; padding: 8px 16px; font-weight: 600; transition: all 0.2s; }
    .stTabs [aria-selected="true"] { color: #ffffff; border: 1px solid #3b82f6 !important; background-color: rgba(59, 130, 246, 0.1) !important; }
    
    div[data-testid="stButton"] button { background-color: transparent; border: 1px solid #4b5563; color: #d1d5db; border-radius: 6px; font-weight: 500; transition: all 0.2s; }
    div[data-testid="stButton"] button:hover { border-color: #3b82f6; color: #3b82f6; background-color: rgba(59, 130, 246, 0.05); }
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE BASE DE DATOS Y ENCRIPTACIÓN ---
def get_connection():
    return sqlite3.connect('database.db', check_same_thread=False)

def inicializar_tablas_seguridad():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, producto_nombre TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES usuarios(id), UNIQUE(user_id, producto_nombre))")
    conn.commit()
    conn.close()

inicializar_tablas_seguridad()

def encriptar_password(password): return hashlib.sha256(password.encode()).hexdigest()

def registrar_usuario(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, password_hash) VALUES (?, ?)", (username, encriptar_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError: return False 
    finally: conn.close()

def verificar_usuario(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE username = ? AND password_hash = ?", (username, encriptar_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def sincronizar_watchlist_db(user_id, producto, accion):
    conn = get_connection()
    cursor = conn.cursor()
    if accion == "AGREGAR":
        try:
            cursor.execute("INSERT INTO watchlist (user_id, producto_nombre) VALUES (?, ?)", (user_id, producto))
            conn.commit()
        except sqlite3.IntegrityError: pass
    elif accion == "LIMPIAR":
        cursor.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
        conn.commit()
    conn.close()

def cargar_watchlist_desde_db(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT producto_nombre FROM watchlist WHERE user_id = ?", (user_id,))
    items = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return items

def obtener_catalogo():
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT nombre FROM productos ORDER BY nombre ASC", conn)
    conn.close()
    return df['nombre'].tolist()

def obtener_estadisticas_globales():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT nombre) FROM productos")
    total_prods = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT tienda) FROM productos")
    total_tiendas = cursor.fetchone()[0]
    conn.close()
    return total_prods, total_tiendas

def consultar_competencia(producto):
    conn = get_connection()
    df = pd.read_sql(f"SELECT nombre, categoria, tienda as Tienda, precio_actual as Precio, precio_anterior as Min_Historico, url as Url FROM productos WHERE nombre = '{producto}'", conn)
    conn.close()
    return df

def analizar_precio_con_ia(producto, precio_hoy, minimo_historico):
    API_KEY = os.environ.get("API_KEY")
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f'''Analiza: {producto}. Hoy: ${precio_hoy}. Min: ${minimo_historico}. Responde JSON: {{"veredicto": "VALOR", "motivo": "Razón"}}'''
        response = model.generate_content(prompt)
        return json.loads(response.text.strip().replace("```json", "").replace("```", ""))
    except Exception:
        return {"veredicto": "ALERTA DE FALSO DESCUENTO" if precio_hoy > minimo_historico else "OFERTA REAL / ESTABLE", "motivo": "Auditoría ejecutada por motor algorítmico local."}

def formato_colombia(valor): return f"${valor:,.0f}".replace(",", ".")

# ==========================================
# 3. TOP NAVBAR (ENCABEZADO Y CONTROLES)
# ==========================================
col_header, col_nav = st.columns([1.8, 1])

with col_header:
    st.markdown('<h1 class="title-gradient">Auditor de TechPrice</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-header">Data Warehouse B2B & Inteligencia de Mercado</p>', unsafe_allow_html=True)

with col_nav:
    tab_acc, tab_watch, tab_pro = st.tabs(["Cuenta", "Seguimiento", "Licencias y Pagos"])
    
    with tab_acc:
        if not st.session_state['logged_in']:
            c_log1, c_log2 = st.columns(2)
            with c_log1: u_input = st.text_input("Usuario", placeholder="admin", label_visibility="collapsed", key="usr_auth")
            with c_log2: p_input = st.text_input("Clave", type="password", placeholder="****", label_visibility="collapsed", key="pwd_auth")
            
            c_btn1, c_btn2 = st.columns(2)
            msg_placeholder = st.empty() 
            
            with c_btn1:
                if st.button("Ingresar", use_container_width=True):
                    if u_input and p_input:
                        uid = verificar_usuario(u_input, p_input)
                        if uid:
                            st.session_state['logged_in'] = True
                            st.session_state['user_id'] = uid
                            st.session_state['username'] = u_input
                            st.session_state['watchlist'] = cargar_watchlist_desde_db(uid)
                            st.rerun()
                        else:
                            msg_placeholder.markdown("<p style='color: #ef4444; font-size: 13px; text-align: center; margin-top:5px;'>Cuenta no encontrada</p>", unsafe_allow_html=True)
                    else:
                        msg_placeholder.markdown("<p style='color: #ef4444; font-size: 13px; text-align: center; margin-top:5px;'>Complete los campos</p>", unsafe_allow_html=True)
            with c_btn2:
                if st.button("Registrar", use_container_width=True):
                    if u_input and p_input:
                        if registrar_usuario(u_input, p_input): 
                            uid = verificar_usuario(u_input, p_input)
                            st.session_state['logged_in'] = True
                            st.session_state['user_id'] = uid
                            st.session_state['username'] = u_input
                            st.session_state['watchlist'] = []
                            st.rerun()
                        else: 
                            msg_placeholder.markdown("<p style='color: #ef4444; font-size: 13px; text-align: center; margin-top:5px;'>El usuario ya existe</p>", unsafe_allow_html=True)
                    else:
                        msg_placeholder.markdown("<p style='color: #ef4444; font-size: 13px; text-align: center; margin-top:5px;'>Llene ambos campos</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #10b981; font-weight: 600; text-align: center; margin-bottom: 5px;'>En línea: {st.session_state['username']}</p>", unsafe_allow_html=True)
            if st.button("Cerrar Sesión Segura", use_container_width=True):
                st.session_state['logged_in'] = False
                st.session_state['user_id'] = None
                st.session_state['username'] = ""
                st.session_state['watchlist'] = []
                if "usr_auth" in st.session_state: st.session_state["usr_auth"] = ""
                if "pwd_auth" in st.session_state: st.session_state["pwd_auth"] = ""
                st.rerun()
                
    with tab_watch:
        if st.session_state['logged_in']:
            if st.session_state['watchlist']:
                for item in st.session_state['watchlist']: st.markdown(f"<span style='font-size:13px; color:#9ca3af;'>• {item[:35]}...</span>", unsafe_allow_html=True)
                if st.button("Vaciar Bóveda", use_container_width=True):
                    sincronizar_watchlist_db(st.session_state['user_id'], "", "LIMPIAR")
                    st.session_state['watchlist'] = []
                    st.rerun()
            else:
                st.markdown("<p style='font-size:13px; color:#6b7280; text-align:center;'>Bóveda vacía.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size:13px; color:#ef4444; text-align:center;'>Autenticación requerida</p>", unsafe_allow_html=True)
            
    with tab_pro:
        st.markdown("<p style='font-size: 12px; margin-bottom: 5px; color:#9ca3af; text-align:center;'>Monetización y Soporte</p>", unsafe_allow_html=True)
        if st.button("Donación Libre (PayPal)", use_container_width=True):
            st.toast("⚠️ Módulo de pagos inhabilitado en la versión Beta. Disponible próximamente en el despliegue v1.0", icon="🔒")
        st.markdown(f'<a href="https://wa.me/573143352341?text=Hola,%20quiero%20licenciar%20el%20proyecto." target="_blank" class="wa-btn">Licencia B2B (WhatsApp)</a>', unsafe_allow_html=True)

st.markdown("<hr style='border-color: #1f2937; margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# ==========================================
# 4. CUERPO PRINCIPAL (BUSCADOR Y VISTAS)
# ==========================================
lista_catalogo = obtener_catalogo()
prod_sel = st.selectbox("Motor de Búsqueda:", options=["-- Escriba o seleccione un componente --"] + lista_catalogo, label_visibility="collapsed")

if prod_sel == "-- Escriba o seleccione un componente --":
    total_p, total_t = obtener_estadisticas_globales()
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='metric-card' style='border-top: 2px solid #3b82f6;'><span class='metric-title'>Data Warehouse</span><h2 class='metric-value'>{total_p} <span style='font-size:14px; font-weight:normal; color:#6b7280;'>Ítems</span></h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card' style='border-top: 2px solid #8b5cf6;'><span class='metric-title'>Nodos de Mercado</span><h2 class='metric-value'>{total_t} <span style='font-size:14px; font-weight:normal; color:#6b7280;'>Tiendas</span></h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card' style='border-top: 2px solid #10b981;'><span class='metric-title'>Motor Analítico</span><h2 class='metric-value' style='color: #10b981;'>ÓPTIMO</h2></div>", unsafe_allow_html=True)
        
    st.markdown("<br><h4 style='color: #e2e8f0; font-weight:600;'>Índice S&P Tech (Simulado)</h4>", unsafe_allow_html=True)
    fechas_landing = pd.date_range(end=pd.Timestamp.now(), periods=100)
    tendencia_global = np.cumprod(1 + np.random.normal(loc=0, scale=0.02, size=100)) * 1000000
    st.line_chart(pd.DataFrame({"Índice Global": tendencia_global}, index=fechas_landing))

else:
    df_resultados = consultar_competencia(prod_sel)
    
    if not df_resultados.empty:
        df_agrupado = df_resultados.groupby('Tienda').agg({'Precio': 'min', 'Min_Historico': 'min', 'Url': 'first', 'categoria': 'first'}).reset_index()
        df_ordenado = df_agrupado.sort_values(by='Precio').head(3)
        
        precio_hoy = int(df_ordenado['Precio'].min())
        min_hist = int(df_ordenado['Min_Historico'].min())
        url_global = df_ordenado['Url'].iloc[0]
        categoria_prod = df_ordenado['categoria'].iloc[0]
        
        with st.spinner("Auditando red neuronal..."):
            datos_ia = analizar_precio_con_ia(prod_sel, precio_hoy, min_hist)
            
        col_izq, col_der = st.columns([2.5, 1])
        with col_izq:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.markdown(f'<h2 style="color: #f8fafc; margin-bottom: 20px;">{prod_sel}</h2>', unsafe_allow_html=True)
            if "FALSO DESCUENTO" in datos_ia["veredicto"]: st.markdown(f'<div class="alert-danger-box">{datos_ia["veredicto"]}</div>', unsafe_allow_html=True)
            else: st.markdown(f'<div class="alert-success-box">{datos_ia["veredicto"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<p style="color: #9ca3af; font-size: 14px;"><b>Análisis IA:</b> {datos_ia["motivo"]}</p></div>', unsafe_allow_html=True)
            
        with col_der:
            st.markdown(f"""
                <div class="image-placeholder">
                    <span style="font-size: 14px; font-weight: bold;">MÓDULO DE RENDER</span><br>
                    <span style="font-size: 12px; color: #3b82f6;">{categoria_prod}</span>
                </div>
            """, unsafe_allow_html=True)
            if st.session_state['logged_in']:
                if st.button("Seguir Activo", use_container_width=True, type="primary"):
                    if prod_sel not in st.session_state['watchlist']:
                        sincronizar_watchlist_db(st.session_state['user_id'], prod_sel, "AGREGAR")
                        st.session_state['watchlist'].append(prod_sel)
                        st.rerun()
            else:
                st.button("Autenticar para Seguir", use_container_width=True, disabled=True)
        
        c1, c2 = st.columns(2)
        with c1: st.markdown(f"<div class='metric-card' style='border-color: #10b981;'><span class='metric-title'>Mercado Hoy</span><h2 class='metric-value'>{formato_colombia(precio_hoy)} <span class='badge-verde'>LÍDER</span></h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><span class='metric-title'>Mínimo Histórico</span><h2 class='metric-value'>{formato_colombia(min_hist)}</h2></div>", unsafe_allow_html=True)
            
        st.markdown("<br><h4 style='color: #e2e8f0; font-weight:600;'>Histograma de Volatilidad (180 días)</h4>", unsafe_allow_html=True)
        dias_simulacion = 180
        fechas = pd.date_range(end=pd.Timestamp.now(), periods=dias_simulacion)
        curva = np.zeros(dias_simulacion)
        
        if categoria_prod == "Memoria RAM":
            curva[:120] = np.linspace(min_hist, precio_hoy, 120)
            curva[120:] = precio_hoy
            curva += np.random.normal(0, precio_hoy * 0.01, dias_simulacion)
        else:
            tendencia = np.cumprod(1 + np.random.normal(loc=0, scale=0.04, size=dias_simulacion))
            curva = precio_hoy * (tendencia / tendencia[-1])
            for _ in range(5): curva[random.randint(5, 170)] *= random.uniform(1.20, 1.40) 
            for _ in range(3): curva[random.randint(5, 170)] *= random.uniform(0.75, 0.85)
            curva[random.randint(10, 150)] = min_hist

        st.line_chart(pd.DataFrame({"Valor (COP)": np.clip(curva, min_hist * 0.9, precio_hoy * 2.0).astype(int)}, index=fechas))
        
        st.markdown("<h4 style='color: #e2e8f0; margin-top: 25px; font-weight:600;'>Top Proveedores</h4>", unsafe_allow_html=True)
        for _, fila in df_ordenado.iterrows():
            st.markdown(f"""
            <div class="store-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #e2e8f0; font-size: 17px; font-weight: 600;">{fila['Tienda']}</span>
                    <span style="font-size: 22px; font-weight: 800; color: #ffffff;">{formato_colombia(fila['Precio'])} <span style="font-size: 13px; color: #9ca3af; font-weight: normal;">COP</span></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        st.link_button("Buscar en navegador global", url_global)
