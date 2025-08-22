# Informe de Asistencia Dinamizadores (Streamlit)

App en **Streamlit** con conexión **en tiempo real** a Google Sheets.

## 📌 Datos
- Hoja: `Respuestas de formulario 1`
- Spreadsheet ID: `16PzfegYvX0ywjOZ0zh3MS9-xxNBNugeMeXGLDqykQRs`
- URL pública: https://docs.google.com/spreadsheets/d/16PzfegYvX0ywjOZ0zh3MS9-xxNBNugeMeXGLDqykQRs/edit?usp=sharing

> La app por defecto se conecta usando el **CSV público** (no requiere credenciales). Si deseas usar **Service Account**, configura `secrets.toml` como se indica más abajo y cambia la función de carga.

## ▶️ Ejecución local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Despliegue en Streamlit Cloud (gratis)
1. Sube este repo a GitHub.
2. En https://share.streamlit.io/ conecta tu repo y elige `app.py`.
3. **(Opcional)** Configura **Secrets** si decides usar cuenta de servicio JSON:
   - En la página de tu app → *Settings* → *Advanced settings* → *Secrets*.
   - Pega tu JSON bajo la clave `[gcp_service_account]` (ver plantilla en `.streamlit/secrets-template.toml`).

> Nota: Si tu hoja es pública, no necesitas secretos. Para hojas privadas, usa Service Account.

## 🔐 Usar Service Account (opcional)
- Crea el archivo `.streamlit/secrets.toml` con el contenido del JSON (ver plantilla).
- Comparte la hoja de cálculo con el email de la cuenta de servicio (`xxx@xxx.iam.gserviceaccount.com`) con permiso de **lector** o **editor**.

## 🗂 Estructura
```
/
├─ app.py
├─ requirements.txt
├─ README.md
└─ .streamlit/
   ├─ config.toml
   └─ secrets-template.toml
```

## 🖌 Diseño
- Interfaz moderna, KPIs arriba, pestañas para secciones, botón **Actualizar** en la barra lateral.

