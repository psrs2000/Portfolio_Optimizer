import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from optimizer import PortfolioOptimizer
import yfinance as yf
from datetime import datetime, timedelta
from scipy import stats
import requests
import importlib.util
import sys
import os
import tempfile

@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_optimizer_from_private_repo():
    """
    Carrega optimizer.py do repositório privado
    """
    try:
        # Configurações do repositório privado
        GITHUB_USER = "psrs2000"  # Seu usuário
        PRIVATE_REPO = "Portfolio_Optimizer_PVT"  # Nome do repo privado
        GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")  # Token do GitHub
        
        if not GITHUB_TOKEN:
            st.error("❌ Token do GitHub não configurado!")
            st.info("Configure GITHUB_TOKEN nas secrets do Streamlit")
            return None
        
        # URL da API do GitHub para buscar o arquivo
        url = f"https://api.github.com/repos/{GITHUB_USER}/{PRIVATE_REPO}/contents/optimizer.py"
        
        # Headers com autenticação
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3.raw"
        }
        
        # Fazer requisição
        with st.spinner("🔄 Carregando optimizer do repositório privado..."):
            response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Código baixado com sucesso
            optimizer_code = response.text
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(optimizer_code)
                temp_path = temp_file.name
            
            # Importar dinamicamente
            spec = importlib.util.spec_from_file_location("optimizer", temp_path)
            optimizer_module = importlib.util.module_from_spec(spec)
            sys.modules["optimizer"] = optimizer_module
            spec.loader.exec_module(optimizer_module)
            
            # Limpar arquivo temporário
            os.unlink(temp_path)
            
            st.success("✅ Optimizer carregado do repositório privado!")
            return optimizer_module.PortfolioOptimizer
            
        elif response.status_code == 404:
            st.error("❌ Arquivo optimizer.py não encontrado no repositório privado")
            st.info("Verifique se o arquivo existe em Portfolio_Optimizer_PVT/optimizer.py")
            return None
            
        elif response.status_code == 401:
            st.error("❌ Token do GitHub inválido ou sem permissão")
            st.info("Verifique se o token tem acesso ao repositório privado")
            return None
            
        else:
            st.error(f"❌ Erro ao acessar repositório: {response.status_code}")
            st.info(f"Mensagem: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Timeout ao carregar optimizer (>30s)")
        return None
        
    except requests.exceptions.ConnectionError:
        st.error("❌ Erro de conexão com GitHub")
        return None
        
    except Exception as e:
        st.error(f"❌ Erro inesperado: {str(e)}")
        return None

# Tentar carregar o optimizer
PortfolioOptimizer = load_optimizer_from_private_repo()

# Se falhou, parar a execução
if PortfolioOptimizer is None:
    st.markdown("---")
    st.markdown("### 🔧 Configuração necessária:")
    st.markdown("""
    1. **Criar Personal Access Token no GitHub:**
       - Vá em: Settings > Developer settings > Personal access tokens
       - Clique em "Generate new token (classic)"
       - Marque: `repo` (acesso completo aos repositórios)
       
    2. **Configurar token no Streamlit:**
       - No Streamlit Cloud: Settings > Secrets
       - Adicionar linha: `GITHUB_TOKEN = "seu_token_aqui"`
       
    3. **Verificar repositório privado:**
       - Nome: `Portfolio_Optimizer_PVT`
       - Arquivo: `optimizer.py` na raiz
    """)
    st.stop()

# =============================================================================
# FUNÇÕES PARA RANKING DE ATIVOS (NOVO!)
# =============================================================================

def calculate_asset_ranking(df_base_zero, risk_free_column=None):
    """
    Calcula ranking de ativos baseado em 4 parâmetros:
    1. R² (Integral vs Data)
    2. Inclinação (Integral vs Data) 
    3. Desvio Padrão (Diferença)
    4. Correlação (Integral vs Data)
    
    Fórmula: Índice = (Inclinacao_norm × Correlação) / [(1 - R²) × Desvio_norm]
    """
    try:
        # Identificar colunas
        if 'Data' in df_base_zero.columns:
            df_work = df_base_zero.copy()
            dates_col = pd.to_datetime(df_work['Data'])
            
            # Identificar coluna de referência (taxa livre de risco)
            if risk_free_column and risk_free_column in df_work.columns:
                ref_col = risk_free_column
                asset_columns = [col for col in df_work.columns if col not in ['Data', risk_free_column]]
            elif len(df_work.columns) > 2:
                # Assumir segunda coluna como referência se contém palavras-chave
                second_col = df_work.columns[1]
                if any(term in second_col.lower() for term in ['taxa', 'livre', 'risco', 'ibov', 'ref', 'cdi', 'selic']):
                    ref_col = second_col
                    asset_columns = [col for col in df_work.columns if col not in ['Data', second_col]]
                else:
                    st.warning("⚠️ Coluna de referência não detectada. Usando primeira coluna de ativo.")
                    ref_col = df_work.columns[1]
                    asset_columns = df_work.columns[2:].tolist()
            else:
                st.error("❌ Necessário pelo menos 3 colunas: Data, Referência, Ativo")
                return None
        else:
            st.error("❌ Coluna 'Data' não encontrada")
            return None
        
        # ===============================
        # PASSO 1: CRIAR ABA "DIFERENÇA"
        # ===============================
        diferenca_data = {}
        diferenca_data['Data'] = dates_col
        
        for asset in asset_columns:
            # Cada ativo - referência (linha por linha)
            diferenca_data[f"{asset}_diff"] = df_work[asset] - df_work[ref_col]
        
        df_diferenca = pd.DataFrame(diferenca_data)
        
        # ===============================
        # PASSO 2: CRIAR ABA "INTEGRAL" 
        # ===============================
        integral_data = {}
        integral_data['Data'] = dates_col
        
        for asset in asset_columns:
            # Soma acumulada das diferenças
            integral_data[f"{asset}_integral"] = df_diferenca[f"{asset}_diff"].cumsum()
        
        df_integral = pd.DataFrame(integral_data)
        
        # ===============================
        # PASSO 3: CALCULAR 4 PARÂMETROS
        # ===============================
        rankings = []
        all_slopes = []
        all_deviations = []
        
        # Primeira passada: coletar todas as inclinações e desvios para normalização
        for asset in asset_columns:
            try:
                # Dados para regressão (x = índice numérico das datas, y = integral)
                x_data = np.arange(len(df_integral))
                y_data = df_integral[f"{asset}_integral"].values
                
                # Calcular regressão linear
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
                
                # Desvio padrão das diferenças
                std_dev = df_diferenca[f"{asset}_diff"].std()
                
                all_slopes.append(slope)  # Valor absoluto para normalização
                all_deviations.append(std_dev)
                
            except Exception as e:
                print(f"Erro ao calcular parâmetros para {asset}: {e}")
                continue
        
        # Encontrar máximos para normalização
        max_slope = max(all_slopes) if all_slopes else 1
        max_deviation = max(all_deviations) if all_deviations else 1
        
        # Segunda passada: calcular índices com normalização
        for asset in asset_columns:
            try:
                # Dados para regressão
                x_data = np.arange(len(df_integral))
                y_data = df_integral[f"{asset}_integral"].values
                
                # Calcular regressão linear
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
                r_squared = r_value ** 2
                correlation = r_value
                
                # Desvio padrão das diferenças
                std_dev = df_diferenca[f"{asset}_diff"].std()
                
                # NORMALIZAÇÃO
                slope_norm = slope / max_slope if max_slope > 0 else 0
                std_dev_norm = std_dev / max_deviation if max_deviation > 0 else 0
                
                # NOVA FÓRMULA COM PESOS PERSONALIZÁVEIS
                if slope > 0:  # Só eliminar se inclinação for negativa
                    # Garantir que correlação está entre 0 e 1 (valor absoluto)
                    correlation_norm = abs(correlation)
                    
                    # Pegar pesos do session_state (ou usar padrões)
                    p_inc = st.session_state.get('peso_inclinacao', 0.33)
                    p_desv = st.session_state.get('peso_desvio', 0.33)
                    p_cor = st.session_state.get('peso_correlacao', 0.33)
                    
                    # Nova fórmula: [P_inc×Inclinação + P_desv×(1-Desvio) + P_cor×Correlação] / (P_inc+P_desv+P_cor)
                    numerador = (p_inc * slope_norm + 
                               p_desv * (1 - std_dev_norm) + 
                               p_cor * correlation_norm)
                    denominador = p_inc + p_desv + p_cor
                    
                    indice = numerador / denominador if denominador > 0 else 0
                else:
                    indice = 0  # Inclinação negativa = 0
                
                rankings.append({
                    'Ativo': asset,
                    'Inclinação': slope,
                    'Inclinação_Norm': slope_norm,
                    'R²': r_squared,
                    'Correlação': correlation,
                    'Desvio_Padrão': std_dev,
                    'Desvio_Norm': std_dev_norm,
                    'Índice': indice
                })
                
            except Exception as e:
                print(f"Erro ao processar {asset}: {e}")
                rankings.append({
                    'Ativo': asset,
                    'Inclinação': 0,
                    'Inclinação_Norm': 0,
                    'R²': 0,
                    'Correlação': 0,
                    'Desvio_Padrão': 0,
                    'Desvio_Norm': 0,
                    'Índice': 0
                })
        
        # Criar DataFrame e ordenar por índice
        df_ranking = pd.DataFrame(rankings)
        df_ranking = df_ranking.sort_values('Índice', ascending=False).reset_index(drop=True)
        df_ranking['Posição'] = range(1, len(df_ranking) + 1)
        
        return {
            'ranking': df_ranking,
            'diferenca': df_diferenca,
            'integral': df_integral,
            'referencia': ref_col,
            'total_ativos': len(asset_columns)
        }
        
    except Exception as e:
        st.error(f"❌ Erro no cálculo do ranking: {str(e)}")
        return None

def display_ranking_results(ranking_result):
    """
    Exibe os resultados do ranking de forma organizada
    """
    if ranking_result is None:
        return
    
    df_ranking = ranking_result['ranking']
    referencia = ranking_result['referencia']
    total_ativos = ranking_result['total_ativos']
    
    # Cabeçalho
    st.subheader("🏆 Ranking de Ativos")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total de Ativos", total_ativos)
    with col2:
        st.metric("🛡️ Referência", referencia)
    with col3:
        top_asset = df_ranking.iloc[0]['Ativo'] if len(df_ranking) > 0 else "N/A"
        st.metric("🥇 Melhor Ativo", top_asset)
    
    # Tabela principal (Top 10) - RECOLHIDA POR PADRÃO
    with st.expander("📋 Ver Top 10 Ativos", expanded=False):
        # Preparar dados para exibição
        display_df = df_ranking.head(10).copy()
        
        # Formatar colunas para melhor visualização
        display_df['R²'] = display_df['R²'].apply(lambda x: f"{x:.3f}")
        display_df['Correlação'] = display_df['Correlação'].apply(lambda x: f"{x:.3f}")
        display_df['Inclinação_Norm'] = display_df['Inclinação_Norm'].apply(lambda x: f"{x:.3f}")
        display_df['Desvio_Norm'] = display_df['Desvio_Norm'].apply(lambda x: f"{x:.3f}")
        display_df['Índice'] = display_df['Índice'].apply(lambda x: f"{x:.4f}")
        
        # Selecionar colunas para exibição
        columns_to_show = ['Posição', 'Ativo', 'Índice', 'Inclinação_Norm', 'R²', 'Correlação', 'Desvio_Norm']
        
        st.dataframe(
            display_df[columns_to_show], 
            use_container_width=True,
            hide_index=True
        )
    
    # Expandir com tabela completa
    with st.expander(f"📊 Ver ranking completo ({len(df_ranking)} ativos)", expanded=False):
        # Mostrar todas as colunas na versão completa
        full_display_df = df_ranking.copy()
        full_display_df['R²'] = full_display_df['R²'].apply(lambda x: f"{x:.3f}")
        full_display_df['Correlação'] = full_display_df['Correlação'].apply(lambda x: f"{x:.3f}")
        full_display_df['Inclinação_Norm'] = full_display_df['Inclinação_Norm'].apply(lambda x: f"{x:.3f}")
        full_display_df['Desvio_Norm'] = full_display_df['Desvio_Norm'].apply(lambda x: f"{x:.3f}")
        full_display_df['Índice'] = full_display_df['Índice'].apply(lambda x: f"{x:.4f}")
        
        st.dataframe(
            full_display_df[columns_to_show],
            use_container_width=True,
            hide_index=True
        )
    
    return df_ranking

# =============================================================================
# FUNÇÕES PARA INTEGRAÇÃO COM YAHOO FINANCE
# =============================================================================

