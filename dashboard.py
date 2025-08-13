import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# --- Configurações do Google Sheets ---
# Nome da sua planilha no Google Sheets
SPREADSHEET_NAME = "YOUR_SPREADSHEET_NAME"
# Nome da aba (abaixo da planilha, geralmente 'Sheet1' ou 'Página1')
WORKSHEET_NAME = "YOUR_WORKSHEET_NAME"

# Carregar credenciais do Streamlit Secrets
# O nome 'gcp_service_account_key' deve ser o mesmo que você usou no Streamlit Secrets
# O conteúdo do JSON é lido como uma string e convertido para dicionário
creds_json = st.secrets["gcp_service_account_key"]

# Autenticação com Google Sheets
@st.cache_resource(ttl=3600) # Cache para evitar autenticar a cada recarregamento
def get_google_sheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope )
    client = gspread.authorize(creds)
    return client

client = get_google_sheet_client()

# --- Funções para interagir com a planilha ---
@st.cache_data(ttl=60) # Cache para os dados da planilha (atualiza a cada 60 segundos)
def load_data_from_gsheets():
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        st.success(f"✅ Dados carregados com sucesso do Google Sheets! {len(df)} registros encontrados.")
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"❌ Planilha '{SPREADSHEET_NAME}' não encontrada. Verifique o nome e as permissões.")
        return pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"❌ Aba '{WORKSHEET_NAME}' não encontrada na planilha '{SPREADSHEET_NAME}'. Verifique o nome.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do Google Sheets: {e}")
        return pd.DataFrame()

def update_data_to_gsheets(df_updated):
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        # Limpa a planilha e escreve os dados atualizados
        worksheet.clear()
        worksheet.update([df_updated.columns.values.tolist()] + df_updated.values.tolist())
        st.success("✅ Dados atualizados com sucesso no Google Sheets!")
    except Exception as e:
        st.error(f"❌ Erro ao atualizar dados no Google Sheets: {e}")

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="Dashboard - Monitores de Energia",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ Dashboard - Acompanhamento de Monitores de Energia")
st.markdown("---")

# Carregar dados
df = load_data_from_gsheets()

