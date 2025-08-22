import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials # <-- Correcta
import plotly.express as px
import re
import gspread
# La línea de oauth2client se eliminó
from io import StringIO

# ---------------- CONFIG ----------------
SHEET_ID = "16PzfegYvX0ywjOZ0zh3MS9-xxNBNugeMeXGLDqykQRs"
SHEET_NAME = "Respuestas de formulario 1"

st.set_page_config(page_title="Informe Dinamizadores", layout="wide")

# ---------------- HELPERS ----------------
def normalize_cedula(ced):
    if pd.isna(ced): 
        return None
    ced = re.sub(r"[^0-9]", "-", str(ced))
    ced = re.sub(r"-+", "-", ced)
    return ced.strip("-")

def unify_dinamizadores(df, col_cedula, col_nombre):
    df["_cedula_norm"] = df[col_cedula].apply(normalize_cedula)
    name_map = {}
    for i, row in df.iterrows():
        ced = row["_cedula_norm"]
        if ced and ced not in name_map:
            name_map[ced] = row[col_nombre]
    df["_nombre_unificado"] = df["_cedula_norm"].map(name_map)
    return df

def load_sheet():
    """
    Se conecta a Google Sheets usando los Secrets de Streamlit, 
    abre la hoja correcta y la devuelve como un DataFrame.
    """
    try:
        # Carga las credenciales desde los Secrets de Streamlit
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ],
        )
        # Autoriza y se conecta a gspread
        client = gspread.authorize(creds)
        
        # Abre la hoja por ID y nombre y la convierte a DataFrame
        ws = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
        
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        st.warning("Verifica que los 'Secrets' estén bien configurados en el panel de Streamlit.")
        return pd.DataFrame() # Devuelve un DataFrame vacío si hay error

@st.cache_data(ttl=300)
def get_data():
    df = load_sheet()
    # Normalizaciones
    df = unify_dinamizadores(df, "Cédula", "Nombre y apellido")
    # Año numérico
    if "Año" in df.columns:
        df["Año"] = pd.to_numeric(df["Año"], errors="coerce")
    return df

def clean_filter_options(series):
    return sorted([x for x in series.dropna().unique() if str(x).strip() not in ["", "Agregar al listado"]])

# ---------------- MAIN APP ----------------
st.title("📊 Informe de Asistencia Dinamizadores")

if st.sidebar.button("🔄 Actualizar"):
    st.cache_data.clear()

df = get_data()

# ---------------- FILTERS ----------------
años = clean_filter_options(df["Año"]) if "Año" in df else []
meses = clean_filter_options(df["Mes"]) if "Mes" in df else []
regs = clean_filter_options(df["Regional"]) if "Regional" in df else []
provs = clean_filter_options(df["Provincia"]) if "Provincia" in df else []
facs = clean_filter_options(df["Facilitador"]) if "Facilitador" in df else []

st.sidebar.header("Filtros")
sel_años = st.sidebar.multiselect("Año", años, default=años)
sel_meses = st.sidebar.multiselect("Mes", meses, default=meses)
sel_reg = st.sidebar.multiselect("Regional", regs, default=regs)
sel_prov = st.sidebar.multiselect("Provincia", provs, default=provs)
sel_fac = st.sidebar.multiselect("Facilitador", facs, default=facs)

df_f = df.copy()
if sel_años: df_f = df_f[df_f["Año"].isin(sel_años)]
if sel_meses: df_f = df_f[df_f["Mes"].isin(sel_meses)]
if sel_reg: df_f = df_f[df_f["Regional"].isin(sel_reg)]
if sel_prov: df_f = df_f[df_f["Provincia"].isin(sel_prov)]
if sel_fac: df_f = df_f[df_f["Facilitador"].isin(sel_fac)]

# ---------------- TABS ----------------
tabs = st.tabs(["📈 KPI", "👥 Dinamizadores", "⭐ Top Dinamizadores", "🏢 Participación por Infoplazas"])

