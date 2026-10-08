import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="Simulador de Préstamos Pro", page_icon="🏦", layout="wide")

st.title("🏦 Simulador Avanzado de Préstamos")
st.markdown("Genera tu cronograma de pagos interactivo y expórtalo a Excel. Calcula con el estándar bancario donde la **Cuota Total se mantiene constante**.")

# Barra lateral para parámetros
with st.sidebar:
    st.header("⚙️ Configuración del Crédito")
    
    monto = st.number_input("Monto a Financiar (S/)", min_value=1000.0, value=24000.0, step=1000.0, format="%.2f")
    tasa_anual = st.number_input("Tasa Efectiva Anual (TEA) %", min_value=0.1, value=10.50, step=0.1) / 100
    
    sistema = st.selectbox("Sistema de Amortización", [
        "Francés (Cuota Total Constante)", 
        "Alemán (Amortización Constante)"
    ])
    
    periodicidad = st.selectbox("Periodicidad de Pago", ["Mensual", "Trimestral", "Semestral", "Anual"])
    n_cuotas = st.number_input("Número de Cuotas", min_value=1, value=60, step=1)
    
    st.markdown("---")
    st.subheader("Costos Adicionales")
    desgravamen_anual = st.number_input(
        "Seguro de Desgravamen Anual %", 
        min_value=0.0, 
        value=1.38, 
        step=0.01, 
        help="Ej: 1.38% anual (se cobra mensualmente sobre el saldo deudor)"
    ) / 100

# Lógica matemática financiera
periodos_por_anio = {"Mensual": 12, "Trimestral": 4, "Semestral": 2, "Anual": 1}
n_per = periodos_por_anio[periodicidad]

# Conversión de tasas al periodo seleccionado
tasa_periodo = (1 + tasa_anual)**(1/n_per) - 1
tasa_desgravamen_periodo = desgravamen_anual / n_per  # Tasa nominal proporcional para el seguro

# Botón generador
if st.button("🚀 Generar Cronograma", type="primary", use_container_width=True):
    saldo = monto
    cronograma = []
    
    if "Francés" in sistema:
        # Sumamos las tasas para que la fórmula calcule una CUOTA TOTAL fija (capital + interes + seguro)
        tasa_total_periodo = tasa_periodo + tasa_desgravamen_periodo
        
        # Fórmula de cuota fija (anualidad)
        if tasa_total_periodo > 0:
            cuota_total_fija = (tasa_total_periodo * monto) / (1 - (1 + tasa_total_periodo)**-n_cuotas)
        else:
            cuota_total_fija = monto / n_cuotas
        
        for i in range(1, int(n_cuotas) + 1):
            interes = saldo * tasa_periodo
            seguro = saldo * tasa_desgravamen_periodo
            
            # La amortización de capital es el "residuo" de la cuota total después de pagar interés y seguro
            amortizacion = cuota_total_fija - interes - seguro
            
            # Ajuste de última cuota para asegurar que el saldo cierre en 0 exacto
            if i == int(n_cuotas):
                amortizacion = saldo
                cuota_total_fija = amortizacion + interes + seguro
                
            saldo -= amortizacion
            
            # Guardamos el mes
            cronograma.append([i, amortizacion, interes, seguro, cuota_total_fija, max(0, saldo)])
            
    elif "Alemán" in sistema:
        # En el sistema alemán, la cuota de amortización de capital es fija
        amortizacion = monto / n_cuotas
        
        for i in range(1, int(n_cuotas) + 1):
            interes = saldo * tasa_periodo
            seguro = saldo * tasa_desgravamen_periodo
            cuota_total = amortizacion + interes + seguro
            saldo -= amortizacion
            
            # Ajuste de seguridad para el último saldo
            if i == int(n_cuotas):
                saldo = 0
                
            cronograma.append([i, amortizacion, interes, seguro, cuota_total, max(0, saldo)])

    # Creación del DataFrame
    columnas = ["Periodo", "Amortización de Capital", "Interés", "Seguro Desgravamen", "Cuota Total", "Saldo Deudor"]
    df = pd.DataFrame(cronograma, columns=columnas)
    
    # Métricas clave en la parte superior
    st.subheader("📊 Resumen del Crédito")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monto Total a Financiar", f"S/ {monto:,.2f}")
    col2.metric("Total Intereses", f"S/ {df['Interés'].sum():,.2f}")
    col3.metric("Total Seguro Desgravamen", f"S/ {df['Seguro Desgravamen'].sum():,.2f}")
    col4.metric("Total a Pagar (Capital + Costos)", f"S/ {df['Cuota Total'].sum():,.2f}")

    # Mostrar tabla interactiva (sin alterar los datos reales, solo formateo visual)
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
        
        # Ajustar anchos y formatos
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:F', 20, money_format)
        
    excel_data = output.getvalue()

    # Botón de descarga
    st.download_button(
        label="📥 Descargar Cronograma en Excel",
        data=excel_data,
        file_name="Cronograma_Prestamo_Pro.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
