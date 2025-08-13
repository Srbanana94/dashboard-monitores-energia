import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Monitores de Energia",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("⚡ Dashboard - Acompanhamento de Monitores de Energia")
st.markdown("---")

# Função para carregar dados
def load_data(file_path):
    try:
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            st.success(f"✅ Dados carregados com sucesso! {len(df)} registros encontrados.")
            return df
        else:
            st.warning(f"⚠️ Arquivo {file_path} não encontrado.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Carregar dados
df = load_data('acompanhamento_monitores_energia.xlsx')

if not df.empty:
    # Sidebar com filtros
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por cidade
    cidades = ['Todas'] + list(df['Cidade'].unique())
    cidade_selecionada = st.sidebar.selectbox("Selecione a Cidade:", cidades)
    
    # Filtro por técnico
    tecnicos = ['Todos'] + list(df['Responsável Técnico'].unique())
    tecnico_selecionado = st.sidebar.selectbox("Selecione o Técnico:", tecnicos)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if cidade_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Cidade'] == cidade_selecionada]
    if tecnico_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Responsável Técnico'] == tecnico_selecionado]
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_pops = len(df_filtrado)
    com_monitor = len(df_filtrado[df_filtrado['Monitor de Energia (Sim/Não)'] == 'Sim'])
    sem_monitor = len(df_filtrado[df_filtrado['Monitor de Energia (Sim/Não)'] == 'Não'])
    percentual_com_monitor = (com_monitor / total_pops * 100) if total_pops > 0 else 0
    
    with col1:
        st.metric("Total de POPs", total_pops)
    with col2:
        st.metric("Com Monitor", com_monitor)
    with col3:
        st.metric("Sem Monitor", sem_monitor)
    with col4:
        st.metric("% Com Monitor", f"{percentual_com_monitor:.1f}%")
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribuição por Cidade")
        cidade_counts = df_filtrado.groupby(['Cidade', 'Monitor de Energia (Sim/Não)']).size().unstack(fill_value=0)
        fig_cidade = px.bar(
            cidade_counts, 
            title="Monitores por Cidade",
            color_discrete_map={'Sim': '#2E8B57', 'Não': '#DC143C'}
        )
        fig_cidade.update_layout(height=400)
        st.plotly_chart(fig_cidade, use_container_width=True)
    
    with col2:
        st.subheader("🔧 Distribuição por Técnico")
        tecnico_counts = df_filtrado.groupby(['Responsável Técnico', 'Monitor de Energia (Sim/Não)']).size().unstack(fill_value=0)
        fig_tecnico = px.bar(
            tecnico_counts, 
            title="Monitores por Técnico",
            color_discrete_map={'Sim': '#2E8B57', 'Não': '#DC143C'}
        )
        fig_tecnico.update_layout(height=400)
        st.plotly_chart(fig_tecnico, use_container_width=True)
    
    # Gráfico de pizza
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥧 Status Geral dos Monitores")
        status_counts = df_filtrado['Monitor de Energia (Sim/Não)'].value_counts()
        fig_pizza = px.pie(
            values=status_counts.values, 
            names=status_counts.index,
            title="Distribuição Geral",
            color_discrete_map={'Sim': '#2E8B57', 'Não': '#DC143C'}
        )
        fig_pizza.update_layout(height=400)
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col2:
        st.subheader("📈 Progresso por Técnico")
        progresso_tecnico = df_filtrado.groupby('Responsável Técnico').agg({
            'Monitor de Energia (Sim/Não)': ['count', lambda x: (x == 'Sim').sum()]
        }).round(2)
        progresso_tecnico.columns = ['Total', 'Com Monitor']
        progresso_tecnico['% Completo'] = (progresso_tecnico['Com Monitor'] / progresso_tecnico['Total'] * 100).round(1)
        
        fig_progresso = px.bar(
            x=progresso_tecnico.index,
            y=progresso_tecnico['% Completo'],
            title="Percentual de POPs com Monitor por Técnico",
            color=progresso_tecnico['% Completo'],
            color_continuous_scale='RdYlGn'
        )
        fig_progresso.update_layout(height=400)
        st.plotly_chart(fig_progresso, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela detalhada
    st.subheader("📋 Dados Detalhados")
    
    # Opção para mostrar apenas POPs sem monitor
    mostrar_apenas_sem_monitor = st.checkbox("Mostrar apenas POPs sem monitor")
    
    if mostrar_apenas_sem_monitor:
        df_tabela = df_filtrado[df_filtrado['Monitor de Energia (Sim/Não)'] == 'Não']
    else:
        df_tabela = df_filtrado
    
    # Colorir linhas baseado no status
    def highlight_status(row):
        if row['Monitor de Energia (Sim/Não)'] == 'Sim':
            return ['background-color: #90EE90'] * len(row)
        else:
            return ['background-color: #FFB6C1'] * len(row)
    
    st.dataframe(
        df_tabela.style.apply(highlight_status, axis=1),
        use_container_width=True,
        height=400
    )
    
    # Estatísticas por tipo de monitor
    if 'Tipo de Monitor' in df_filtrado.columns:
        st.markdown("---")
        st.subheader("🔌 Tipos de Monitores Encontrados")
        
        df_com_monitor = df_filtrado[df_filtrado['Monitor de Energia (Sim/Não)'] == 'Sim']
        if not df_com_monitor.empty:
            tipos_monitor = df_com_monitor['Tipo de Monitor'].value_counts()
            if not tipos_monitor.empty:
                fig_tipos = px.bar(
                    x=tipos_monitor.index,
                    y=tipos_monitor.values,
                    title="Distribuição dos Tipos de Monitores",
                    color=tipos_monitor.values,
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_tipos, use_container_width=True)
            else:
                st.info("Nenhum tipo de monitor especificado nos dados.")
        else:
            st.info("Nenhum POP com monitor encontrado nos dados filtrados.")

else:
    st.warning("⚠️ Nenhum dado encontrado. Certifique-se de que o arquivo 'acompanhamento_monitores_energia.xlsx' está no diretório correto.")
    st.info("💡 O dashboard está configurado para carregar dados do arquivo 'acompanhamento_monitores_energia.xlsx'. Quando você preencher a planilha e salvá-la neste diretório, os dados aparecerão automaticamente no dashboard.")

# Rodapé
st.markdown("---")
st.markdown("**Dashboard criado para acompanhamento de monitores de energia em POPs**")
st.markdown(f"*Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*")

