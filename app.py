import streamlit as st
import pandas as pd
import io
import datetime
import calendar

# Configuración de la página
st.set_page_config(page_title="Simulador de Préstamos Pro", page_icon="🏦", layout="wide")

st.title("🏦 Simulador Avanzado de Préstamos")
st.markdown("Genera tu cronograma de pagos interactivo y expórtalo a Excel. Incluye cálculo de **días de gracia** con capitalización al principal.")

# Barra lateral para parámetros
with st.sidebar:
    st.header("⚙️ Configuración del Crédito")
    
    monto = st.number_input("Monto a Financiar (S/)", min_value=1000.0, value=24000.0, step=1000.0, format="%.2f")
    tasa_anual = st.number_input("Tasa Efectiva Anual (TEA) %", min_value=0.1, value=10.50, step=0.1) / 100
    
    st.markdown("---")
    st.subheader("Fechas")
    fecha_desembolso = st.date_input("Fecha de Desembolso", datetime.date.today())
    dia_pago = st.number_input("Día de Pago de cada mes", min_value=1, max_value=31, value=15, help="Día del mes en el que deseas pagar")
    
    st.markdown("---")
    sistema = st.selectbox("Sistema de Amortización", [
        "Francés (Cuota Total Constante)", 
        "Alemán (Amortización Constante)"
    ])
    
    # Para simplificar con las fechas exactas, asumiremos cuotas mensuales
    periodicidad = st.selectbox("Periodicidad de Pago", ["Mensual"]) 
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

# Conversión de tasas al periodo seleccionado (Mensual estandar)
tasa_periodo = (1 + tasa_anual)**(1/n_per) - 1
tasa_desgravamen_periodo = desgravamen_anual / n_per 

# Tasa diaria para cálculo de días de gracia (Base 360)
tasa_diaria = (1 + tasa_anual)**(1/360) - 1
tasa_desgravamen_diaria = desgravamen_anual / 360

# Determinar la fecha del primer pago (mes siguiente al desembolso)
mes_pago = fecha_desembolso.month + 1
anio_pago = fecha_desembolso.year
if mes_pago > 12:
    mes_pago = 1
    anio_pago += 1

# Ajustar si el día de pago no existe en el mes (ej. 31 de Febrero -> 28 de Febrero)
ultimo_dia_mes = calendar.monthrange(anio_pago, mes_pago)[1]
dia_real_pago = min(dia_pago, ultimo_dia_mes)

fecha_primer_pago = datetime.date(anio_pago, mes_pago, dia_real_pago)
dias_primer_periodo = (fecha_primer_pago - fecha_desembolso).days

# Calcular días de gracia (Días que exceden a un mes estándar de 30 días)
dias_gracia = max(0, dias_primer_periodo - 30)

# ---------------- NUEVA LÓGICA DE CAPITALIZACIÓN ----------------
# Calculamos el interés y seguro de los días de gracia
interes_gracia = monto * ((1 + tasa_anual)**(dias_gracia/360) - 1)
seguro_gracia = monto * (tasa_desgravamen_diaria * dias_gracia)

# Capitalizamos: El nuevo monto a financiar (Monto Préstamo Capitalizado)
monto_capitalizado = monto + interes_gracia + seguro_gracia

st.info(f"""
📅 **Primer pago:** {fecha_primer_pago.strftime('%d/%m/%Y')} | **Días hasta el primer pago:** {dias_primer_periodo} días (Incluye {dias_gracia} días de gracia)
📈 **Capitalización:** Intereses (S/{interes_gracia:.2f}) y Seguro (S/{seguro_gracia:.2f}) de los días de gracia se han sumado al principal.
💰 **Nuevo Monto a Financiar:** S/ {monto_capitalizado:,.2f}
""")
# ----------------------------------------------------------------

# Botón generador
if st.button("🚀 Generar Cronograma", type="primary", use_container_width=True):
    # El saldo inicial ahora es el monto capitalizado
    saldo = monto_capitalizado
    cronograma = []
    fecha_actual = fecha_primer_pago
    
    if "Francés" in sistema:
        tasa_total_periodo = tasa_periodo + tasa_desgravamen_periodo
        
        # Fórmula de cuota fija (anualidad) aplicada al NUEVO MONTO
        if tasa_total_periodo > 0:
            cuota_total_fija = (tasa_total_periodo * monto_capitalizado) / (1 - (1 + tasa_total_periodo)**-n_cuotas)
        else:
            cuota_total_fija = monto_capitalizado / n_cuotas
            
        for i in range(1, int(n_cuotas) + 1):
            interes = saldo * tasa_periodo
            seguro = saldo * tasa_desgravamen_periodo
            
            cuota_actual = cuota_total_fija
            amortizacion = cuota_actual - interes - seguro
            
            if i == int(n_cuotas):
                amortizacion = saldo
                cuota_actual = amortizacion + interes + seguro
                
            saldo -= amortizacion
            
            cronograma.append([i, fecha_actual.strftime("%d/%m/%Y"), amortizacion, interes, seguro, cuota_actual, max(0, saldo)])
            
            # Calcular siguiente fecha de pago
            mes_siguiente = fecha_actual.month + 1
            anio_siguiente = fecha_actual.year
            if mes_siguiente > 12:
                mes_siguiente = 1
                anio_siguiente += 1
            
            ult_dia = calendar.monthrange(anio_siguiente, mes_siguiente)[1]
            dia_p = min(dia_pago, ult_dia)
            fecha_actual = datetime.date(anio_siguiente, mes_siguiente, dia_p)
            
    elif