def buscar_dados_yahoo(simbolos, data_inicio, data_fim, sufixo=".SA"):
    """
    Busca dados do Yahoo Finance (adaptado do seu código)
    ATUALIZADO: Suporte a códigos livres sem sufixo
    """
    dados_historicos = {}
    simbolos_com_erro = []
    
    start_date = data_inicio.strftime('%Y-%m-%d')
    end_date = data_fim.strftime('%Y-%m-%d')
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, simbolo in enumerate(simbolos):
        try:
            status_text.text(f"Buscando {simbolo}... ({i+1}/{len(simbolos)})")
            progress_bar.progress((i + 1) / len(simbolos))
            
            # NOVA LÓGICA: Verificar se é código livre ou precisa de sufixo
            if sufixo == "" or sufixo is None:
                # Códigos livres - usar exatamente como digitado
                simbolo_completo = simbolo
            elif "." in simbolo:
                # Código já tem sufixo - usar como está (para compatibilidade)
                simbolo_completo = simbolo
                st.info(f"🔍 Código {simbolo} já contém sufixo - usando como digitado")
            else:
                # Código tradicional - adicionar sufixo
                simbolo_completo = simbolo + sufixo
            
            ticker = yf.Ticker(simbolo_completo)
            hist = ticker.history(start=start_date, end=end_date, interval="1d")
            
            if not hist.empty and len(hist) > 5:  # Pelo menos 5 dias de dados
                # IMPORTANTE: Salvar com o código ORIGINAL para manter consistência
                dados_historicos[simbolo] = hist
                
                # Debug para códigos livres
                if sufixo == "":
                    st.success(f"✅ {simbolo} → encontrado como {simbolo_completo}")
            else:
                simbolos_com_erro.append(simbolo)
                if sufixo == "":
                    st.warning(f"⚠️ {simbolo} → sem dados suficientes")
                
        except Exception as e:
            simbolos_com_erro.append(simbolo)
            if sufixo == "":
                st.error(f"❌ {simbolo} → erro: {str(e)}")
    
    progress_bar.empty()
    status_text.empty()
    
    return dados_historicos, simbolos_com_erro

def criar_consolidado_yahoo(dados_historicos):
    """
    Cria DataFrame consolidado com preços de fechamento
    """
    if not dados_historicos:
        return None
    
    lista_dfs = []
    
    for simbolo, dados in dados_historicos.items():
        if 'Close' in dados.columns and not dados['Close'].empty:
            df_temp = pd.DataFrame({simbolo: dados['Close']})
            
            # Remove timezone se houver
            if hasattr(df_temp.index, 'tz') and df_temp.index.tz is not None:
                df_temp.index = df_temp.index.tz_localize(None)
            
            lista_dfs.append(df_temp)
    
    if lista_dfs:
        dados_consolidados = pd.concat(lista_dfs, axis=1, sort=True)
        dados_consolidados.index.name = "Data"
        return dados_consolidados
    
    return None

def transformar_base_zero(df_precos):
    """
    Transforma dados de preços para base 0 (adaptado do seu Base_0.py)
    """
    if df_precos is None or df_precos.empty:
        return None, []
    
    df_limpo = df_precos.copy()
    
    # 1. Remove colunas com primeiro valor inválido
    colunas_removidas = []
    for coluna in df_limpo.columns:
        if len(df_limpo[coluna]) == 0:
            colunas_removidas.append(coluna)
            continue
            
        primeiro_valor = df_limpo[coluna].iloc[0]
        if pd.isna(primeiro_valor) or primeiro_valor == 0:
            colunas_removidas.append(coluna)
    
    if colunas_removidas:
        df_limpo = df_limpo.drop(columns=colunas_removidas)
    
    # Verifica se ainda há colunas válidas
    if df_limpo.empty:
        return None, colunas_removidas
    
    # 2. Preenche valores faltantes/zero (CORRIGIDO - sem method='ffill')
    for coluna in df_limpo.columns:
        df_limpo[coluna] = df_limpo[coluna].replace(0, np.nan)
        df_limpo[coluna] = df_limpo[coluna].ffill()  # Novo método
    
    df_limpo = df_limpo.fillna(0)
    
    # 3. Calcula base zero
    df_base_zero = pd.DataFrame(index=df_limpo.index)
    
    for coluna in df_limpo.columns:
        valores = df_limpo[coluna].values
        
        if len(valores) == 0:
            continue
            
        cota_1 = valores[0]  # Primeiro valor como referência
        
        if cota_1 == 0:  # Evita divisão por zero
            continue
        
        novos_valores = np.zeros(len(valores))
        novos_valores[0] = 0.0  # Primeiro valor sempre 0
        
        # Calcula os demais: (Preço_n - Preço_{n-1}) / Preço_1
        for i in range(1, len(valores)):
            cota_n = valores[i]
            cota_anterior = valores[i-1]
            novo_valor = (cota_n - cota_anterior) / cota_1
            novos_valores[i] = novo_valor
        
        df_base_zero[coluna] = novos_valores
    
    return df_base_zero, colunas_removidas

def processar_periodo_selecionado(df_bruto, data_inicio, data_fim, data_analise=None):
    """
    NOVA FUNÇÃO: Processa dados brutos para o período selecionado
    Retorna dados em base 0 para otimização e análise estendida
    """
    try:
        # Verificar se tem coluna de data
        if 'Data' in df_bruto.columns:
            df_trabalho = df_bruto.copy()
            df_trabalho['Data'] = pd.to_datetime(df_trabalho['Data'])
            df_trabalho = df_trabalho.set_index('Data')
        else:
            # Assumir que o índice é a data
            df_trabalho = df_bruto.copy()
            if not isinstance(df_trabalho.index, pd.DatetimeIndex):
                df_trabalho.index = pd.to_datetime(df_trabalho.index)
        
        # Filtrar período para otimização
        df_otimizacao = df_trabalho[(df_trabalho.index >= data_inicio) & 
                                     (df_trabalho.index <= data_fim)].copy()
        
        # Se tem data de análise, pegar período estendido
        df_analise_estendida = None
        if data_analise and data_analise > data_fim:
            df_analise_estendida = df_trabalho[(df_trabalho.index >= data_inicio) & 
                                               (df_trabalho.index <= data_analise)].copy()
        
        # Converter para base 0 - período de otimização
        df_base0_otimizacao, cols_removidas_otim = transformar_base_zero(df_otimizacao)
        
        # Converter para base 0 - período estendido (se aplicável)
        df_base0_analise = None
        if df_analise_estendida is not None:
            df_base0_analise, _ = transformar_base_zero(df_analise_estendida)
        
        # Adicionar coluna de data de volta
        if df_base0_otimizacao is not None:
            df_base0_otimizacao = df_base0_otimizacao.reset_index()
            df_base0_otimizacao.rename(columns={'index': 'Data'}, inplace=True)
        
        if df_base0_analise is not None:
            df_base0_analise = df_base0_analise.reset_index()
            df_base0_analise.rename(columns={'index': 'Data'}, inplace=True)
        
        return df_base0_otimizacao, df_base0_analise, cols_removidas_otim
        
    except Exception as e:
        st.error(f"Erro ao processar período: {str(e)}")
        return None, None, []
    
def create_monthly_returns_table(returns_data, weights, dates=None, risk_free_returns=None):
    """
    Cria tabela de retornos mensais do portfólio otimizado
    MÉTODO CORRIGIDO: Usa metodologia BASE 0 (igual ao otimizador)
    """
    # Calcular retornos diários do portfólio (base 0)
    portfolio_returns_daily = np.dot(returns_data.values, weights)
    
    # Calcular retornos acumulados (base 0) - IGUAL AO OTIMIZADOR
    portfolio_cumulative = np.cumsum(portfolio_returns_daily)
    
    # Usar datas reais se disponíveis, senão simular
    if dates is not None:
        portfolio_df = pd.DataFrame({
            'cumulative': portfolio_cumulative
        }, index=dates)
    else:
        # Simular datas (assumindo dados diários consecutivos)
        start_date = pd.Timestamp('2020-01-01')
        dates = pd.date_range(start=start_date, periods=len(portfolio_cumulative), freq='D')
        portfolio_df = pd.DataFrame({
            'cumulative': portfolio_cumulative
        }, index=dates)
    
    # ========== NOVA METODOLOGIA: BASE 0 MENSAL ==========
    
    # 1. Agrupar por mês e pegar o ÚLTIMO valor de cada mês
    monthly_cumulative = portfolio_df['cumulative'].resample('ME').last()
    
    # 2. Calcular retornos mensais em PERCENTUAIS
    monthly_returns = []
    previous_cumulative = 0  # Começar do zero (base 0)

    for month_date, current_cumulative in monthly_cumulative.items():
        # ✅ NOVO: Retorno percentual do mês
        if previous_cumulative != 0:
            # Crescimento relativo: (novo - antigo) / (1 + antigo)
            monthly_return = (current_cumulative - previous_cumulative) / (1 + previous_cumulative)
        else:
            # Primeiro mês: retorno direto da base 0
            monthly_return = current_cumulative
        
        monthly_returns.append(monthly_return)
        previous_cumulative = current_cumulative
    
    # 3. Criar série com retornos mensais
    monthly_returns_series = pd.Series(monthly_returns, index=monthly_cumulative.index)
    
    # ========== PROCESSAR TAXA LIVRE DE RISCO ==========
    monthly_risk_free = None
    if risk_free_returns is not None:
        # Mesmo processo para taxa livre de risco
        risk_free_cumulative = np.cumsum(risk_free_returns.values)
        
        if dates is not None:
            risk_free_df = pd.DataFrame({
                'cumulative': risk_free_cumulative
            }, index=dates)
        else:
            risk_free_df = pd.DataFrame({
                'cumulative': risk_free_cumulative
            }, index=dates)
        
        # Agrupar por mês
        monthly_rf_cumulative = risk_free_df['cumulative'].resample('ME').last()
        
        # Calcular retornos mensais da taxa livre (base 0)
        monthly_rf_returns = []
        previous_rf_cumulative = 0
        
        for month_date, current_rf_cumulative in monthly_rf_cumulative.items():
            monthly_rf_return = current_rf_cumulative - previous_rf_cumulative
            monthly_rf_returns.append(monthly_rf_return)
            previous_rf_cumulative = current_rf_cumulative
        
        monthly_risk_free = pd.Series(monthly_rf_returns, index=monthly_rf_cumulative.index)
    
    # ========== CRIAR TABELA PIVOTADA ==========
    
    # Criar DataFrame para pivotar
    monthly_df = pd.DataFrame({
        'Year': monthly_returns_series.index.year,
        'Month': monthly_returns_series.index.month,
        'Return': monthly_returns_series.values
    })
    
    # Pivotar para ter anos nas linhas e meses nas colunas
    pivot_table = monthly_df.pivot(index='Year', columns='Month', values='Return')
    
    # Renomear colunas para nomes dos meses
    month_names = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    pivot_table.columns = [month_names.get(col, f'M{col}') for col in pivot_table.columns]
    
    # ========== CALCULAR TOTAL ANUAL CORRIGIDO ==========
    
    # ========== CALCULAR TOTAL ANUAL CORRIGIDO ==========

    # ✅ NOVA METODOLOGIA: Multiplicação composta dos retornos percentuais
    yearly_returns = []
    for year in pivot_table.index:
        year_data = pivot_table.loc[year].dropna()
        if len(year_data) > 0:
            # Para percentuais: multiplicação composta (1+r1)*(1+r2)*...*(1+rn) - 1
            annual_return = 1.0
            for monthly_return in year_data:
                annual_return *= (1 + monthly_return)
            annual_return -= 1  # Subtrair 1 para ter o ganho líquido
            yearly_returns.append(annual_return)
        else:
            yearly_returns.append(np.nan)
    
    pivot_table['Total Anual'] = yearly_returns
    
    # ========== TABELA DE COMPARAÇÃO (SE HÁ TAXA LIVRE) ==========
    
    comparison_table = None
    if monthly_risk_free is not None:
        # Criar tabela similar para taxa livre
        rf_monthly_df = pd.DataFrame({
            'Year': monthly_risk_free.index.year,
            'Month': monthly_risk_free.index.month,
            'Return': monthly_risk_free.values
        })
        
        rf_pivot = rf_monthly_df.pivot(index='Year', columns='Month', values='Return')
        rf_pivot.columns = [month_names.get(col, f'M{col}') for col in rf_pivot.columns]
        
        # Calcular total anual da taxa livre (soma simples - base 0)
        rf_yearly = []
        for year in rf_pivot.index:
            year_data = rf_pivot.loc[year].dropna()
            if len(year_data) > 0:
                annual_return = year_data.sum()  # Soma simples para base 0
                rf_yearly.append(annual_return)
            else:
                rf_yearly.append(np.nan)
        
        rf_pivot['Total Anual'] = rf_yearly
        
        # Criar tabela de comparação (excesso de retorno)
        comparison_table = pivot_table - rf_pivot
    
    return pivot_table, comparison_table

def load_from_github(filename):
    """
    Carrega arquivo Excel diretamente do GitHub
    MODIFICADO: Agora salva dados brutos + processa para base 0 (igual Yahoo)
    """
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/sample_data/{filename}"
    
    try:
        df_bruto = pd.read_excel(url)

        # ✅ NORMALIZAR: Primeira coluna sempre "Data"
        if len(df_bruto.columns) > 0:
            df_bruto.columns.values[0] = "Data"
        
        # SALVAR DADOS BRUTOS - NÃO PROCESSAR AINDA!
        st.session_state['dados_brutos'] = df_bruto.copy()
        st.session_state['fonte_dados'] = f"GitHub: {filename}"
        
        # Identificar período disponível
        if 'Data' in df_bruto.columns or (isinstance(df_bruto.columns[0], str) and 'data' in df_bruto.columns[0].lower()):
            try:
                if 'Data' in df_bruto.columns:
                    datas = pd.to_datetime(df_bruto['Data'])
                else:
                    datas = pd.to_datetime(df_bruto.iloc[:, 0])
                
                st.session_state['periodo_disponivel'] = {
                    'inicio': datas.min(),
                    'fim': datas.max(),
                    'total_dias': len(datas)
                }
            except:
                pass
        
        return True
        
    except Exception as e:
        st.error(f"Erro ao carregar arquivo do GitHub: {str(e)}")
        st.info("Verifique se o arquivo existe e o repositório é público")
        return False

