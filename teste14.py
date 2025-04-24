import pandas as pd
import streamlit as st
import plotly.express as px
from io import StringIO


# Configurações da página
st.set_page_config(layout="wide", page_title="Dados SUS - Procedimentos")

@st.cache_data
def load_data():
    return pd.read_csv('C:/Users/Victor/Desktop/PEGA/testes/cidades_e_procedimentos.csv', header=0)

# Carrega os dados com cache
dados_sus = load_data()

# Verifica e renomeia colunas se necessário
if 'procedimento' in dados_sus.columns and 'nome_procedimento' not in dados_sus.columns:
    dados_sus = dados_sus.rename(columns={'procedimento': 'nome_procedimento'})

# Interface principal
#st.title("Análise de Procedimentos do SUS")
#st.header("Visualização de procedimentos")

# Sidebar - Filtros e opções
with st.sidebar:
    st.subheader("Filtros")
    
    # Lista de procedimentos com scroll
    st.markdown("*Selecione os procedimentos:*")
    procedimentos = sorted(dados_sus["nome_procedimento"].unique())
    procedimentos_selecionados = st.multiselect(
        "Procedimentos (selecione um ou mais)",
        procedimentos,
        default=procedimentos[0] if len(procedimentos) > 0 else None,
        key="procedimentos_select",
        label_visibility="collapsed"
    )
    
    # Filtro por cidade (opcional)
    cidades = sorted(dados_sus["cidade_origem"].unique())
    cidade_selecionada = st.selectbox(
        "Filtrar por cidade (opcional)",
        ["Todas"] + cidades
    )
    
    # Opção para baixar CSV
    st.divider()
    st.subheader("Exportar Dados")
    
    # Cria um buffer para o CSV
    csv_buffer = StringIO()
    dados_sus.to_csv(csv_buffer, index=False)
    csv_str = csv_buffer.getvalue()
    
    st.download_button(
        label="Baixar dados completos (CSV)",
        data=csv_str,
        file_name="dados_sus_procedimentos.csv",
        mime="text/csv"
    )

# Aplica filtros
if procedimentos_selecionados:
    dados_filtrados = dados_sus[dados_sus["nome_procedimento"].isin(procedimentos_selecionados)]
else:
    dados_filtrados = dados_sus.copy()

if cidade_selecionada != "Todas":
    dados_filtrados = dados_filtrados[dados_filtrados["cidade_origem"] == cidade_selecionada]

# Visualização do Mapa
st.subheader("Mapa de Procedimentos por Cidade de Origem")

CENTRO_RS = dict(lat=-30.3, lon=-52.0)
ZOOM_PADRAO = 5

if not dados_filtrados.empty:
    # Agrupa os dados
    dados_agrupados = dados_filtrados.groupby(
        ['lat_cid_ori', 'long_cid_ori', 'cidade_origem', 'nome_procedimento']
    )['total_ocorrencias'].sum().reset_index()

    # Normaliza intensidade para escala de cores
    dados_agrupados['intensidade'] = dados_agrupados['total_ocorrencias'] / dados_agrupados['total_ocorrencias'].max()


    # Cores personalizadas, da mais clara até a mais escura
    cores_personalizadas = [
    # azul muito claro
    "#a0c4ff",
    "#80afff",
    "#609bff",
    "#4087ff",
    "#206fff",
    "#0057e0",
    "#003fc0",
    "#0000c0"   # azul profundo
]
    
    # Tamanho desejado
    tamanho_maximo = 90
    tamanho_minimo = 80

    fig = px.scatter_mapbox(
        dados_agrupados,
        lat="lat_cid_ori",
        lon="long_cid_ori",
        color="intensidade",
        size="total_ocorrencias",  # Aqui está o segredo
        hover_name="cidade_origem",
        hover_data={
            "nome_procedimento": True,
            "total_ocorrencias": True,
            "intensidade": False,
            "lat_cid_ori": False,
            "long_cid_ori": False
        },
        color_continuous_scale=cores_personalizadas,
        range_color=[0, 1],
        zoom=ZOOM_PADRAO,
        size_max=tamanho_maximo,
        height=400
    )

    fig.update_layout(
        mapbox_style="carto-darkmatter",
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox=dict(center=CENTRO_RS, zoom=ZOOM_PADRAO),
        coloraxis_colorbar=dict(
            title="Intensidade",
            tickvals=[0, 1],
            ticktext=["Baixa", "Alta"]
        )
    )

    # Ajuste de zoom se cidade selecionada
    if cidade_selecionada != "Todas":
        cidade_data = dados_agrupados.iloc[0]
        fig.update_layout(
            mapbox_center=dict(
                lat=cidade_data["lat_cid_ori"],
                lon=cidade_data["long_cid_ori"]
            ),
            mapbox_zoom=3
        )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nenhum dado disponível para os filtros selecionados.")

# Métricas resumidas
st.subheader("Resumo Estatístico")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Cidades", len(dados_filtrados["cidade_origem"].unique()))
with col2:
    st.metric("Total de Ocorrências", f"{dados_filtrados['total_ocorrencias'].sum():,}")
with col3:
    st.metric("Procedimentos Selecionados", len(procedimentos_selecionados))

# Dados completos
st.subheader("Dados Detalhados")
st.dataframe(
    dados_filtrados.sort_values("total_ocorrencias", ascending=False),
    column_config={
        "total_ocorrencias": st.column_config.NumberColumn(format="%d"),
        "nome_procedimento": "Procedimento",
        "cidade_origem": "Cidade"
    },
    hide_index=True,
    use_container_width=True,
    height=400
)

# Estilo CSS
st.markdown("""
<style>
    [data-testid="stDataFrame"] {
        width: 100% !important;
    }
    .stMultiSelect [data-baseweb="select"] {
        min-height: 100px;
        max-height: 200px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)
