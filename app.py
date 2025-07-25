# app.py

import streamlit as st
import pandas as pd
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Análise Financeira",
    page_icon="💰",
    layout="wide"
)

# --- FUNÇÃO DE CACHE PARA CARREGAR DADOS ---
@st.cache_data
def load_data(file_content):
    try:
        df = pd.read_excel(BytesIO(file_content), header=0, index_col=0)
        for col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        df.dropna(how='all', axis=0, inplace=True)
        df.dropna(how='all', axis=1, inplace=True)
        grupos = {
            'CMV': (1, 9), 'Folha': (10, 28), 'Folha Retorno': (29, 39),
            'Despesas Gerais': (40, 64), 'Estoques': (65, 68), 'Descontos': (69, 80),
            'Compras e Ineficiência': (81, 83)
        }
        return df, grupos
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return None, None

# --- SIDEBAR E UPLOAD PERSISTENTE ---
with st.sidebar:
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)
    st.title("Menu de Navegação")
    if 'file_content' not in st.session_state:
        st.session_state.file_content = None

    uploaded_file = st.file_uploader("Faça o upload do seu arquivo Excel", type=["xlsx", "xls"])
    if uploaded_file is not None:
        st.session_state.file_content = uploaded_file.getvalue()
        st.session_state.file_name = uploaded_file.name

    if st.session_state.file_content is not None:
        st.success(f"Arquivo `{st.session_state.get('file_name', '...')} ` carregado.")
        if st.button("Remover arquivo"):
            st.session_state.file_content = None
            st.session_state.file_name = None
            st.rerun()

# --- PÁGINA PRINCIPAL ---
st.title("🚀 Dashboard de Análise Financeira")

