import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="Simulador de Préstamos Pro", page_icon="🏦", layout="wide")

st.title("🏦 Simulador Avanzado de Préstamos")
st.markdown("Genera tu cronograma de pagos interactivo y expórtalo a Excel. Ideal para simular escenarios hipotecarios, vehiculares o de capital de trabajo.")

# Barra lateral para parámetros
with st.sidebar:
    st.header("⚙️ Configuración del Crédito")
    
    monto = st.number_input("Monto a Financiar", min_value=1000.0, value=50000.0, step=1000.0, format="%.2f")
    tasa_anual = st.number_input("Tasa Efectiva Anual (TEA) %", min_value=0.1, value=12.0, step=0.1) / 100
    
    sistema = st.selectbox("Sistema de Amortización", [
        "Francés (Cuota Constante)", 
        "Alemán (Amortización Constante)"
    ])
    
    periodicidad = st.selectbox("Periodicidad de Pago", ["Mensual", "Trimestral", "Semestral", "Anual"])
    n_cuotas = st.number_input("Número de Cuotas", min_value=1, value=36, step=1)
    
    st.markdown("---")
    st.subheader("Costos Adicionales")
    desgravamen_anual = st.number_input("Seguro de Desgravamen Anual %", min_value=0.0, value=1.2, step=0.1, help="Porcentaje anual que se cobrará proporcionalmente sobre el saldo restante en cada cuota.") / 100

# Lógica matemática financiera
periodos_por_anio = {"Mensual": 12, "Trimestral": 4, "Semestral": 2, "Anual": 1}
n_per = periodos_por_anio[periodicidad]

# Conversión de tasas
tasa_periodo = (1 + tasa_anual)**(1/n_per) - 1
tasa_desgravamen_periodo = desgravamen_anual / n_per

# Botón generador
if st.button("🚀 Generar Cronograma", type="primary", use_container_width=True):
    saldo = monto
    cronograma = []
    
    if "Francés" in sistema:
        # Fórmula de cuota fija: C = P * [i / (1 - (1+i)^-n)]
        cuota_fija = (tasa_periodo * monto) / (1 - (1 + tasa_periodo)**-n_cuotas)
        
        for i in range(1, int(n_cuotas) + 1):
            interes = saldo * tasa_periodo
            amortizacion = cuota_fija - interes
            seguro = saldo * tasa_desgravamen_periodo
            cuota_total = cuota_fija + seguro
            saldo -= amortizacion
            
            cronograma.append([i, amortizacion, interes, seguro, cuota_total, max(0, saldo)])
            
    elif "Alemán" in sistema:
        # Amortización fija de capital
        amortizacion = monto / n_cuotas
        
        for i in range(1, int(n_cuotas) + 1):
            interes = saldo * tasa_periodo
            seguro = saldo * tasa_desgravamen_periodo
            cuota_total = amortizacion + interes + seguro
            saldo -= amortizacion
            
            cronograma.append([i, amortizacion, interes, seguro, cuota_total, max(0, saldo)])

    # Creación del DataFrame
    columnas = ["Periodo", "Amortización de Capital", "Interés", "Seguro Desgravamen", "Cuota Total", "Saldo Deudor"]
    df = pd.DataFrame(cronograma, columns=columnas)
    
    # Redondeo para mejor visualización
    df = df.round(2)
    
    # Métricas clave en la parte superior
    st.subheader("📊 Resumen del Crédito")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monto Total", f"S/ {monto:,.2f}")
    col2.metric("Total Intereses", f"S/ {df['Interés'].sum():,.2f}")
    col3.metric("Total Desgravamen", f"S/ {df['Seguro Desgravamen'].sum():,.2f}")
    col4.metric("Total a Pagar", f"S/ {df['Cuota Total'].sum():,.2f}")

    # Mostrar tabla interactiva
    st.subheader("🗓️ Cronograma de Pagos")
    st.dataframe(
        df.style.format({
            "Amortización de Capital": "{:,.2f}",
            "Interés": "{:,.2f}",
            "Seguro Desgravamen": "{:,.2f}",
            "Cuota Total": "{:,.2f}",
            "Saldo Deudor": "{:,.2f}"
        }), 
        use_container_width=True, 
        hide_index=True
    )

    # Lógica para exportar a Excel en memoria (sin crear archivos temporales)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Cronograma')
        
        # Dar formato básico a las columnas en Excel
        workbook = writer.book
        worksheet = writer.sheets['Cronograma']
        money_format = workbook.add_format({'num_format': '#,##0.00'})
        worksheet.set_column('B:F', 18, money_format)
        worksheet.set_column('A:A', 10)
        
    excel_data = output.getvalue()

    # Botón de descarga
    st.download_button(
        label="📥 Descargar Cronograma en Excel",
        data=excel_data,
        file_name="Cronograma_Prestamo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )