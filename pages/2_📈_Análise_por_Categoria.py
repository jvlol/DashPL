# pages/2_📈_Análise_por_Categoria.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📈 Análise Detalhada por Categoria")

if 'df' not in st.session_state:
    st.error("Por favor, faça o upload de um arquivo na página principal primeiro.")
    st.stop()

# Recupera os dados
df = st.session_state.df
months = st.session_state.months
grupos = st.session_state.grupos

# --- FILTROS NA SIDEBAR com st.select_slider ---
with st.sidebar:
    st.header("Filtros de Período")
    start_month, end_month = st.select_slider(
        "Selecione o intervalo de meses",
        options=months,
        value=(months[0], months[-1]),
        key="categoria_slider"
    )

start_month_idx = months.index(start_month)
end_month_idx = months.index(end_month)
selected_months = months[start_month_idx:end_month_idx + 1]
df_filtered = df[selected_months]

# --- SELEÇÃO DE CATEGORIA ---
st.header(f"Selecione uma Categoria para Análise (Período: {start_month} a {end_month})")

col1, col2 = st.columns(2)
with col1:
    grupo_selecionado = st.selectbox("1. Escolha o Grupo", list(grupos.keys()))
    start_idx, end_idx = grupos[grupo_selecionado]
    df_grupo = df.iloc[start_idx:min(end_idx + 1, len(df))]
with col2:
    if not df_grupo.empty:
        categoria_selecionada = st.selectbox("2. Escolha a Categoria", df_grupo.index)
    else:
        categoria_selecionada = None

st.markdown("---")
if categoria_selecionada:
    st.header(f"Análise da Categoria: '{categoria_selecionada}'")
    
    data_categoria = df_filtered.loc[categoria_selecionada]
    
    # Detecção inteligente de formato (percentual vs número)
    is_percent = '%' in categoria_selecionada or (data_categoria.abs().max() < 2 and data_categoria.abs().max() != 0)

    def format_kpi_value(value):
        if is_percent: return f"{value:.2%}"
        return f"{value:,.2f}"

    # --- MÉTRICAS COM O NOVO KPI DE "ÚLTIMO MÊS" ---
    st.subheader("Métricas no Período Selecionado")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4) # Adicionada uma quarta coluna

    kpi1.metric(label="Média", value=format_kpi_value(data_categoria.mean()))
    kpi2.metric(label=f"Mínimo (em {data_categoria.idxmin()})", value=format_kpi_value(data_categoria.min()))
    kpi3.metric(label=f"Máximo (em {data_categoria.idxmax()})", value=format_kpi_value(data_categoria.max()))

    # Lógica para o KPI "Último Mês vs Mês Anterior"
    if len(selected_months) >= 2:
        ultimo_mes_valor = data_categoria.iloc[-1]
        penultimo_mes_valor = data_categoria.iloc[-2]
        delta = ultimo_mes_valor - penultimo_mes_valor
        kpi4.metric(label=f"Último Mês ({selected_months[-1]})",
                    value=format_kpi_value(ultimo_mes_valor),
                    delta=format_kpi_value(delta),
                    delta_color="inverse", # Vermelho se subir (ruim para custos), verde se cair
                    help=f"Vs. Mês Anterior ({selected_months[-2]}): {format_kpi_value(penultimo_mes_valor)}")
    else:
        # Caso só um mês seja selecionado
        ultimo_mes_valor = data_categoria.iloc[-1]
        kpi4.metric(label=f"Valor em {selected_months[-1]}", value=format_kpi_value(ultimo_mes_valor))
    
    # --- GRÁFICO E TABELA (sem alterações) ---
    st.subheader("Evolução Mensal")
    fig_line = px.line(data_categoria,
                         title=f"Evolução de '{categoria_selecionada}'",
                         labels={'x': 'Mês', 'y': 'Valor'},
                         markers=True, text=data_categoria.apply(format_kpi_value))
    fig_line.update_traces(line=dict(color='royalblue', width=3))
    st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("Dados Detalhados")
    st.dataframe(data_categoria.to_frame(name='Valor').style.format(format_kpi_value))

else:
    st.info("Selecione uma categoria para visualizar a análise.")