if st.session_state.file_content is not None:
    df, grupos = load_data(st.session_state.file_content)
    if df is not None:
        st.session_state.df, st.session_state.grupos, st.session_state.months = df, grupos, df.columns.tolist()

        # --- FILTRO DE MÊS NA PÁGINA PRINCIPAL ---
        st.markdown("---")
        months_list = st.session_state.months
        _, col_filter, _ = st.columns([2, 3, 2])
        with col_filter:
            focus_month = st.selectbox(
                "🗓️ **Selecione o Mês de Análise**",
                options=months_list,
                index=len(months_list) - 1
            )
        st.markdown("---")

        focus_month_index = months_list.index(focus_month)
        previous_month = months_list[focus_month_index - 1] if focus_month_index > 0 else None
        df_historical = df.iloc[:, :focus_month_index] if focus_month_index > 0 else None

        cat = {
            'cmv_geral': df.index[6], 'cmv_ab': df.index[7], 'inef_perc': df.index[8],
            'inef_rs': df.index[9], 'compras': df.index[81], 'inef_compra_perc': df.index[82],
            'inef_compra_rs': df.index[83], 'desp_folha': df.index[39], 'desp_geral': df.index[64],
            'descontos': df.index[80]
        }
        def format_value(value, is_percent=False):
            if not isinstance(value, (int, float)) or pd.isna(value): return "N/A"
            if is_percent: return f"{value:.2%}"
            return f"{value:,.2f}"

        # --- ANÁLISE MENSAL COM KPIs RESTAURADOS ---
        if previous_month:
            st.header("📊 KPIs Principais (Resumo Geral)")
            st.subheader(f"Análise de {focus_month} (Comparativo com {previous_month})")
            col1, col2, col3, col4 = st.columns(4)

            with col1: # CMV
                st.markdown("###### CMV")
                # CMV Geral
                valor_focal = df.loc[cat['cmv_geral'], focus_month]
                valor_anterior = df.loc[cat['cmv_geral'], previous_month]
                st.metric(f"{cat['cmv_geral']} ({focus_month})", format_value(valor_focal, True), delta=format_value(valor_focal - valor_anterior, True), delta_color="inverse", help=f"Vs. {previous_month}: {format_value(valor_anterior, True)}")
                # CMV A&B
                valor_focal = df.loc[cat['cmv_ab'], focus_month]
                valor_anterior = df.loc[cat['cmv_ab'], previous_month]
                st.metric(f"{cat['cmv_ab']} ({focus_month})", format_value(valor_focal, True), delta=format_value(valor_focal - valor_anterior, True), delta_color="inverse", help=f"Vs. {previous_month}: {format_value(valor_anterior, True)}")

            with col2: # Ineficiências
                st.markdown("###### Ineficiências")
                # Ineficiência %
                valor_focal = df.loc[cat['inef_perc'], focus_month]
                valor_anterior = df.loc[cat['inef_perc'], previous_month]
                st.metric(f"{cat['inef_perc']} ({focus_month})", format_value(valor_focal), delta=format_value(valor_focal - valor_anterior), delta_color="inverse", help=f"Vs. {previous_month}: {format_value(valor_anterior)}")
                # Ineficiência R$
                valor_focal = df.loc[cat['inef_rs'], focus_month]
                valor_anterior = df.loc[cat['inef_rs'], previous_month]
                st.metric(f"{cat['inef_rs']} ({focus_month})", f"R$ {format_value(valor_focal)}", delta=f"R$ {format_value(valor_focal - valor_anterior)}", delta_color="inverse", help=f"Vs. {previous_month}: R$ {format_value(valor_anterior)}")

            with col3: # Compras e Descontos
                st.markdown("###### Compras e Descontos")
                # Compras %
                valor_focal = df.loc[cat['compras'], focus_month]
                valor_anterior = df.loc[cat['compras'], previous_month]
                st.metric(f"{cat['compras']} ({focus_month})", format_value(valor_focal, True), delta=format_value(valor_focal - valor_anterior, True), delta_color="inverse", help=f"Vs. {previous_month}: {format_value(valor_anterior, True)}")
                # Descontos %
                valor_focal = df.loc[cat['descontos'], focus_month]
                valor_anterior = df.loc[cat['descontos'], previous_month]
                st.metric(f"{cat['descontos']} ({focus_month})", format_value(valor_focal, True), delta=format_value(valor_focal - valor_anterior, True), delta_color="inverse", help=f"Vs. {previous_month}: {format_value(valor_anterior, True)}")
                 
            with col4: # Despesas Totais
                st.markdown("###### Despesas Totais")
                # Despesa de Folha
                valor_focal = df.loc[cat['desp_folha'], focus_month]
                valor_anterior = df.loc[cat['desp_folha'], previous_month]
                st.metric(f"{cat['desp_folha']} ({focus_month})", format_value(valor_focal, True), delta=format_value(valor_focal - valor_anterior, True), delta_color="inverse", help=f"Vs. {previous_month}: {format_value(valor_anterior, True)}")
                # Despesas Gerais
                valor_focal = df.loc[cat['desp_geral'], focus_month]
                valor_anterior = df.loc[cat['desp_geral'], previous_month]
                st.metric(f"{cat['desp_geral']} ({focus_month})", format_value(valor_focal, True), delta=format_value(valor_focal - valor_anterior, True), delta_color="inverse", help=f"Vs. {previous_month}: {format_value(valor_anterior, True)}")
        else:
            st.info(f"Analisando {focus_month}. Não há mês anterior para comparação mensal.")

        # --- ANÁLISE HISTÓRICA COMPLETA E DINÂMICA ---
        if df_historical is not None and not df_historical.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader(f"Análise Histórica ({focus_month} vs. Média até {previous_month})")
            col1_hist, col2_hist, col3_hist, _ = st.columns(4)

            with col1_hist:
                st.markdown("###### CMV")
                # CMV Geral
                media_hist = df_historical.loc[cat['cmv_geral']].mean()
                valor_focal = df.loc[cat['cmv_geral'], focus_month]
                st.metric(f"Média Hist. {cat['cmv_geral']}", format_value(media_hist, True), delta=format_value(valor_focal - media_hist, True), delta_color="inverse", help=f"Valor de {focus_month}: {format_value(valor_focal, True)}")
            
            with col2_hist:
                 # CMV A&B
                st.markdown("######  ", unsafe_allow_html=True) # Espaçador
                media_hist = df_historical.loc[cat['cmv_ab']].mean()
                valor_focal = df.loc[cat['cmv_ab'], focus_month]
                st.metric(f"Média Hist. {cat['cmv_ab']}", format_value(media_hist, True), delta=format_value(valor_focal - media_hist, True), delta_color="inverse", help=f"Valor de {focus_month}: {format_value(valor_focal, True)}")

            with col3_hist:
                st.markdown("###### Ineficiência Compra R$")
                media_hist = df_historical.loc[cat['inef_compra_rs']].mean()
                valor_focal = df.loc[cat['inef_compra_rs'], focus_month]
                st.metric(f"Média Hist. {cat['inef_compra_rs']}", f"R$ {format_value(media_hist)}", delta=f"R$ {format_value(valor_focal - media_hist)}", delta_color="inverse", help=f"Valor de {focus_month}: R$ {format_value(valor_focal)}")
        
        # --- PRE-VISUALIZAÇÃO DOS DADOS ---
        st.markdown("---")
        st.subheader("Pré-visualização dos Dados Carregados")
        st.dataframe(df.style.format("{:,.2f}", na_rep="-"))
else:
    st.markdown("### Bem-vindo! Faça o upload do seu arquivo no menu à esquerda para começar.")
    st.info("Aguardando o upload de um arquivo Excel.")