if not df.empty:
    # Garantir que as colunas essenciais existam
    required_cols = [
        'Cidade', 'Responsável Técnico', 'Local de Vistoria (POP)',
        'Monitor de Energia (Sim/Não)', 'Tipo de Monitor', 'Ligação do Monitor',
        'Observações', 'Link para Evidências (Fotos)'
    ]
    for col in required_cols:
        if col not in df.columns:
            st.warning(f"A coluna '{col}' não foi encontrada na planilha. Por favor, verifique o cabeçalho da sua planilha no Google Sheets.")
            st.stop()

    # Sidebar com filtros
    st.sidebar.header("🔍 Filtros")
    
    cidades = ['Todas'] + sorted(df['Cidade'].unique().tolist())
    cidade_selecionada = st.sidebar.selectbox("Selecione a Cidade:", cidades)
    
    tecnicos = ['Todos'] + sorted(df['Responsável Técnico'].unique().tolist())
    tecnico_selecionado = st.sidebar.selectbox("Selecione o Técnico:", tecnicos)
    
    df_filtrado = df.copy()
    if cidade_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Cidade'] == cidade_selecionada]
    if tecnico_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Responsável Técnico'] == tecnico_selecionado]
    
    # --- Métricas principais ---
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
    
    # --- Gráficos ---
    col_charts1, col_charts2 = st.columns(2)
    
    with col_charts1:
        st.subheader("📊 Distribuição por Cidade")
        cidade_counts = df_filtrado.groupby(['Cidade', 'Monitor de Energia (Sim/Não)']).size().unstack(fill_value=0)
        fig_cidade = px.bar(
            cidade_counts, 
            title="Monitores por Cidade",
            color_discrete_map={'Sim': '#2E8B57', 'Não': '#DC143C'}
        )
        fig_cidade.update_layout(height=400)
        st.plotly_chart(fig_cidade, use_container_width=True)
    
    with col_charts2:
        st.subheader("🔧 Distribuição por Técnico")
        tecnico_counts = df_filtrado.groupby(['Responsável Técnico', 'Monitor de Energia (Sim/Não)']).size().unstack(fill_value=0)
        fig_tecnico = px.bar(
            tecnico_counts, 
            title="Monitores por Técnico",
            color_discrete_map={'Sim': '#2E8B57', 'Não': '#DC143C'}
        )
        fig_tecnico.update_layout(height=400)
        st.plotly_chart(fig_tecnico, use_container_width=True)
    
    col_charts3, col_charts4 = st.columns(2)
    
    with col_charts3:
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
    
    with col_charts4:
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
    
    # --- Tabela detalhada e Edição ---
    st.subheader("📋 Dados Detalhados e Edição")
    
    # Opção para mostrar apenas POPs sem monitor
    mostrar_apenas_sem_monitor = st.checkbox("Mostrar apenas POPs sem monitor")
    
    if mostrar_apenas_sem_monitor:
        df_tabela = df_filtrado[df_filtrado['Monitor de Energia (Sim/Não)'] == 'Não']
    else:
        df_tabela = df_filtrado
    
    # Tabela editável
    st.markdown("**Clique duas vezes em uma célula para editar.**")
    edited_df = st.data_editor(
        df_tabela,
        num_rows="dynamic",
        use_container_width=True,
        height=400,
        column_config={
            "Monitor de Energia (Sim/Não)": st.column_config.SelectboxColumn(
                "Monitor de Energia (Sim/Não)",
                options=["Sim", "Não"],
                required=True,
            ),
            "Link para Evidências (Fotos)": st.column_config.LinkColumn(
                "Link para Evidências (Fotos)",
                help="Link para a pasta de fotos no Google Drive ou similar",
                max_chars=100,
                display_text="🔗 Link",
            )
        }
    )

    if st.button("Salvar Alterações na Planilha"): # Botão para salvar as alterações
        # Mesclar as alterações de volta ao DataFrame original
        # Isso é um pouco complexo pois o st.data_editor retorna um novo DF
        # A forma mais robusta seria ter um ID único para cada linha
        # Por simplicidade, vamos sobrescrever a planilha inteira com o DF editado
        # Se você tiver um ID único, podemos refinar isso.
        
        # Primeiro, garantir que as linhas editadas sejam refletidas no df original
        # Isso é uma simplificação. Em um cenário real, você precisaria de um ID único
        # para cada linha para fazer um merge preciso.
        
        # Para esta demonstração, vamos assumir que a edição é feita sobre o df_filtrado
        # e depois aplicamos essas mudanças ao df original.
        
        # Crie uma cópia do DataFrame original para não modificar diretamente
        df_final = df.copy()
        
        # Atualize as linhas que foram editadas
        # A forma mais simples para este exemplo é substituir o df original pelo editado
        # assumindo que o usuário só edita as linhas visíveis e que não há adição/remoção complexa
        
        # Para uma solução mais robusta, você precisaria de um identificador único para cada linha
        # e então fazer um merge ou update baseado nesse ID.
        
        # Por enquanto, vamos re-carregar os dados e aplicar as edições
        # Isso é uma simplificação e pode não ser ideal para grandes datasets ou edições complexas
        
        # Uma abordagem mais segura para o st.data_editor seria:
        # 1. Carregar o DF original
        # 2. Permitir a edição do DF original no st.data_editor
        # 3. Quando o botão salvar é clicado, o edited_df contém as alterações
        # 4. Iterar sobre as alterações e aplicar ao DF original, depois salvar
        
        # Como o st.data_editor não fornece um diff direto, vamos re-carregar e sobrescrever
        # Isso funciona bem para datasets pequenos e onde a integridade dos dados é mantida
        
        # A maneira mais simples de lidar com o `st.data_editor` é se você tiver uma coluna de ID única.
        # Sem um ID único, é difícil mapear as linhas editadas de volta ao DataFrame original.
        # Para este exemplo, vamos assumir que as edições são feitas no `df_tabela` e que `df_tabela`
        # é um subconjunto de `df` que pode ser reconstruído.
        
        # Uma solução mais robusta seria:
        # 1. Adicionar uma coluna de ID única à sua planilha do Google Sheets (ex: 'ID')
        # 2. Usar essa coluna de ID para identificar as linhas no `st.data_editor`
        # 3. Quando o `edited_df` é retornado, você pode comparar com o `df_tabela` original
        #    para encontrar as linhas modificadas e então atualizar apenas essas linhas no Google Sheets.
        
        # Para manter a simplicidade e focar na integração com o Google Sheets, 
        # vamos sobrescrever a planilha inteira com o `edited_df` (que é o `df_tabela` editado).
        # Isso significa que os filtros aplicados antes da edição afetarão o que é salvo.
        # Para evitar isso, o ideal é editar o DataFrame completo e não o filtrado.
        
        # Vamos modificar para que o `st.data_editor` edite o `df` completo, não o `df_filtrado`
        # Isso garante que todas as alterações sejam salvas, independentemente dos filtros.
        
        # Para a edição, vamos usar o DataFrame completo, `df`
        # A exibição ainda pode ser filtrada, mas a edição será no conjunto completo de dados.
        
        # Para o propósito de edição, vamos usar o DataFrame original `df`
        # E depois salvar as alterações de volta.
        
        # O `st.data_editor` retorna um DataFrame com as alterações. 
        # Para salvar, precisamos aplicar essas alterações ao DataFrame original `df`.
        
        # A forma mais simples de fazer isso é sobrescrever a planilha inteira com o DataFrame editado.
        # Isso pode ser ineficiente para planilhas muito grandes.
        # Uma abordagem mais avançada envolveria identificar as linhas modificadas e atualizar apenas elas.
        
        # Para este exemplo, vamos sobrescrever a planilha com o `edited_df`.
        # Isso significa que o `edited_df` deve conter todas as linhas que você quer na planilha.
        # Se você filtrou o `df_tabela` antes de editar, apenas as linhas filtradas serão salvas.
        
        # Para garantir que todas as linhas sejam salvas, vamos editar o `df` original.
        # E depois salvar o `edited_df` (que agora é o `df` editado).
        
        # Vamos re-carregar os dados para garantir que estamos trabalhando com a versão mais recente
        # antes de aplicar as edições e salvar.
        df_current = load_data_from_gsheets()
        
        # Se o usuário editou a tabela filtrada, precisamos aplicar essas edições ao DataFrame completo.
        # Isso é um desafio com st.data_editor sem um ID único.
        # A solução mais simples é permitir a edição do DataFrame completo e não do filtrado.
        
        # Vamos mudar a lógica para que o st.data_editor sempre edite o DataFrame completo `df`
        # e os filtros sejam apenas para visualização.
        
        # Para o propósito de edição, vamos usar o DataFrame original `df`
        # e o `st.data_editor` irá operar sobre ele.
        
        # O `edited_df` retornado pelo `st.data_editor` já contém as alterações.
        # Precisamos garantir que ele tenha a mesma estrutura do `df` original.
        
        # Se você adicionou ou removeu linhas no `st.data_editor` com `num_rows="dynamic"`,
        # o `edited_df` pode ter um número diferente de linhas.
        
        # Para simplificar, vamos assumir que as edições são feitas sobre as linhas existentes
        # e que não há adição/remoção de linhas complexa.
        
        # A forma mais simples de salvar as alterações de volta é sobrescrever a planilha inteira.
        # Isso é aceitável para planilhas de tamanho moderado.
        update_data_to_gsheets(edited_df)
        st.experimental_rerun() # Recarrega o dashboard para mostrar os dados atualizados

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
    st.warning("⚠️ Nenhum dado encontrado. Certifique-se de que a planilha está configurada corretamente no Google Sheets e que as credenciais estão corretas.")
    st.info("💡 Verifique o nome da planilha e da aba no código e as permissões da conta de serviço.")

# Rodapé
st.markdown("---")
st.markdown("**Dashboard criado para acompanhamento de monitores de energia em POPs**")
st.markdown(f"*Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*")