# Configuração da página
st.set_page_config(
    page_title="Otimizador de Portfólio v3.0",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .help-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }
    .stDateInput > div > div > input {
        background-color: #f0f2f6;
    }
    .period-selector {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state para controle da ajuda
if 'show_help' not in st.session_state:
    st.session_state.show_help = False

# Função para alternar ajuda
def toggle_help():
    st.session_state.show_help = not st.session_state.show_help

# Título
st.title("📊 Otimizador de Portfólio v3.0")
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("*Baseado na metodologia de Markowitz - Agora com Janelas Temporais*")
with col2:
    if st.button("📖 Ajuda", use_container_width=True, help="Clique para ver a documentação"):
        toggle_help()

# Mostrar documentação se solicitado
if st.session_state.show_help:
    with st.container():
        st.markdown("---")
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🚀 Início Rápido", "📊 Preparar Dados", "📅 Janelas Temporais", "⚙️ Configurações", "📈 Resultados", "❓ FAQ"])
        
        with tab1:
            st.markdown("""
            ## 🚀 Guia de Início Rápido - v3.0
            
            ### 4 Passos com Janelas Temporais:
            
            1. **📁 Carregue seus dados completos**
               - Use qualquer fonte: Upload, GitHub ou Yahoo
               - Carregue TODO o período disponível (ex: 2015-2025)
            
            2. **📅 Defina as 3 datas críticas**
               - **Início da Otimização**: Onde começar o treino
               - **Fim da Otimização**: Onde terminar o treino
               - **Fim da Análise**: Até onde validar (forward testing)
            
            3. **🎯 Configure e otimize**
               - Selecione os ativos
               - Escolha o objetivo
               - Ajuste os limites
            
            4. **📊 Analise os resultados**
               - Veja performance no período de treino
               - Valide no período estendido
               - Compare in-sample vs out-of-sample
            """)
        
        with tab2:
            st.markdown("""
            ## 📊 Como Preparar seus Dados
            
            ### Formato da Planilha Excel:
            
            | Data | Taxa Ref (opcional) | Ativo 1 | Ativo 2 | ... |
            |------|---------------------|---------|---------|-----|
            | 01/01/2020 | 120.54 | 205.32 |145.65 | ... |
            | 02/01/2020 | 123.67 | 204.21 |139.57 | ... |
            
            ### ⚠️ NOVO em v3.0:
            - **Carregue TODOS os dados disponíveis**
            - **Não se preocupe com o período ainda**
            - **Os dados serão preservados em formato bruto**
            """)
        
        with tab3:
            st.markdown("""
            ## 📅 Sistema de Janelas Temporais (NOVO!)
            
            ### Conceito de 3 Datas:
            
            ```
            |-------- Dados Completos Carregados --------|
                    |--- Otimização ---|--- Validação ---|
                    ↑                 ↑                 ↑
                 Início           Fim              Análise
                Otimização     Otimização          Final
            ```
            
            ### 📊 Vantagens:
            
            1. **Backtesting Realista**
               - Otimize em dados históricos
               - Valide em dados futuros não vistos
            
            2. **Múltiplas Análises**
               - Teste vários períodos sem recarregar
               - Compare diferentes janelas
            """)
        
        with tab4:
            st.markdown("""
            ## ⚙️ Configurações Detalhadas
            
            ### 🎯 Objetivos de Otimização:
            
            | Objetivo | Quando Usar |
            |----------|-------------|
            | **Sharpe Ratio** | Carteiras tradicionais |
            | **Sortino Ratio** | Aversão a perdas |
            | **Minimizar Risco** | Perfil conservador |
            """)
        
        with tab5:
            st.markdown("""
            ## 📈 Interpretando Resultados
            
            ### Métricas Duplas:
            
            **In-Sample**: Performance no treino
            **Out-of-Sample**: Performance na validação
            """)
        
        with tab6:
            st.markdown("""
            ## ❓ FAQ v3.0
            
            ### Como escolher as datas?
            - Otimização: 70% dos dados
            - Validação: 30% dos dados
            """)
        
        # Botão para fechar ajuda
        st.markdown("---")
        if st.button("❌ Fechar Ajuda", use_container_width=False):
            toggle_help()
            st.rerun()

# Configuração dos dados de exemplo no GitHub
GITHUB_USER = "psrs2000"
GITHUB_REPO = "Portfolio_Optimizer"
GITHUB_BRANCH = "main"

# Arquivos de exemplo disponíveis
SAMPLE_DATA = {
    "🏢 Ações Brasileiras": {
        "filename": "acoes_brasileiras.xlsx",
        "description": "Principais ações do Ibovespa"
    },
    "🏠 Fundos Imobiliários": {
        "filename": "fundos_imobiliarios.xlsx",
        "description": "FIIs negociados na B3"
    },
    "💰 Fundos de Investimento": {
        "filename": "fundos_de_investimento.xlsx",
        "description": "Exemplo com fundos de investimento cadastrados na CVM"
    },
    "🌍 ETFs Nacionais": {
        "filename": "etfs_nacionais.xlsx",
        "description": "ETFs de mercados Nacionais"
    },
    "🪙 Criptomoedas": {
        "filename": "criptomoedas.xlsx",
        "description": "Bitcoin, Ethereum e principais"
    }
}

# Sidebar para carregamento de dados
with st.sidebar:
    st.header("📁 Carregar Dados")
    
    # Tabs para organizar opções
    tab_exemplo, tab_upload, tab_yahoo = st.tabs(["📊 Exemplos", "📤 Upload", "🌐 Yahoo Finance"])
    
    with tab_exemplo:
        st.markdown("### Dados de Exemplo")
        
        # Verificar se GitHub está configurado
        if GITHUB_USER == "SEU_USUARIO_GITHUB":
            st.warning(
                "⚠️ Configure o GitHub primeiro!\n\n"
                "1. Edite o arquivo app.py\n"
                "2. Substitua GITHUB_USER e GITHUB_REPO\n"
                "3. Faça upload dos arquivos Excel em /sample_data/"
            )
        else:
            st.info("Clique para carregar:")
            
            # Botões para cada dataset
            for name, info in SAMPLE_DATA.items():
                if st.button(
                    f"{name}",
                    use_container_width=True,
                    help=info['description']
                ):
                    with st.spinner(f"Carregando {name}..."):
                        if load_from_github(info['filename']):
                            st.success("✅ Dados brutos salvos!")
                            st.info("📅 Agora selecione o período na área principal →")
                            st.rerun()
    
    with tab_upload:
        st.markdown("### Upload Manual")
        uploaded_file = st.file_uploader(
            "Escolha sua planilha Excel",
            type=['xlsx', 'xls'],
            help="Planilha com dados históricos dos ativos"
        )
        
        if uploaded_file is not None:
            try:
                # Ler arquivo bruto
                df_bruto = pd.read_excel(uploaded_file)

                # ✅ NORMALIZAR: Primeira coluna sempre "Data"
                if len(df_bruto.columns) > 0:
                    df_bruto.columns.values[0] = "Data"
                
                # SALVAR DADOS BRUTOS - NÃO PROCESSAR!
                st.session_state['dados_brutos'] = df_bruto.copy()
                st.session_state['fonte_dados'] = "Upload Manual"
                
                # Calcular período disponível se tem coluna de data
                if 'Data' in df_bruto.columns or (isinstance(df_bruto.columns[0], str) and 'data' in df_bruto.columns[0].lower()):
                    try:
                        if 'Data' in df_bruto.columns:
                            datas_upload = pd.to_datetime(df_bruto['Data'])
                        else:
                            datas_upload = pd.to_datetime(df_bruto.iloc[:, 0])
                        
                        st.session_state['periodo_disponivel'] = {
                            'inicio': datas_upload.min(),
                            'fim': datas_upload.max(),
                            'total_dias': len(datas_upload)
                        }
                    except:
                        pass
                
                st.success("✅ Dados brutos salvos!")
                st.info("📅 Selecione o período na área principal →")
                #st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {str(e)}")

    with tab_yahoo:
        st.markdown("### 🌐 Buscar Online")
        st.markdown("Busque dados diretamente do Yahoo Finance")
        
        # Configuração de símbolos
        st.markdown("**📝 Símbolos dos Ativos:**")
        simbolos_input = st.text_area(
            "Digite os códigos (um por linha):",
            value="PETR4\nVALE3\nITUB4\nBBDC4\nABEV3",
            height=120,
            help="Digite os códigos dos ativos, um por linha. Ex: PETR4, VALE3, etc."
        )
        
        # NOVO: Ativo de Referência
        st.markdown("**🏛️ Ativo de Referência (Taxa Livre de Risco):**")
        
        col_ref1, col_ref2 = st.columns([3, 1])
        
        with col_ref1:
            ativo_referencia = st.text_input(
                "Código do ativo de referência:",
                value="BOVA11",
                help="Ex: BOVA11 (Ibovespa), LFTS11 (CDI), IVV (S&P500)"
            )
        
        with col_ref2:
            usar_referencia = st.checkbox(
                "Incluir",
                value=True,
                help="Marque para incluir ativo de referência"
            )
        
        # Sugestões rápidas
        st.markdown("💡 **Sugestões:** BOVA11 (Ibovespa), LFTS11 (CDI), SMAL11 (Small Caps)")
        
        # Tipo de ativo - ATUALIZADO COM CÓDIGOS LIVRES
        tipos_disponiveis = [
            ("Ações Brasileiras", ".SA"),
            ("Criptomoedas", ""),
            ("Ações Americanas", ""),
            ("ETFs Americanos", ""),
            ("Códigos Livres do Yahoo", "LIVRE")
        ]
        
        tipo_ativo = st.selectbox(
            "🏷️ Tipo de Ativo:",
            tipos_disponiveis,
            format_func=lambda x: x[0],
            index=0
        )
        sufixo = tipo_ativo[1]
        
        # NOVA SEÇÃO: Instrução condicional para códigos livres
        if sufixo == "LIVRE":
            st.info(
                "🔥 **Modo Códigos Livres Ativado!**\n\n"
                "• Digite os códigos **exatamente** como aparecem no Yahoo Finance\n"
                "• Exemplos: `PETR4.SA`, `MSFT`, `BTC-USD`\n"
                "• Não será adicionado nenhum sufixo automático"
            )
        
        # Período
        st.markdown("**📅 Período:**")
        col1, col2 = st.columns(2)
        
        with col1:
            data_inicio = st.date_input(
                "Data Início:",
                value=datetime.now() - timedelta(days=365*3),
                max_value=datetime.now().date()
            )
        
        with col2:
            data_fim = st.date_input(
                "Data Fim:",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
        
        # Botão para buscar
        if st.button("🚀 Buscar e Processar", use_container_width=True, type="primary"):
            # Validações
            simbolos_lista = [s.strip().upper() for s in simbolos_input.split('\n') if s.strip()]
            
            if len(simbolos_lista) < 2:
                st.error("❌ Digite pelo menos 2 símbolos")
            elif data_inicio >= data_fim:
                st.error("❌ Data de início deve ser anterior à data fim")
            else:
                # NOVA LÓGICA: Códigos livres vs sufixo automático
                simbolos_completos = simbolos_lista.copy()
                
                if usar_referencia and ativo_referencia.strip():
                    ativo_ref_clean = ativo_referencia.strip().upper()
                    if ativo_ref_clean not in simbolos_completos:
                        simbolos_completos.append(ativo_ref_clean)
                        st.info(f"📊 Ativo de referência adicionado: {ativo_ref_clean}")
                
                with st.spinner("🔄 Buscando dados do Yahoo Finance..."):
                    # MODIFICAÇÃO PRINCIPAL: Condicional do sufixo
                    if sufixo == "LIVRE":
                        # Modo códigos livres - não adiciona sufixo
                        dados_yahoo, erros = buscar_dados_yahoo(
                            simbolos_completos, 
                            datetime.combine(data_inicio, datetime.min.time()),
                            datetime.combine(data_fim, datetime.min.time()),
                            sufixo=""  # ← Sem sufixo
                        )
                        st.info("🔥 Modo códigos livres: buscando códigos como digitados")
                    else:
                        # Modo tradicional - adiciona sufixo
                        dados_yahoo, erros = buscar_dados_yahoo(
                            simbolos_completos, 
                            datetime.combine(data_inicio, datetime.min.time()),
                            datetime.combine(data_fim, datetime.min.time()),
                            sufixo
                        )
                    
                    if dados_yahoo:
                        st.success(f"✅ Dados obtidos para {len(dados_yahoo)} ativos")
                        
                        if erros:
                            st.warning(f"⚠️ Erros em: {', '.join(erros)}")
                        
                        # 2. Consolidar PREÇOS BRUTOS
                        with st.spinner("🔄 Consolidando preços..."):
                            df_precos_brutos = criar_consolidado_yahoo(dados_yahoo)
                        
                        if df_precos_brutos is not None:
                            st.success(f"✅ Preços consolidados: {df_precos_brutos.shape}")
                            
                            # Preparar DataFrame com Data
                            df_precos_com_data = df_precos_brutos.copy()
                            df_precos_com_data = df_precos_com_data.reset_index()  # Data vira primeira coluna
                            
                            # REORGANIZAR ATIVO DE REFERÊNCIA se necessário
                            if usar_referencia and ativo_referencia.strip():
                                ativo_ref_clean = ativo_referencia.strip().upper()
                                
                                if ativo_ref_clean in df_precos_com_data.columns:
                                    # Renomear para que o otimizador detecte
                                    nome_referencia = f"Taxa_Ref_{ativo_ref_clean}"
                                    
                                    # Reorganizar: Data, Taxa_Ref, Outros_Ativos
                                    colunas_reorganizadas = ['Data']
                                    outras_colunas = [col for col in df_precos_com_data.columns 
                                                    if col not in ['Data', ativo_ref_clean]]
                                    
                                    # Renomear a coluna do ativo de referência
                                    df_precos_com_data = df_precos_com_data.rename(columns={ativo_ref_clean: nome_referencia})
                                    
                                    # Reorganizar colunas: Data, Taxa_Ref, Outros
                                    colunas_reorganizadas.append(nome_referencia)
                                    colunas_reorganizadas.extend(outras_colunas)
                                    
                                    df_precos_com_data = df_precos_com_data[colunas_reorganizadas]
                                    
                                    st.info(f"🏛️ Ativo de referência renomeado para: {nome_referencia}")
                            
                            # SALVAR DADOS BRUTOS (PERPÉTUA)
                            st.session_state['dados_brutos'] = df_precos_com_data
                            st.session_state['fonte_dados'] = f"Yahoo Finance ({len(dados_yahoo)} ativos)"
                            st.session_state['periodo_disponivel'] = {
                                'inicio': df_precos_com_data['Data'].min(),
                                'fim': df_precos_com_data['Data'].max(),
                                'total_dias': len(df_precos_com_data)
                            }
                            
                            st.success("🎉 Dados brutos salvos!")
                            st.info("📅 Agora selecione o período na área principal →")
                            st.rerun()
                            
                        else:
                            st.error("❌ Erro ao consolidar dados")
                    else:
                        st.error("❌ Nenhum dado encontrado. Verifique os símbolos.")
                        
# ÁREA PRINCIPAL - NOVO FLUXO COM JANELAS TEMPORAIS
# Verificar se há dados brutos carregados
dados_brutos = st.session_state.get('dados_brutos', None)

if dados_brutos is not None:
    # Mostrar origem dos dados
    fonte = st.session_state.get('fonte_dados', 'Desconhecida')
    periodo_disp = st.session_state.get('periodo_disponivel', None)
    
    # Header com informações
    col_info1, col_info2, col_download, col_clear = st.columns([3, 3, 1, 1])
    
    with col_info1:
        st.success(f"✅ **Dados Carregados:** {fonte}")
    
    with col_info2:
        if periodo_disp:
            st.info(f"📅 **Período Disponível:** {periodo_disp['inicio'].strftime('%d/%m/%Y')} a {periodo_disp['fim'].strftime('%d/%m/%Y')} ({periodo_disp['total_dias']} dias)")
    
    with col_download:
        # Função para converter DataFrame para Excel
        def convert_to_excel(df):
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Adicionar planilha principal com dados
                df.to_excel(writer, index=False, sheet_name='Dados')
                
                # Adicionar planilha com metadados
                metadata = pd.DataFrame({
                    'Informação': ['Fonte dos Dados', 'Data do Download', 'Período Início', 'Período Fim', 'Total de Dias', 'Total de Ativos'],
                    'Valor': [
                        fonte,
                        datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                        periodo_disp['inicio'].strftime('%d/%m/%Y') if periodo_disp else 'N/A',
                        periodo_disp['fim'].strftime('%d/%m/%Y') if periodo_disp else 'N/A',
                        str(periodo_disp['total_dias']) if periodo_disp else 'N/A',
                        str(len(df.columns) - 1)  # -1 para excluir coluna Data
                    ]
                })
                metadata.to_excel(writer, index=False, sheet_name='Metadados')
                
                # Adicionar planilha com instruções
                instrucoes = pd.DataFrame({
                    'Como usar este arquivo': [
                        '1. Este arquivo contém dados históricos de ativos financeiros',
                        '2. A primeira coluna deve sempre ser "Data"',
                        '3. A segunda coluna pode ser uma taxa de referência (opcional)',
                        '4. As demais colunas são os ativos para análise',
                        '5. Use este arquivo como template para seus próprios dados',
                        '6. Faça upload deste arquivo no Otimizador de Portfólio',
                        '',
                        'Estrutura esperada:',
                        'Data | Taxa_Ref | Ativo1 | Ativo2 | Ativo3 | ...',
                        '',
                        'Dica: A taxa de referência é detectada automaticamente',
                        'se contiver as palavras: taxa, livre, risco, ref, cdi, selic'
                    ]
                })
                instrucoes.to_excel(writer, index=False, sheet_name='Instruções')
                
            return output.getvalue()
        
        try:
            excel_data = convert_to_excel(dados_brutos)
            
            # Nome do arquivo com timestamp
            filename = f"portfolio_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            
            st.download_button(
                label="💾 Baixar",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Baixar dados para uso posterior",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro ao preparar download: {str(e)}")
    
    with col_clear:
        if st.button("🔄 Limpar", use_container_width=True, help="Limpar todos os dados carregados"):
            for key in ['dados_brutos', 'fonte_dados', 'periodo_disponivel', 'df', 'df_analise']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # NOVA SEÇÃO: SELEÇÃO DE JANELAS TEMPORAIS
    st.header("📅 Definir Janelas Temporais")
    
    # Container estilizado para seleção de datas (com sliders)
    with st.container():
        st.markdown('<div class="period-selector">', unsafe_allow_html=True)
        
        st.markdown("🎯 **Configure as 3 datas críticas para análise:**")
        
        if periodo_disp:
            total_dias = (periodo_disp['fim'] - periodo_disp['inicio']).days
            dias_otimizacao = int(total_dias * 0.7)
            
            default_inicio = periodo_disp['inicio'].date()
            default_fim_otim = (periodo_disp['inicio'] + timedelta(days=dias_otimizacao)).date()
            default_fim_analise = periodo_disp['fim'].date()
        else:
            default_inicio = datetime(2020, 1, 1).date()
            default_fim_otim = datetime(2022, 12, 31).date()
            default_fim_analise = datetime(2024, 12, 31).date()

        # Slider de intervalo para período de otimização
        data_inicio_otim, data_fim_otim = st.slider(
            "📅 Selecione o período de **Otimização (Treinamento)**",
            min_value=default_inicio,
            max_value=default_fim_analise,
            value=(default_inicio, default_fim_otim),
            format="DD/MM/YYYY",
            help="Arraste as extremidades para escolher o intervalo de treino"
        )
        
        # Slider para Fim da Análise (validação)
        usar_validacao = st.checkbox("Usar validação (forward test)?", value=True)
        
        if usar_validacao:
            data_fim_analise = st.slider(
                "📊 Selecione o **Fim da Análise (Validação)**",
                min_value=data_fim_otim,
                max_value=default_fim_analise,
                value=default_fim_analise,
                format="DD/MM/YYYY",
                help="Define até onde você deseja validar os resultados"
            )
        else:
            data_fim_analise = None
        
        st.markdown('</div>', unsafe_allow_html=True)        
        # Visualização das janelas selecionadas
        if data_fim_analise:
            dias_otim = (data_fim_otim - data_inicio_otim).days
            dias_valid = (data_fim_analise - data_fim_otim).days
            dias_total = dias_otim + dias_valid
            
            col_viz1, col_viz2, col_viz3 = st.columns(3)
            
            with col_viz1:
                st.metric("📊 Dias para Otimização", f"{dias_otim}", f"{(dias_otim/dias_total*100):.0f}% do total")
            
            with col_viz2:
                st.metric("🔍 Dias para Validação", f"{dias_valid}", f"{(dias_valid/dias_total*100):.0f}% do total")
            
            with col_viz3:
                st.metric("📈 Total de Dias", f"{dias_total}", f"{(dias_total/periodo_disp['total_dias']*100):.0f}% disponível" if periodo_disp else "")
        else:
            dias_otim = (data_fim_otim - data_inicio_otim).days
            st.metric("📊 Dias para Otimização", f"{dias_otim}")
        
        # Botão para processar período
        if st.button("⚡ Processar Período Selecionado", use_container_width=True, type="primary"):
            with st.spinner("🔄 Processando dados para o período selecionado..."):
                
                # Converter datas para datetime
                inicio_dt = pd.Timestamp(data_inicio_otim)
                fim_dt = pd.Timestamp(data_fim_otim)
                analise_dt = pd.Timestamp(data_fim_analise) if data_fim_analise else None
                
                # Processar dados para os períodos selecionados
                df_otimizacao, df_analise_estendida, cols_removidas = processar_periodo_selecionado(
                    dados_brutos,
                    inicio_dt,
                    fim_dt,
                    analise_dt
                )
                
                if df_otimizacao is not None:
                    # Salvar no session_state
                    st.session_state['df'] = df_otimizacao
                    st.session_state['df_analise'] = df_analise_estendida
                    st.session_state['periodo_otimizacao'] = {
                        'inicio': inicio_dt,
                        'fim': fim_dt
                    }
                    st.session_state['periodo_analise'] = {
                        'inicio': inicio_dt,
                        'fim': analise_dt if analise_dt else fim_dt
                    }
                    
                    st.success("✅ Período processado com sucesso!")
                    
                    if cols_removidas:
                        st.warning(f"⚠️ Colunas removidas (sem dados válidos): {', '.join(cols_removidas)}")
                    
                    st.info(f"📊 {len(df_otimizacao.columns)-1} ativos prontos para otimização")
                    
                    if df_analise_estendida is not None:
                        st.info(f"🔍 Período de validação configurado: {(analise_dt - fim_dt).days} dias adicionais")
                else:
                    st.error("❌ Erro ao processar período selecionado")
    
    # Mostrar dados processados se existirem
    df = st.session_state.get('df', None)
    df_analise = st.session_state.get('df_analise', None)
    
    if df is not None:

        # NOVA SEÇÃO: RANKING DE ATIVOS (FASE 1)
        #st.header("🏆 Ranking de Ativos (NOVO!)")
        
        # Checkbox para ativar ranking
        use_ranking = st.checkbox(
            "🤖 Ativar ranking automático de ativos",
            help="Calcula índice de qualidade para cada ativo baseado em 4 parâmetros"
        )
        
        ranking_result = None
        
        if use_ranking:
            with st.spinner("🧮 Calculando ranking dos ativos..."):
                # Calcular ranking baseado nos dados de otimização
                ranking_result = calculate_asset_ranking(df)
                
                if ranking_result is not None:
                    # Exibir resultados
                    top_assets_df = display_ranking_results(ranking_result)
                    
                    # Salvar no session_state para uso posterior
                    st.session_state['ranking_result'] = ranking_result
                    
                    st.success("✅ Ranking calculado com sucesso!")

                    # NOVA SEÇÃO: Configuração de pesos
                    with st.expander("⚙️ Configurar pesos dos parâmetros", expanded=False):
                        st.markdown("**Personalize a importância de cada fator no ranking:**")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            p_inc = st.slider(
                                "📈 Peso Inclinação", 
                                min_value=0.0, 
                                max_value=1.0, 
                                value=st.session_state.get('peso_inclinacao', 0.33),
                                step=0.05,
                                help="Importância do crescimento/tendência"
                            )
                        
                        with col2:
                            p_desv = st.slider(
                                "📊 Peso Desvio Padrão", 
                                min_value=0.0, 
                                max_value=1.0, 
                                value=st.session_state.get('peso_desvio', 0.33),
                                step=0.05,
                                help="Importância da baixa volatilidade"
                            )
                        
                        with col3:
                            p_cor = st.slider(
                                "🎯 Peso Correlação", 
                                min_value=0.0, 
                                max_value=1.0, 
                                value=st.session_state.get('peso_correlacao', 0.33),
                                step=0.05,
                                help="Importância da consistência linear"
                            )
                        
                        # Atualizar session_state
                        st.session_state['peso_inclinacao'] = p_inc
                        st.session_state['peso_desvio'] = p_desv
                        st.session_state['peso_correlacao'] = p_cor
                        
                        # Mostrar soma dos pesos
                        total_pesos = p_inc + p_desv + p_cor
                        if total_pesos > 0:
                            st.info(f"💡 **Distribuição:** Inclinação {p_inc/total_pesos*100:.0f}% | Estabilidade {p_desv/total_pesos*100:.0f}% | Correlação {p_cor/total_pesos*100:.0f}%")
                        
                        # Botão para recalcular
                        if st.button("🔄 Recalcular Ranking", help="Aplicar novos pesos ao ranking"):
                            st.rerun()

# NOVA FUNCIONALIDADE: Seleção automática
                    st.markdown("---")
                    st.subheader("🎯 Seleção Automática de Ativos")
                    
                    col1, col2, col3 = st.columns([1.5, 1.5, 1])

                    with col1:
                        score_min = st.number_input(
                            "📉 Score mínimo:",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.7,
                            step=0.05,
                            help="Score mínimo para seleção (0 a 1)"
                        )

                    with col2:
                        score_max = st.number_input(
                            "📈 Score máximo:",
                            min_value=0.0,
                            max_value=1.0,
                            value=1.0,
                            step=0.05,
                            help="Score máximo para seleção (0 a 1)"
                        )

                    with col3:
                        st.markdown("<br>", unsafe_allow_html=True)  # Espaço para alinhar com os inputs
                        auto_select_btn = st.button(
                            "✅ Selecionar Top Ativos", 
                            type="primary",
                            use_container_width=True,
                            help="Aplica seleção automática baseada no ranking"
                        )
                    
                    # Processar seleção automática
                    if auto_select_btn:
                        # Validar range
                        if score_min > score_max:
                            st.error("❌ Score mínimo deve ser menor que o máximo!")
                        else:
                            # Filtrar ativos por range de score
                            filtered_ranking = ranking_result['ranking'][
                                (ranking_result['ranking']['Índice'] >= score_min) & 
                                (ranking_result['ranking']['Índice'] <= score_max)
                            ]
                            top_assets = filtered_ranking['Ativo'].tolist()
                            
                            if len(top_assets) == 0:
                                st.warning(f"⚠️ Nenhum ativo encontrado no range {score_min:.2f} - {score_max:.2f}")
                                top_assets = []
                        
                        # Salvar seleção automática no session_state
                        st.session_state['selected_assets_auto'] = top_assets
                        st.session_state['auto_selection_active'] = True
                        st.session_state['score_range_selected'] = (score_min, score_max)
                        
                        if len(top_assets) > 0:
                            st.success(f"🎉 {len(top_assets)} ativos selecionados no range {score_min:.2f} - {score_max:.2f}!")
                            
                            # Mostrar estatísticas do range
                            if len(filtered_ranking) > 0:
                                avg_score = filtered_ranking['Índice'].mean()
                                st.info(f"📊 Score médio dos selecionados: {avg_score:.3f}")
                        
                        # Mostrar lista dos ativos selecionados
                        with st.expander("👀 Ver ativos selecionados", expanded=False):
                            selected_df = filtered_ranking[['Posição', 'Ativo', 'Índice']].copy()
                            selected_df['Índice'] = selected_df['Índice'].apply(lambda x: f"{x:.4f}")
                            st.dataframe(selected_df, use_container_width=True, hide_index=True)
                        
                        st.info("👇 Agora vá para a seção de otimização abaixo!")

                else:
                    st.error("❌ Erro ao calcular ranking")
        # Tabs para visualizar dados
        tab_otim, tab_valid = st.tabs(["📊 Dados de Otimização", "🔍 Dados de Validação"])
        
        with tab_otim:
            with st.expander("Ver dados processados para otimização", expanded=False):
                st.write(f"**Dimensões:** {df.shape[0]} linhas x {df.shape[1]} colunas")
                st.write(f"**Período:** {st.session_state['periodo_otimizacao']['inicio'].strftime('%d/%m/%Y')} a {st.session_state['periodo_otimizacao']['fim'].strftime('%d/%m/%Y')}")
                st.dataframe(df.head(10))
        
        with tab_valid:
            if df_analise is not None:
                with st.expander("Ver dados estendidos para validação", expanded=False):
                    st.write(f"**Dimensões:** {df_analise.shape[0]} linhas x {df_analise.shape[1]} colunas")
                    st.write(f"**Período:** {st.session_state['periodo_analise']['inicio'].strftime('%d/%m/%Y')} a {st.session_state['periodo_analise']['fim'].strftime('%d/%m/%Y')}")
                    st.dataframe(df_analise.tail(10))
            else:
                st.info("📍 Nenhum período de validação configurado")
        
        # Verificar taxa de referência
        has_risk_free = False
        risk_free_column_name = None
        if len(df.columns) > 2 and isinstance(df.columns[1], str):
            col_name = df.columns[1].lower()
            if any(term in col_name for term in ['taxa', 'livre', 'risco', 'ibov', 'ref', 'cdi', 'selic']):
                has_risk_free = True
                risk_free_column_name = df.columns[1]
                st.info(f"📊 Taxa de referência detectada: '{risk_free_column_name}'")
        
        # SEÇÃO DE OTIMIZAÇÃO
        st.header("🛒 Seleção de Ativos")
        
        # Identificar colunas de ativos
        if isinstance(df.columns[0], str) and 'data' in df.columns[0].lower():
            if has_risk_free:
                asset_columns = df.columns[2:].tolist()
            else:
                asset_columns = df.columns[1:].tolist()
        else:
            asset_columns = df.columns.tolist()
        
        # Verificar se há seleção automática ativa
        auto_selection_active = st.session_state.get('auto_selection_active', False)
        selected_assets_auto = st.session_state.get('selected_assets_auto', [])
        
        if auto_selection_active and selected_assets_auto:
            # MODO AUTOMÁTICO: Aparecer como se fosse seleção manual normal
            selected_assets = st.multiselect(
                "🎯 Selecione os ativos para otimização:",
                options=asset_columns,
                default=selected_assets_auto,  # ← Usar os ativos do ranking como padrão
                help="Mínimo 2 ativos (selecionados automaticamente pelo ranking)",
                placeholder="Ativos selecionados pelo ranking..."
            )
            
            # Botão discreto para resetar
            if st.button("🔄 Resetar seleção automática", help="Voltar ao modo manual normal"):
                st.session_state['auto_selection_active'] = False
                st.session_state['selected_assets_auto'] = []
                st.rerun()
            
        else:
            # MODO MANUAL: Seleção tradicional
            selected_assets = st.multiselect(
                "🎯 Selecione os ativos para otimização:",
                options=asset_columns,
                default=asset_columns[:min(250, len(asset_columns))],
                help="Mínimo 2 ativos",
                placeholder="Escolha os ativos..."
            )
        
        if len(selected_assets) < 2:
            st.warning("⚠️ Selecione pelo menos 2 ativos para otimização")
        else:
            mode_text = "automática" if auto_selection_active else "manual"
            st.success(f"✅ {len(selected_assets)} ativos selecionados ({mode_text})")
        
        # NOVA SEÇÃO: Short Selling / Hedge
        st.header("🔄 Posições Short / Hedge (Opcional)")
        
        use_short = st.checkbox("Habilitar posições short/hedge", help="Permite incluir ativos com pesos negativos (venda a descoberto)")
        
        short_assets = []
        short_weights = {}
        
        if use_short:
            # Identificar ativos não selecionados
            available_for_short = [asset for asset in asset_columns if asset not in selected_assets]
            
            if len(available_for_short) > 0:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    short_assets = st.multiselect(
                        "Selecione ativos para posição short:",
                        options=available_for_short,
                        help="Estes ativos terão pesos negativos (venda a descoberto)"
                    )
                
                if len(short_assets) > 0:
                    st.markdown("**Defina os pesos negativos:**")
                    
                    # Criar sliders para cada ativo short
                    cols = st.columns(min(3, len(short_assets)))
                    for idx, asset in enumerate(short_assets):
                        with cols[idx % 3]:
                            weight = st.slider(
                                f"{asset}",
                                min_value=-100,
                                max_value=0,
                                value=-100,
                                step=1,
                                help=f"Peso negativo para {asset} (%). -100% = venda total do ativo"
                            )
                            short_weights[asset] = weight / 100
                    
                    # Mostrar resumo
                    total_short = sum(short_weights.values())
                    st.info(f"📊 Total short: {total_short*100:.1f}% (não entra na soma dos 100% do portfólio)")
            else:
                st.warning("⚠️ Selecione menos ativos na otimização para liberar opções de short")
        
        # Configurações de otimização
        st.header("⚙️ Configurações da Otimização")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Lista de objetivos com condicional
            objectives_list = [
                "Maximizar Sharpe Ratio", 
                "Maximizar Sortino Ratio",
                "Minimizar Risco", 
                "Maximizar Inclinação", 
                "Maximizar Inclinação/[(1-R²)×Vol]"
            ]
            
            # Adicionar objetivo de excesso apenas se taxa livre foi detectada
            if has_risk_free:
                objectives_list.append("Maximizar Qualidade da Linearidade")
                objectives_list.append("Maximizar Linearidade do Excesso")
                
            objective = st.selectbox(
                "🎯 Objetivo da Otimização",
                objectives_list,
                help="Escolha o que você quer otimizar"
            )
        
        with col2:
            min_weight = st.slider(
                "📊 Peso mínimo por ativo (%)",
                min_value=0,
                max_value=20,
                value=0,
                step=1,
                help="Limite mínimo para cada ativo no portfólio (0% = sem mínimo)"
            ) / 100
        
        with col3:
            max_weight = st.slider(
                "📊 Peso máximo por ativo (%)",
                min_value=5,
                max_value=100,
                value=30,
                step=1,
                help="Limite máximo para cada ativo no portfólio"
            ) / 100
        
        with col4:
            # Inicializar otimizador para verificar taxa livre
            temp_optimizer = PortfolioOptimizer(df, [])
            
            if has_risk_free and hasattr(temp_optimizer, 'risk_free_rate_total'):
                # Mostrar taxa livre detectada como informação
                detected_rate = temp_optimizer.risk_free_rate_total
                st.metric(
                    "🏛️ Taxa de referência",
                    f"{detected_rate:.2%}",
                    help="Taxa detectada automaticamente da coluna B (acumulada do período)"
                )
                used_risk_free_rate = detected_rate
            else:
                # Campo manual se não detectou
                used_risk_free_rate = st.number_input(
                    "🏛️ Taxa de referência (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=0.1,
                    help="Taxa de referência ACUMULADA do período"
                ) / 100

# NOVA SEÇÃO: Restrições Individuais
        use_individual_constraints = False
        individual_constraints = {}
        
        if len(selected_assets) >= 2:
            st.header("🚫 Restrições Individuais por Ativo (Opcional)")
            
            use_individual_constraints = st.checkbox(
                "Definir limites específicos para alguns ativos",
                help="Permite definir pesos mínimos e máximos diferentes para ativos específicos"
            )
            
            if use_individual_constraints:
                # Selecionar quais ativos terão restrições individuais
                constrained_assets = st.multiselect(
                    "Selecione os ativos com restrições específicas:",
                    options=selected_assets,
                    help="Escolha apenas os ativos que precisam de limites diferentes dos globais"
                )
                
                if len(constrained_assets) > 0:
                    st.markdown("**Configure os limites para cada ativo selecionado:**")
                    
                    # Criar colunas para organizar melhor
                    num_cols = min(2, len(constrained_assets))
                    if num_cols > 0:
                        cols = st.columns(num_cols)
                    
                    for idx, asset in enumerate(constrained_assets):
                        with cols[idx % num_cols] if num_cols > 0 else st.container():
                            st.markdown(f"**{asset}**")
                            
                            # Valores padrão baseados nos limites globais
                            default_min = min_weight * 100
                            default_max = max_weight * 100
                            
                            # Criar duas colunas para min e max lado a lado
                            col_min, col_max = st.columns(2)
                            
                            with col_min:
                                asset_min = st.number_input(
                                    "Mín %",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=default_min,
                                    step=0.5,
                                    key=f"min_{asset}",
                                    help=f"Peso mínimo para {asset}"
                                )
                            
                            with col_max:
                                asset_max = st.number_input(
                                    "Máx %",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=default_max,
                                    step=0.5,
                                    key=f"max_{asset}",
                                    help=f"Peso máximo para {asset}"
                                )
                            
                            # Validar que min <= max
                            if asset_min > asset_max:
                                st.error(f"⚠️ Mínimo deve ser ≤ Máximo")
                                asset_min = asset_max
                            
                            # Guardar apenas os ativos com restrições
                            individual_constraints[asset] = {
                                'min': asset_min / 100,
                                'max': asset_max / 100
                            }
                            
                            # Mostrar range visualmente
                            if asset_min == asset_max:
                                st.info(f"🔒 Travado em {asset_min:.1f}%")
                            else:
                                st.caption(f"📊 Range: {asset_min:.1f}% - {asset_max:.1f}%")
                            st.markdown("---")
                    
                    # Validar se a soma dos mínimos não excede 100%
                    total_min = 0
                    for asset in selected_assets:
                        if asset in individual_constraints:
                            total_min += individual_constraints[asset]['min']
                        else:
                            total_min += min_weight
                    
                    if total_min > 1.0:
                        st.error(f"❌ Soma dos mínimos ({total_min*100:.1f}%) excede 100%!")
                        st.caption("Isso inclui os ativos sem restrições individuais usando o mínimo global")
                    else:
                        st.success(f"✅ Soma total dos mínimos: {total_min*100:.1f}%")
                else:
                    st.info("👆 Selecione os ativos que precisam de limites específicos")
        
        # Botão de otimização
        if st.button("🚀 OTIMIZAR PORTFÓLIO", type="primary", use_container_width=True):
            
            # Verificar novamente se há ativos suficientes
            if len(selected_assets) < 2:
                st.error("❌ Selecione pelo menos 2 ativos para otimização")
            else:
                with st.spinner("🔄 Otimizando... Aguarde alguns segundos"):
                    try:
                        # Preparar lista completa de ativos (selected + short)
                        all_assets = selected_assets.copy()
                        if use_short and len(short_assets) > 0:
                            all_assets.extend(short_assets)
                        
                        # Inicializar otimizador com TODOS os ativos
                        optimizer = PortfolioOptimizer(df, all_assets)
                        
                        # Usar taxa livre detectada ou manual
                        if has_risk_free and hasattr(optimizer, 'risk_free_rate_total'):
                            final_risk_free_rate = optimizer.risk_free_rate_total
                        else:
                            final_risk_free_rate = used_risk_free_rate
                        
                        # Definir tipo de objetivo
                        if objective == "Maximizar Sharpe Ratio":
                            obj_type = 'sharpe'
                        elif objective == "Maximizar Sortino Ratio":
                            obj_type = 'sortino'
                        elif objective == "Minimizar Risco":
                            obj_type = 'volatility'
                        elif objective == "Maximizar Inclinação":
                            obj_type = 'slope'
                        elif objective == "Maximizar Inclinação/[(1-R²)×Vol]":
                            obj_type = 'hc10'
                        elif objective == "Maximizar Qualidade da Linearidade":
                            obj_type = 'quality_linear'
                        elif objective == "Maximizar Linearidade do Excesso":
                            obj_type = 'excess_hc10'
                        
                        # Preparar restrições individuais se habilitadas
                        constraints_to_use = individual_constraints if use_individual_constraints else None
                        
                        # Executar otimização
                        if use_short and len(short_assets) > 0:
                            # Otimização com shorts
                            result = optimizer.optimize_portfolio_with_shorts(
                                selected_assets=selected_assets,
                                short_assets=short_assets,
                                short_weights=short_weights,
                                objective_type=obj_type,
                                max_weight=max_weight,
                                min_weight=min_weight,
                                risk_free_rate=final_risk_free_rate,
                                individual_constraints=constraints_to_use
                            )
                        else:
                            # Otimização normal
                            result = optimizer.optimize_portfolio(
                                objective_type=obj_type,
                                target_return=None,
                                max_weight=max_weight,
                                min_weight=min_weight,
                                risk_free_rate=final_risk_free_rate,
                                individual_constraints=constraints_to_use
                            )
                        
                        if result['success']:
                            st.success("🎉 Otimização concluída com sucesso!")
                            
                            # Salvar pesos otimizados
                            st.session_state['optimal_weights'] = result['weights']
                            st.session_state['optimization_result'] = result
                            
                            # ANÁLISE EM DOIS PERÍODOS
                            tabs_results = st.tabs(["📊 Período de Otimização", "🔍 Período de Validação", "📈 Comparação"])
                            
                            with tabs_results[0]:
                                st.subheader("📊 Resultados no Período de Otimização (In-Sample)")
                                
                                # Métricas do período de otimização
                                metrics = result['metrics']
                                ref_anualiz = (1 + metrics['risk_free_rate']) ** (365 / dias_otim) - 1
                                sharpe_corrigido = (metrics['annual_return'] - ref_anualiz) / metrics['volatility'] if metrics['volatility'] > 0 else 0
                                sortino_corrigido = (metrics['annual_return'] - ref_anualiz) / metrics['downside_deviation'] if metrics['downside_deviation'] > 0 else 0
                                
                                # Primeira linha de métricas
                                col1, col2, col3, col4, col5 = st.columns(5)
                                
                                with col1:
                                    st.metric(
                                        "📈 Retorno Total", 
                                        f"{metrics['gv_final']:.2%}",
                                        help="Retorno acumulado total"
                                    )
                                
                                with col2:
                                    st.metric(
                                        "📅 Ganho Anual", 
                                        f"{metrics['annual_return']:.2%}",
                                        help="Retorno anualizado do portfólio"
                                    )
                                
                                with col3:
                                    st.metric(
                                        "📊 Volatilidade", 
                                        f"{metrics['volatility']:.2%}",
                                        help="Risco anualizado (DESVPAD.P × √252)"
                                    )
                                
                                with col4:
                                    st.metric(
                                        "⚡ Sharpe Ratio", 
                                        f"{sharpe_corrigido:.3f}",
                                        help=f"(Retorno Total - Taxa de referência) / Volatilidade\nTaxa de referência usada: {metrics['risk_free_rate']:.2%}"
                                    )
                                
                                with col5:
                                    st.metric(
                                        "🔥 Sortino Ratio", 
                                        f"{sortino_corrigido:.3f}",
                                        help="Similar ao Sharpe, mas considera apenas volatilidade negativa"
                                    )
                                
                                # Segunda linha - Métricas de risco
                                st.subheader("📊 Métricas de Risco")
                                col1, col2, col3, col4, col5 = st.columns(5)
                                
                                with col1:
                                    st.metric(
                                        "📈 R²", 
                                        f"{metrics['r_squared']:.3f}",
                                        help="Qualidade da linearidade da tendência"
                                    )
                                
                                with col2:
                                    st.metric(
                                        "⚠️ VaR 95% (Diário)", 
                                        f"{metrics['var_95_daily']:.2%}",
                                        help="Perda máxima esperada em 95% dos dias"
                                    )
                                
                                with col3:
                                    st.metric(
                                        "📉 CVaR 95% (Diário)", 
                                        f"{metrics['cvar_95_daily']:.2%}",
                                        help="Perda média nos 5% piores dias"
                                    )
                                
                                with col4:
                                    st.metric(
                                        "🏛️ Taxa Ref", 
                                        f"{metrics['risk_free_rate']:.2%}",
                                        help="Taxa de referência acumulada"
                                    )
                                
                                with col5:
                                    st.metric(
                                        "📈 Excesso", 
                                        f"{metrics['excess_return']:.2%}",
                                        help="Retorno Total - Taxa de referência"
                                    )
                                
                                # Composição do portfólio
                                st.subheader("📊 Composição do Portfólio Otimizado")
                                
                                portfolio_df = optimizer.get_portfolio_summary(result['weights'])
                                
                                #col1, col2 = st.columns([1, 1])
                                
                                #with col1:
                                st.subheader("📋 Tabela de Pesos")
                                portfolio_display = portfolio_df.copy()
                                portfolio_display['Peso Inicial (%)'] = portfolio_display['Peso Inicial (%)'].apply(lambda x: f"{x:.2f}%")
                                portfolio_display['Peso Atual (%)'] = portfolio_display['Peso Atual (%)'].apply(lambda x: f"{x:.2f}%")
                                
                                st.dataframe(portfolio_display, use_container_width=True, hide_index=True)
                                
                                # Mostrar totais
                                total_initial = portfolio_df['Peso Inicial (%)'].sum()
                                total_current = portfolio_df['Peso Atual (%)'].sum()
                                
                                col_total1, col_total2 = st.columns(2)
                                with col_total1:
                                    st.info(f"✅ Total inicial: {total_initial:.1f}%")
                                with col_total2:
                                    st.info(f"🔄 Total atual: {total_current:.1f}%")

                                # Tabela mensal - Período de Otimização
                                if hasattr(optimizer, 'dates'):
                                    st.subheader("📅 Performance Mensal - Período de Otimização")
                                    
                                    try:
                                        monthly_table, excess_table = create_monthly_returns_table(
                                            optimizer.returns_data,  # Dados só da otimização
                                            result['weights'],
                                            optimizer.dates,        # Datas só da otimização
                                            getattr(optimizer, 'risk_free_returns', None)
                                        )
                                        
                                        # Função para colorir valores
                                        def color_negative_red(val):
                                            if val == "-" or pd.isna(val):
                                                return 'color: gray'
                                            try:
                                                if isinstance(val, str) and '%' in val:
                                                    numeric_val = float(val.replace('%', '')) / 100
                                                else:
                                                    numeric_val = float(val)
                                                
                                                if numeric_val < 0:
                                                    return 'color: red; font-weight: bold'
                                                elif numeric_val > 0:
                                                    return 'color: green; font-weight: bold'
                                                else:
                                                    return 'color: black'
                                            except:
                                                return 'color: black'
                                        
                                        # Mostrar tabela mensal
                                        monthly_display = monthly_table.copy()
                                        for col in monthly_display.columns:
                                            monthly_display[col] = monthly_display[col].apply(
                                                lambda x: f"{x:.2%}" if pd.notna(x) else "-"
                                            )
                                        
                                        styled_table = monthly_display.style.applymap(color_negative_red)
                                        st.dataframe(styled_table, use_container_width=True)
                                        
                                        st.caption("💡 Esta tabela mostra apenas o período de otimização (treino)")
                                        
                                    except Exception as e:
                                        st.warning(f"⚠️ Não foi possível gerar tabelas mensais: {str(e)}")
                                
                                # Gráfico de evolução
                                st.subheader("📈 Evolução do Portfólio - Período de Otimização")
                                
                                # Buscar datas do otimizador
                                dates = getattr(optimizer, 'dates', None)
                                
                                # Criar DataFrame para o gráfico
                                periods = range(1, len(metrics['portfolio_cumulative']) + 1)
                                
                                # Criar figura com múltiplas linhas
                                fig_line = go.Figure()
                                
                                # Linha do portfólio
                                fig_line.add_trace(go.Scatter(
                                    x=pd.to_datetime(dates).dt.strftime('%d/%m/%Y') if dates is not None else list(periods),
                                    y=metrics['portfolio_cumulative'] * 100,
                                    mode='lines',
                                    name='Portfólio Otimizado',
                                    line=dict(color='#1f77b4', width=2.5)
                                ))
                                
                                # Se temos taxa livre, adicionar linha
                                if hasattr(optimizer, 'risk_free_cumulative') and optimizer.risk_free_cumulative is not None:
                                    fig_line.add_trace(go.Scatter(
                                        x=pd.to_datetime(dates).dt.strftime('%d/%m/%Y') if dates is not None else list(periods),
                                        y=optimizer.risk_free_cumulative * 100,
                                        mode='lines',
                                        name='Taxa de Referência',
                                        line=dict(color='#ff7f0e', width=2, dash='dash')
                                    ))
                                    
                                    # Adicionar linha de excesso de retorno
                                    excess_cumulative = metrics['portfolio_cumulative'] - optimizer.risk_free_cumulative.values
                                    fig_line.add_trace(go.Scatter(
                                        x=pd.to_datetime(dates).dt.strftime('%d/%m/%Y') if dates is not None else list(periods),
                                        y=excess_cumulative * 100,
                                        mode='lines',
                                        name='Excesso de Retorno',
                                        line=dict(color='#2ca02c', width=2, dash='dot')
                                    ))
                                
                                # Personalizar layout
                                fig_line.update_layout(
                                    title='Evolução do Retorno Acumulado',
                                    xaxis_title='Período',
                                    yaxis_title='Retorno Acumulado (%)',
                                    hovermode='x unified',
                                    height=500,
                                    showlegend=True,
                                    legend=dict(
                                        yanchor="top",
                                        y=0.99,
                                        xanchor="left",
                                        x=0.01
                                    ),
                                    xaxis=dict(
                                        showgrid=True, 
                                        gridwidth=1, 
                                        gridcolor='rgba(128,128,128,0.2)',
                                        nticks=12  # ← NOVO: Limita a 10 datas no máximo
                                    ),
                                    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                                )

                                
                                st.plotly_chart(fig_line, use_container_width=True)
                
                          
                            with tabs_results[1]:
                                if df_analise is not None:
                                    st.subheader("🔍 Resultados no Período de Validação (Out-of-Sample)")
                                    
                                    # Aplicar pesos otimizados no período estendido
                                    with st.spinner("Calculando performance no período de validação..."):
                                        try:
                                            # CORREÇÃO PARA SHORTS: Verificar quais ativos foram usados na otimização
                                            
                                            # Determinar lista de ativos usados na otimização
                                            if use_short and len(short_assets) > 0:
                                                # Com shorts: todos os ativos (selected + short)
                                                assets_used_in_optimization = selected_assets + short_assets
                                            else:
                                                # Sem shorts: apenas selected
                                                assets_used_in_optimization = selected_assets
                                            
                                            # Criar novo otimizador com dados estendidos E OS MESMOS ATIVOS
                                            optimizer_valid = PortfolioOptimizer(df_analise, assets_used_in_optimization)
                                            
                                            # Verificar se todos os ativos existem no período de validação
                                            missing_assets = []
                                            for asset in assets_used_in_optimization:
                                                if asset not in df_analise.columns:
                                                    missing_assets.append(asset)
                                                    st.warning(f"⚠️ Ativo {asset} não encontrado no período de validação")
                                            
                                            # Se faltar algum ativo, ajustar
                                            if missing_assets:
                                                st.error(f"❌ Ativos faltantes no período de validação: {', '.join(missing_assets)}")
                                                st.info("💡 Não é possível calcular validação com ativos faltantes")
                                            else:
                                                # VERIFICAÇÃO DE DIMENSÕES
                                                n_assets_optimization = len(result['weights'])
                                                n_assets_validation = optimizer_valid.returns_data.shape[1] if len(optimizer_valid.returns_data.shape) > 1 else 1
                                                
                                                st.info(f"📊 Debug: Otimização com {n_assets_optimization} ativos, Validação com {n_assets_validation} ativos")
                                                
                                                if n_assets_optimization != n_assets_validation:
                                                    st.error(f"❌ Incompatibilidade: {n_assets_optimization} pesos vs {n_assets_validation} ativos")
                                                    
                                                    # Tentar ajustar pesos se possível
                                                    if n_assets_optimization > n_assets_validation:
                                                        st.warning("⚠️ Alguns ativos da otimização não estão disponíveis na validação")
                                                        # Podemos tentar usar apenas os pesos dos ativos disponíveis
                                                        # mas isso alteraria a alocação total
                                                    else:
                                                        st.warning("⚠️ Há mais ativos na validação do que na otimização")
                                                else:
                                                    # Calcular métricas com os pesos já otimizados
                                                    portfolio_returns_valid = np.dot(optimizer_valid.returns_data.values, result['weights'])
                                                    cumulative_valid = np.cumsum(portfolio_returns_valid)
                                                    
                                                    # Separar períodos
                                                    periodo_otim = st.session_state['periodo_otimizacao']
                                                    n_dias_otim = len(optimizer.returns_data)
                                                    
                                                    # Métricas apenas do período de validação
                                                    if len(portfolio_returns_valid) > n_dias_otim:
                                                        returns_valid_only = portfolio_returns_valid[n_dias_otim:]
                                                        cumulative_valid_only = np.cumsum(returns_valid_only)
                                                    else:
                                                        # Se não há dados suficientes para validação
                                                        st.warning("⚠️ Período de validação muito curto")
                                                        returns_valid_only = portfolio_returns_valid
                                                        cumulative_valid_only = cumulative_valid
                                                    
                                                    # ✅ CALCULAR MÉTRICAS DE VALIDAÇÃO - METODOLOGIA BASE 0 CORRIGIDA

                                                    # ADICIONAR ESTA LINHA NO INÍCIO:
                                                    returns_valid_only = portfolio_returns_valid[n_dias_otim:]  # Retornos diários do período
                                                    n_dias_valid = len(returns_valid_only)  # ← ADICIONAR ESTA LINHA

                                                    # 1. RETORNO DO PORTFÓLIO - CRESCIMENTO RELATIVO (BASE 0)
                                                    # Retorno acumulado desde início até fim da validação
                                                    portfolio_total_ate_validacao = cumulative_valid[-1]  # Último ponto da curva completa

                                                    # Retorno acumulado desde início até fim da otimização
                                                    portfolio_total_ate_otimizacao = cumulative_valid[n_dias_otim-1]  # Ponto no fim da otimização

                                                    # Crescimento no período de validação (base 0)
                                                    retorno_total_valid = (1 + portfolio_total_ate_validacao) / (1 + portfolio_total_ate_otimizacao) - 1

                                                    # Anualizar usando dias corridos
                                                    if dias_valid > 0:
                                                        annual_return_valid = (1 + retorno_total_valid) ** (365/dias_valid) - 1
                                                    else:
                                                        annual_return_valid = 0

                                                    # 2. VOLATILIDADE ANUALIZADA - METODOLOGIA VARIAC_RESULT_PU (igual ao otimizador)
                                                    # Pegar retornos acumulados do período de validação
                                                    portfolio_cumulative_validacao = cumulative_valid[n_dias_otim-1:]  # Desde fim otimização

                                                    if len(portfolio_cumulative_validacao) > 1:
                                                        # Adicionar ponto inicial para calcular variação
                                                        portfolio_cumulative_with_zero = np.concatenate([[portfolio_cumulative_validacao[0]], portfolio_cumulative_validacao])
                                                        
                                                        # Calcular Variac_Result_PU (igual ao otimizador)
                                                        variac_result_pu = (1 + portfolio_cumulative_with_zero[1:]) / (1 + portfolio_cumulative_with_zero[:-1])
                                                        
                                                        # Retornos percentuais diários
                                                        portfolio_returns_pct_valid = variac_result_pu - 1
                                                        
                                                        # Volatilidade anualizada correta (mesma metodologia do otimizador)
                                                        vol_valid = np.std(portfolio_returns_pct_valid, ddof=0) * np.sqrt(252)
                                                    else:
                                                        vol_valid = 0

                                                    # 3. TAXA LIVRE DE RISCO - CRESCIMENTO RELATIVO (BASE 0)
                                                    if hasattr(optimizer_valid, 'risk_free_cumulative') and optimizer_valid.risk_free_cumulative is not None:
                                                        try:
                                                            # Taxa acumulada desde início até fim da validação
                                                            risk_free_total_ate_validacao = optimizer_valid.risk_free_cumulative.iloc[-1]
                                                            
                                                            # Taxa acumulada desde início até fim da otimização  
                                                            risk_free_total_ate_otimizacao = optimizer_valid.risk_free_cumulative.iloc[n_dias_otim-1]
                                                            
                                                            # Crescimento no período de validação (base 0)
                                                            risk_free_total_valid = (1 + risk_free_total_ate_validacao) / (1 + risk_free_total_ate_otimizacao) - 1
                                                            
                                                            # Anualizar usando dias corridos
                                                            if dias_valid > 0:
                                                                risk_free_annual_valid = (1 + risk_free_total_valid) ** (365/dias_valid) - 1
                                                            else:
                                                                risk_free_annual_valid = 0
                                                                
                                                        except Exception as e:
                                                            st.warning(f"⚠️ Erro ao calcular taxa livre: {str(e)}")
                                                            risk_free_annual_valid = 0

                                                    # Opção B: Taxa livre manual ou estimada
                                                    else:
                                                        # Se temos uma taxa acumulada do período de otimização
                                                        if final_risk_free_rate > 0 and dias_valid > 0:
                                                            # Estimar crescimento proporcional
                                                            periodo_otim_dias = (data_fim_otim - data_inicio_otim).days
                                                            if periodo_otim_dias > 0:
                                                                # Taxa anual base
                                                                taxa_anual_base = (1 + final_risk_free_rate) ** (365/periodo_otim_dias) - 1
                                                                # Aplicar ao período de validação
                                                                risk_free_annual_valid = taxa_anual_base
                                                            else:
                                                                risk_free_annual_valid = 0
                                                        else:
                                                            risk_free_annual_valid = 0
                                                    
                                                    # 4. SHARPE RATIO CORRIGIDO
                                                    if vol_valid > 0:
                                                        sharpe_valid = (annual_return_valid - risk_free_annual_valid) / vol_valid
                                                    else:
                                                        sharpe_valid = 0
                                                    
                                                    # ✅ SORTINO CORRIGIDO:
                                                    negative_returns_valid = portfolio_returns_pct_valid[portfolio_returns_pct_valid < 0]  # ← USAR ESTA!
                                                    if len(negative_returns_valid) > 0:
                                                        downside_dev_valid = np.std(negative_returns_valid, ddof=0) * np.sqrt(252)
                                                        if downside_dev_valid > 0:
                                                            sortino_valid = (annual_return_valid - risk_free_annual_valid) / downside_dev_valid
                                                        else:
                                                            sortino_valid = sharpe_valid
                                                    else:
                                                        sortino_valid = sharpe_valid
                                                    
                                                    # DEBUG: Mostrar componentes do cálculo
                                                    with st.expander("🔍 Detalhes dos Cálculos de Validação", expanded=False):
                                                        col_debug1, col_debug2, col_debug3 = st.columns(3)
                                                        
                                                        with col_debug1:
                                                            st.markdown("**Retornos:**")
                                                            st.write(f"• Total: {retorno_total_valid:.2%}")
                                                            st.write(f"• Anualizado: {annual_return_valid:.2%}")
                                                            st.write(f"• Dias: {dias_valid}")
                                                        
                                                        with col_debug2:
                                                            st.markdown("**Risco:**")
                                                            st.write(f"• Vol Anual: {vol_valid:.2%}")
                                                            st.write(f"• Downside Dev: {downside_dev_valid:.2%}" if 'downside_dev_valid' in locals() else "• Downside: N/A")
                                                        
                                                        with col_debug3:
                                                            st.markdown("**Taxa Livre:**")
                                                            st.write(f"• Anualizada: {risk_free_annual_valid:.2%}")
                                                            st.write(f"• Excesso: {(annual_return_valid - risk_free_annual_valid):.2%}")
                                                    
                                                    # Mostrar métricas de validação
                                                    col1, col2, col3, col4, col5 = st.columns(5)
                                                    
                                                    with col1:
                                                        st.metric("📈 Retorno Total", f"{retorno_total_valid:.2%}",
                                                                help=f"Retorno acumulado dos {dias_valid} dias de validação")
                                                    with col2:
                                                        st.metric("📅 Retorno Anual", f"{annual_return_valid:.2%}",
                                                                help="Retorno anualizado do período de validação")
                                                    with col3:
                                                        st.metric("📊 Volatilidade", f"{vol_valid:.2%}",
                                                                help="Volatilidade anualizada")
                                                    with col4:
                                                        st.metric("⚡ Sharpe Ratio", f"{sharpe_valid:.3f}",
                                                                help=f"(Ret.Anual {annual_return_valid:.1%} - Taxa {risk_free_annual_valid:.1%}) / Vol {vol_valid:.1%}")
                                                    with col5:
                                                        st.metric("🔥 Sortino Ratio", f"{sortino_valid:.3f}",
                                                                help="Similar ao Sharpe mas usa apenas volatilidade negativa")
                                                    

                                                    
                                        except Exception as e:
                                            st.error(f"❌ Erro na validação: {str(e)}")
                                            st.info("💡 Verifique se todos os ativos têm dados no período de validação")
 
    # TABELA MENSAL COMPLETA (Otimização + Validação)
                                        st.subheader("📅 Performance Mensal - Período Completo")
                                        
                                        try:
                                            # VERIFICAR SE EXISTE OTIMIZADOR DE VALIDAÇÃO
                                            if 'optimizer_valid' in locals() and hasattr(optimizer_valid, 'returns_data'):
                                                # Usar dados COMPLETOS do período estendido
                                                optimizer_to_use = optimizer_valid
                                                period_label = "Período Completo (Otimização + Validação)"
                                            else:
                                                # Usar dados apenas do período de otimização
                                                optimizer_to_use = optimizer
                                                period_label = "Período de Otimização"
                                                st.info("📍 Mostrando apenas período de otimização (configure validação para ver período completo)")
                                            
                                            # Usar dados do otimizador apropriado
                                            monthly_table_complete, excess_table_complete = create_monthly_returns_table(
                                                optimizer_to_use.returns_data,     # Dados apropriados
                                                result['weights'],                  # Pesos otimizados
                                                optimizer_to_use.dates,           # Datas apropriadas
                                                getattr(optimizer_to_use, 'risk_free_returns', None)
                                            )
                                            
                                            # Função para colorir valores negativos
                                            def color_monthly_values(val):
                                                if val == "-" or pd.isna(val):
                                                    return 'color: gray'
                                                try:
                                                    if isinstance(val, str) and '%' in val:
                                                        numeric_val = float(val.replace('%', '')) / 100
                                                    else:
                                                        numeric_val = float(val)
                                                    
                                                    if numeric_val < 0:
                                                        return 'color: red; font-weight: bold'
                                                    elif numeric_val > 0:
                                                        return 'color: green; font-weight: bold'
                                                    else:
                                                        return 'color: black'
                                                except:
                                                    return 'color: black'
                                            
                                            # Preparar tabela para exibição
                                            monthly_display_complete = monthly_table_complete.copy()
                                            for col in monthly_display_complete.columns:
                                                monthly_display_complete[col] = monthly_display_complete[col].apply(
                                                    lambda x: f"{x:.2%}" if pd.notna(x) else "-"
                                                )
                                            
                                            # Aplicar estilo
                                            styled_monthly_complete = monthly_display_complete.style.applymap(color_monthly_values)
                                            
                                            # Informações do período
                                            if 'optimizer_valid' in locals() and hasattr(optimizer_valid, 'returns_data'):
                                                # Com validação
                                                periodo_otim = st.session_state['periodo_otimizacao']
                                                periodo_analise = st.session_state['periodo_analise']
                                                
                                                col_info1, col_info2 = st.columns(2)
                                                with col_info1:
                                                    st.info(f"📊 **Período:** {periodo_otim['inicio'].strftime('%d/%m/%Y')} a {periodo_analise['fim'].strftime('%d/%m/%Y')}")
                                                with col_info2:
                                                    st.info(f"🔍 **Incluindo:** Otimização + Validação (período completo)")
                                            else:
                                                # Sem validação
                                                periodo_otim = st.session_state['periodo_otimizacao']
                                                
                                                col_info1, col_info2 = st.columns(2)
                                                with col_info1:
                                                    st.info(f"📊 **Período:** {periodo_otim['inicio'].strftime('%d/%m/%Y')} a {periodo_otim['fim'].strftime('%d/%m/%Y')}")
                                                with col_info2:
                                                    st.warning(f"⚠️ **Apenas:** Período de otimização")
                                            
                                            # Mostrar tabela
                                            st.dataframe(styled_monthly_complete, use_container_width=True)
                                            
                                            # Nota explicativa condicional
                                            if 'optimizer_valid' in locals() and hasattr(optimizer_valid, 'returns_data'):
                                                st.caption("💡 Esta tabela mostra a performance mensal durante todo o período analisado (treino + teste)")
                                            else:
                                                st.caption("💡 Esta tabela mostra apenas o período de otimização (configure validação para ver período completo)")
                                            
                                        except Exception as e:
                                            st.warning(f"⚠️ Não foi possível gerar tabela mensal: {str(e)}")
                                            st.info("💡 Verifique se há dados suficientes no período selecionado") 
                                        
                                        # Gráfico comparativo
                                        st.subheader("📈 Evolução do Portfólio - Período Completo")
                                        
                                        # VERIFICAR SE HÁ DADOS DE VALIDAÇÃO
                                        if df_analise is not None:
                                            # Usar dados estendidos se disponíveis
                                            if use_short and len(short_assets) > 0:
                                                assets_used_in_optimization = selected_assets + short_assets
                                            else:
                                                assets_used_in_optimization = selected_assets
                                            
                                            try:
                                                # Criar otimizador com dados completos
                                                optimizer_extended = PortfolioOptimizer(df_analise, assets_used_in_optimization)
                                                
                                                # Calcular métricas com período completo
                                                metrics_extended = optimizer_extended.calculate_portfolio_metrics(result['weights'], final_risk_free_rate)
                                                
                                                # Buscar datas completas
                                                dates_extended = getattr(optimizer_extended, 'dates', None)
                                                
                                                # Determinar ponto de divisão (fim da otimização)
                                                n_dias_otim = len(optimizer.returns_data)
                                                
                                                # Criar figura com múltiplas linhas
                                                fig_extended = go.Figure()
                                                
                                                # 1. LINHA DO PORTFÓLIO (período completo)
                                                fig_extended.add_trace(go.Scatter(
                                                    x=pd.to_datetime(dates_extended).dt.strftime('%d/%m/%Y') if dates_extended is not None else list(range(len(metrics_extended['portfolio_cumulative']))),
                                                    y=metrics_extended['portfolio_cumulative'] * 100,
                                                    mode='lines',
                                                    name='Portfólio Otimizado',
                                                    line=dict(color='#1f77b4', width=2.5)
                                                ))
                                                
                                                # 2. LINHA DA TAXA DE REFERÊNCIA (se existir)
                                                if hasattr(optimizer_extended, 'risk_free_cumulative') and optimizer_extended.risk_free_cumulative is not None:
                                                    fig_extended.add_trace(go.Scatter(
                                                        x=pd.to_datetime(dates_extended).dt.strftime('%d/%m/%Y') if dates_extended is not None else list(range(len(metrics_extended['portfolio_cumulative']))),
                                                        y=optimizer_extended.risk_free_cumulative * 100,
                                                        mode='lines',
                                                        name='Taxa de Referência',
                                                        line=dict(color='#ff7f0e', width=2, dash='dash')
                                                    ))
                                                    
                                                    # 3. LINHA DO EXCESSO DE RETORNO
                                                    if metrics_extended.get('excess_cumulative') is not None:
                                                        fig_extended.add_trace(go.Scatter(
                                                            x=pd.to_datetime(dates_extended).dt.strftime('%d/%m/%Y') if dates_extended is not None else list(range(len(metrics_extended['portfolio_cumulative']))),
                                                            y=metrics_extended['excess_cumulative'] * 100,
                                                            mode='lines',
                                                            name='Excesso de Retorno',
                                                            line=dict(color='#2ca02c', width=2, dash='dot')
                                                        ))
                                                
                                                # 4. LINHA VERTICAL - Fim da Otimização
                                                fig_extended.add_vline(
                                                    x=n_dias_otim-1,  # Índice do último dia de otimização
                                                    line_dash="solid",
                                                    line_color="red",
                                                    line_width=2,
                                                    annotation_text="Fim da Otimização",
                                                    annotation_position="top"
                                                )
                                                
                                                # 5. ÁREAS SOMBREADAS (sem textos internos)
                                                # Área de Otimização (verde claro)
                                                fig_extended.add_vrect(
                                                    x0=0, 
                                                    x1=n_dias_otim-1,
                                                    fillcolor="green", 
                                                    opacity=0.1
                                                )
                                                
                                                # Área de Validação (azul claro)
                                                if len(metrics_extended['portfolio_cumulative']) > n_dias_otim:
                                                    fig_extended.add_vrect(
                                                        x0=n_dias_otim-1, 
                                                        x1=len(metrics_extended['portfolio_cumulative'])-1,
                                                        fillcolor="blue", 
                                                        opacity=0.1
                                                    )
                                                
                                                # 6. PERSONALIZAR LAYOUT
                                                fig_extended.update_layout(
                                                    title='Evolução do Retorno Acumulado - Visão Completa (In-Sample + Out-of-Sample)',
                                                    xaxis_title='Período',
                                                    yaxis_title='Retorno Acumulado (%)',
                                                    hovermode='x unified',
                                                    height=500,
                                                    showlegend=True,
                                                    legend=dict(
                                                        yanchor="top",
                                                        y=0.99,
                                                        xanchor="left",
                                                        x=0.01
                                                    ),
                                                    # CONFIGURAR EIXO X: máximo 12 pontos
                                                    xaxis=dict(
                                                        nticks=12  # Máximo 12 marcações, sem inclinação
                                                    )
                                                )
                                                
                                                # 7. MOSTRAR GRÁFICO
                                                st.plotly_chart(fig_extended, use_container_width=True)
                                                
                                                # 8. INFORMAÇÕES ADICIONAIS
                                                col_graf1, col_graf2, col_graf3 = st.columns(3)
                                                
                                                with col_graf1:
                                                    st.success(f"🎯 **Período de Otimização:** {n_dias_otim} dias")
                                                
                                                with col_graf2:
                                                    dias_validacao = dias_valid
                                                    st.info(f"🔍 **Período de Validação:** {dias_validacao} dias")
                                                
                                                with col_graf3:
                                                    total_dias = len(metrics_extended['portfolio_cumulative'])
                                                    st.metric("📊 Total de Registros", f"{total_dias}")
                                                
                                                # 9. NOTA EXPLICATIVA
                                                st.caption("💡 Este gráfico mostra a evolução completa do portfólio, destacando visualmente onde termina o treino e começa a validação")
                                                
                                            except Exception as e:
                                                st.error(f"❌ Erro ao criar gráfico estendido: {str(e)}")
                                                st.info("💡 Usando gráfico do período de otimização apenas")
                                                
                                                # FALLBACK: Gráfico original se der erro
                                                dates = getattr(optimizer, 'dates', None)
                                                periods = range(1, len(metrics['portfolio_cumulative']) + 1)
                                                
                                                fig_line = go.Figure()
                                                
                                                fig_line.add_trace(go.Scatter(
                                                    x=pd.to_datetime(dates).dt.strftime('%d/%m/%Y') if dates is not None else list(periods),
                                                    y=metrics['portfolio_cumulative'] * 100,
                                                    mode='lines',
                                                    name='Portfólio Otimizado',
                                                    line=dict(color='#1f77b4', width=2.5)
                                                ))
                                                
                                                if hasattr(optimizer, 'risk_free_cumulative') and optimizer.risk_free_cumulative is not None:
                                                    fig_line.add_trace(go.Scatter(
                                                        x=pd.to_datetime(dates).dt.strftime('%d/%m/%Y') if dates is not None else list(periods),
                                                        y=optimizer.risk_free_cumulative * 100,
                                                        mode='lines',
                                                        name='Taxa de Referência',
                                                        line=dict(color='#ff7f0e', width=2, dash='dash')
                                                    ))
                                                    
                                                    excess_cumulative = metrics['portfolio_cumulative'] - optimizer.risk_free_cumulative.values
                                                    fig_line.add_trace(go.Scatter(
                                                        x=pd.to_datetime(dates).dt.strftime('%d/%m/%Y') if dates is not None else list(periods),
                                                        y=excess_cumulative * 100,
                                                        mode='lines',
                                                        name='Excesso de Retorno',
                                                        line=dict(color='#2ca02c', width=2, dash='dot')
                                                    ))
                                                
                                                fig_line.update_layout(
                                                    title='Evolução do Retorno Acumulado - Período de Otimização',
                                                    xaxis_title='Período',
                                                    yaxis_title='Retorno Acumulado (%)',
                                                    hovermode='x unified',
                                                    height=500,
                                                    showlegend=True
                                                )
                                                
                                                st.plotly_chart(fig_line, use_container_width=True)
                                        
                                        else:
                                            # SE NÃO HÁ DADOS DE VALIDAÇÃO: Gráfico original
                                            dates = getattr(optimizer, 'dates', None)
                                            periods = range(1, len(metrics['portfolio_cumulative']) + 1)
                                            
                                            fig_line = go.Figure()
                                            
                                            fig_line.add_trace(go.Scatter(
                                                x=pd.to_datetime(dates).dt.strftime('%d/%m/%Y') if dates is not None else list(periods),
                                                y=metrics['portfolio_cumulative'] * 100,
                                                mode='lines',
                                                name='Portfólio Otimizado',
                                                line=dict(color='#1f77b4', width=2.5)
                                            ))
                                            
                                            if hasattr(optimizer, 'risk_free_cumulative') and optimizer.risk_free_cumulative is not None:
                                                fig_line.add_trace(go.Scatter(
                                                    x=pd.to_datetime(dates).dt.strftime('%d/%m/%Y') if dates is not None else list(periods),
                                                    y=optimizer.risk_free_cumulative * 100,
                                                    mode='lines',
                                                    name='Taxa de Referência',
                                                    line=dict(color='#ff7f0e', width=2, dash='dash')
                                                ))
                                                
                                                excess_cumulative = metrics['portfolio_cumulative'] - optimizer.risk_free_cumulative.values
                                                fig_line.add_trace(go.Scatter(
                                                    x=pd.to_datetime(dates).dt.strftime('%d/%m/%Y') if dates is not None else list(periods),
                                                    y=excess_cumulative * 100,
                                                    mode='lines',
                                                    name='Excesso de Retorno',
                                                    line=dict(color='#2ca02c', width=2, dash='dot')
                                                ))
                                            
                                            fig_line.update_layout(
                                                title='Evolução do Retorno Acumulado - Período de Otimização Apenas',
                                                xaxis_title='Período',
                                                yaxis_title='Retorno Acumulado (%)',
                                                hovermode='x unified',
                                                height=500,
                                                showlegend=True
                                            )
                                            
                                            st.plotly_chart(fig_line, use_container_width=True)
                                            st.info("📍 Configure um período de validação para ver o gráfico estendido")



                                else:
                                    st.info("📍 Configure um período de validação para ver resultados out-of-sample")
                            
                            with tabs_results[2]:
                                if df_analise is not None and 'retorno_total_valid' in locals():
                                    st.subheader("📊 Comparação: Otimização vs Validação")
                                    
                                    # Criar DataFrame comparativo
                                    comparison_data = {
                                        'Métrica': ['Retorno Anual (%)', 'Volatilidade (%)'],
                                        'Otimização (In-Sample)': [
                                            f"{metrics['annual_return']*100:.2f}",
                                            f"{metrics['volatility']*100:.2f}",
                                        ],
                                        'Validação (Out-of-Sample)': [
                                            f"{annual_return_valid*100:.2f}",
                                            f"{vol_valid*100:.2f}",
                                        ],
                                        'Diferença': [
                                            f"{(annual_return_valid - metrics['annual_return'])*100:.2f}",
                                            f"{(vol_valid - metrics['volatility'])*100:.2f}",
                                        ]
                                    }
                                    
                                    df_comparison = pd.DataFrame(comparison_data)
                                    
                                    # Aplicar cores condicionais
                                    def highlight_diff(val):
                                        try:
                                            num = float(val)
                                            if num > 0:
                                                return 'color: green'
                                            elif num < 0:
                                                return 'color: red'
                                        except:
                                            pass
                                        return ''
                                    
                                    styled_df = df_comparison.style.applymap(
                                        highlight_diff, 
                                        subset=['Diferença']
                                    )
                                    
                                    st.dataframe(styled_df, use_container_width=True)

                                else:
                                    st.info("📍 Configure um período de validação para comparar resultados")
                            
                        else:
                            st.error(f"❌ {result['message']}")
                            st.info("💡 Tente ajustar os parâmetros da otimização")
                    
                    except Exception as e:
                        st.error(f"❌ Erro durante a otimização: {str(e)}")
                        st.info("💡 Verifique se os dados estão no formato correto")

else:
    # Mensagem quando não há dados
    st.info("👈 Faça upload de uma planilha Excel para começar")
    
    # Verificar se GitHub está configurado
    if GITHUB_USER == "SEU_USUARIO_GITHUB":
        st.warning(
            "⚠️ **Para habilitar os dados de exemplo:**\n\n"
            "1. **Configure o GitHub** no código:\n"
            "   - Substitua `GITHUB_USER` pelo seu usuário\n"
            "   - Substitua `GITHUB_REPO` pelo nome do seu repositório\n\n"
            "2. **Crie a pasta** `sample_data/` no seu repositório\n\n"
            "3. **Faça upload** dos arquivos Excel de exemplo"
        )
    
    # Instruções
    st.markdown("""
    ### 📝 Como usar v3.0:
    
    1. **Carregue dados completos** (todo período disponível)
    
    2. **Selecione as 3 datas**:
       - Início da otimização
       - Fim da otimização  
       - Fim da análise (validação)
    
    3. **Configure** os parâmetros de otimização
    
    4. **Otimize** e veja resultados in-sample vs out-of-sample!
    
    ### 💡 Novidade v3.0:
    Os dados ficam salvos na sessão! Você pode testar múltiplos períodos sem recarregar!
    """)

# Rodapé
st.markdown("---")
st.markdown("*Desenvolvido com Streamlit - Otimizador de Portfólio v3.0* 🚀")
st.markdown("*Agora com Janelas Temporais para Backtesting Profissional*")