# ---- KPI ----
with tabs[0]:
    st.subheader("Sección 1: Datos completos")
    total_registros = len(df_f)
    sesiones_unicas = df_f["CountSesión"].nunique() if "CountSesión" in df_f else 0
    prom_particip = total_registros / sesiones_unicas if sesiones_unicas > 0 else 0
    c1,c2,c3 = st.columns(3)
    c1.metric("Total registros", f"{total_registros:,}")
    c2.metric("Sesiones únicas", f"{sesiones_unicas:,}")
    c3.metric("Promedio participación/sesión", f"{prom_particip:,.2f}")
    
    st.subheader("Sección 2: Datos únicos")
    din_uniq = df_f["_cedula_norm"].nunique()
    inf_uniq = df_f["#"].nunique() if "#" in df_f else 0
    temas_uniq = df_f["Tema"].nunique() if "Tema" in df_f else 0
    c1,c2,c3 = st.columns(3)
    c1.metric("Dinamizadores únicos", f"{din_uniq:,}")
    c2.metric("Infoplazas únicas", f"{inf_uniq:,}")
    c3.metric("Temas únicos", f"{temas_uniq:,}")
    
    st.markdown("---")
    st.subheader("Gráficos")
    if "Mes" in df_f:
        g1 = df_f.groupby(["Año","Mes"])["CountSesión"].nunique().reset_index(name="Sesiones")
        st.plotly_chart(px.bar(g1, x="Mes", y="Sesiones", color="Año", barmode="group"), use_container_width=True)
    if "Mes" in df_f:
        g2 = df_f.groupby(["Año","Mes"])["_cedula_norm"].nunique().reset_index(name="Dinamizadores")
        st.plotly_chart(px.bar(g2, x="Mes", y="Dinamizadores", color="Año", barmode="group"), use_container_width=True)
    if "Regional" in df_f:
        g3 = df_f.groupby("Regional")["_cedula_norm"].nunique().reset_index(name="Dinamizadores")
        st.plotly_chart(px.bar(g3, x="Regional", y="Dinamizadores"), use_container_width=True)
    if "Provincia" in df_f:
        g4 = df_f.groupby("Provincia")["_cedula_norm"].nunique().reset_index(name="Dinamizadores")
        st.plotly_chart(px.bar(g4, x="Provincia", y="Dinamizadores"), use_container_width=True)

# ---- Dinamizadores ----

with tabs[1]:
    st.subheader("Listado de Dinamizadores")
    if "_cedula_norm" in df_f:
        df_f["InfoplazaFull"] = df_f["#"].astype(str) + " - " + df_f["INFOPLAZAS"]

        tabla = df_f.sort_values("Marca temporal").groupby("_cedula_norm").agg(
            Nombre=("_nombre_unificado", "first"),
            Infoplaza=("InfoplazaFull", "first"),
            Participaciones=("CountSesión", "count"),
            TemasUnicos=("Tema", "nunique")
        ).reset_index().rename(columns={"_cedula_norm": "Cédula"})
        inf_opts = sorted(tabla["Infoplaza"].dropna().unique())
        sel_inf = st.selectbox("Filtrar por Infoplaza", ["Todos"] + inf_opts)
        if sel_inf != "Todos":
            tabla = tabla[tabla["Infoplaza"].str.contains(sel_inf)]

        st.dataframe(tabla)

        csv = tabla.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar CSV", csv, "dinamizadores.csv", "text/csv")


# ---- Top Dinamizadores ----
with tabs[2]:
    st.subheader("Top Dinamizadores")
    if "#" in df_f and "Infoplaza" in df.columns:
        df_f["InfoplazaFull"] = df_f["#"].astype(str) + " - " + df_f["INFOPLAZAS"]
        tabla = df_f.groupby(["_cedula_norm","_nombre_unificado","InfoplazaFull"]).size().reset_index(name="Participaciones")
        tabla.rename(columns={"_cedula_norm":"Cédula","_nombre_unificado":"Nombre","InfoplazaFull":"Infoplaza"}, inplace=True)
        top_n = st.slider("Cantidad",1,20,5)
        top_tabla = tabla.sort_values("Participaciones", ascending=False).head(top_n)
        st.dataframe(top_tabla)
        st.plotly_chart(px.bar(top_tabla, x="Participaciones", y="Nombre", color="Infoplaza", orientation="h"), use_container_width=True)

# ---- Participación por Infoplazas ----
with tabs[3]:
    st.subheader("Participación por Infoplazas")

    required_cols = ["#", "INFOPLAZAS", "Regional", "Provincia", "CountSesión", "_cedula_norm", "_nombre_unificado"]
    if all(col in df.columns for col in required_cols) and not df_f.empty:
        
        # 1. PREPARACIÓN DE DATOS DE PARTICIPACIÓN (SIN CAMBIOS)
        df_f["InfoplazaFull"] = df_f["#"].astype(str) + " - " + df_f["INFOPLAZAS"]
        
        summary_table = df_f.groupby("InfoplazaFull").agg(
            TotalSesiones=("CountSesión", "count"),
            SesionesUnicas=("CountSesión", "nunique"),
            DinamizadoresUnicos=("_cedula_norm", "nunique")
        ).reset_index()

        detail_table = df_f.groupby(["InfoplazaFull", "_cedula_norm", "_nombre_unificado"]).agg(
            TotalParticipacion=("CountSesión", "count"),
            ParticipacionUnica=("CountSesión", "nunique")
        ).reset_index().rename(columns={
            "_cedula_norm": "Cédula", 
            "_nombre_unificado": "Nombre del Dinamizador"
        })

        # 2. CATÁLOGO MAESTRO FILTRADO (LÓGICA MEJORADA)
        # Se crea el catálogo maestro desde el DataFrame original `df` para tener la lista completa.
        catalogo_maestro = df[["#", "INFOPLAZAS", "Regional", "Provincia"]].drop_duplicates().dropna()
        
        # APLICAMOS LOS FILTROS DE LA BARRA LATERAL AL CATÁLOGO MAESTRO.
        # Esto asegura que la lista de Infoplazas se ajusta a la selección del usuario.
        if sel_reg:
            catalogo_maestro = catalogo_maestro[catalogo_maestro["Regional"].isin(sel_reg)]
        if sel_prov:
            catalogo_maestro = catalogo_maestro[catalogo_maestro["Provincia"].isin(sel_prov)]
        
        catalogo_maestro["InfoplazaFull"] = catalogo_maestro["#"].astype(str) + " - " + catalogo_maestro["INFOPLAZAS"]
        
        # 3. UNIÓN FINAL (MERGE)
        # Se une el catálogo ya filtrado con los datos de participación.
        final_summary = pd.merge(
            catalogo_maestro[["InfoplazaFull"]], 
            summary_table, 
            on="InfoplazaFull", 
            how="left"
        ).fillna(0)
        
        for col in ["TotalSesiones", "SesionesUnicas", "DinamizadoresUnicos"]:
            final_summary[col] = final_summary[col].astype(int)

        # 4. FILTROS DE VISTA Y EXPORTACIÓN (SIN CAMBIOS)
        show_only = st.checkbox("Mostrar solo infoplazas sin participación")
        if show_only:
            display_data = final_summary[final_summary["TotalSesiones"] == 0]
        else:
            display_data = final_summary.sort_values("TotalSesiones", ascending=False)
        
        csv = display_data.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Exportar Resumen CSV", csv, "resumen_participacion_infoplazas.csv", "text/csv")
        st.markdown("---")

        # 5. RENDERIZADO DE LA VISTA DESPLEGABLE (SIN CAMBIOS)
        if display_data.empty:
            st.info("No hay Infoplazas que coincidan con los filtros de Regional o Provincia seleccionados.")
        else:
            detail_table.set_index("InfoplazaFull", inplace=True)
            
            for _, row in display_data.iterrows():
                infoplaza_name = row["InfoplazaFull"]
                
                expander_label = (
                    f"{infoplaza_name} | **Total de Sesiones:** {row['TotalSesiones']} | "
                    f"**Sesiones Únicas:** {row['SesionesUnicas']} | "
                    f"**Dinamizadores Únicos:** {row['DinamizadoresUnicos']}"
                )
                
                with st.expander(expander_label):
                    if row['TotalSesiones'] > 0 and row['DinamizadoresUnicos'] > 0:
                        try:
                            dinamizador_details = detail_table.loc[[infoplaza_name]]
                            st.dataframe(
                                dinamizador_details[["Cédula", "Nombre del Dinamizador", "TotalParticipacion", "ParticipacionUnica"]].reset_index(drop=True)
                            )
                        except KeyError:
                            st.warning("No se encontraron detalles de dinamizadores para esta infoplaza.")
                    else:
                        st.info("Esta infoplaza no registra participación con los filtros actuales.")
    
    elif df_f.empty:
         st.info("No hay datos de participación que coincidan con los filtros seleccionados.")
    else:
        st.warning("Faltan columnas necesarias en la hoja de Google Sheets para generar este reporte.")