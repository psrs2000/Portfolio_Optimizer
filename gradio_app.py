"""
Otimizador de Portfolio v3.0 - Interface Gradio
Baseado na metodologia de Markowitz com Janelas Temporais
"""

import gradio as gr
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from optimizer import PortfolioOptimizer
import yfinance as yf
from datetime import datetime, timedelta
from scipy import stats
from io import BytesIO
import tempfile
import os

# =============================================================================
# CONFIGURACAO GITHUB
# =============================================================================
GITHUB_USER = "psrs2000"
GITHUB_REPO = "Portfolio_Optimizer"
GITHUB_BRANCH = "main"

SAMPLE_DATA = {
    "Acoes Brasileiras": "acoes_brasileiras.xlsx",
    "Fundos Imobiliarios": "fundos_imobiliarios.xlsx",
    "Fundos de Investimento": "fundos_de_investimento.xlsx",
    "ETFs Nacionais": "etfs_nacionais.xlsx",
    "Criptomoedas": "criptomoedas.xlsx",
}

# =============================================================================
# FUNCOES DE DADOS
# =============================================================================

def load_from_github(dataset_name):
    """Carrega arquivo Excel do GitHub"""
    filename = SAMPLE_DATA.get(dataset_name)
    if not filename:
        return None, "Dataset nao encontrado"

    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/sample_data/{filename}"

    try:
        df_bruto = pd.read_excel(url)
        if len(df_bruto.columns) > 0:
            df_bruto.columns.values[0] = "Data"
        return df_bruto, f"Carregado: {dataset_name} ({len(df_bruto)} linhas, {len(df_bruto.columns)-1} ativos)"
    except Exception as e:
        return None, f"Erro ao carregar: {str(e)}"


def load_from_upload(file):
    """Carrega arquivo Excel do upload"""
    if file is None:
        return None, "Nenhum arquivo selecionado"
    try:
        df_bruto = pd.read_excel(file.name if hasattr(file, 'name') else file)
        if len(df_bruto.columns) > 0:
            df_bruto.columns.values[0] = "Data"
        return df_bruto, f"Upload: {len(df_bruto)} linhas, {len(df_bruto.columns)-1} ativos"
    except Exception as e:
        return None, f"Erro ao ler arquivo: {str(e)}"


def buscar_dados_yahoo(simbolos_text, tipo_ativo, data_inicio, data_fim,
                       ativo_referencia, usar_referencia):
    """Busca dados do Yahoo Finance"""
    sufixo_map = {
        "Acoes Brasileiras (.SA)": ".SA",
        "Criptomoedas": "",
        "Acoes Americanas": "",
        "ETFs Americanos": "",
        "Codigos Livres": "",
    }
    sufixo = sufixo_map.get(tipo_ativo, ".SA")

    simbolos = [s.strip().upper() for s in simbolos_text.strip().split('\n') if s.strip()]

    if len(simbolos) < 2:
        return None, "Digite pelo menos 2 simbolos"

    # Adicionar referencia
    if usar_referencia and ativo_referencia.strip():
        ref = ativo_referencia.strip().upper()
        if ref not in simbolos:
            simbolos.append(ref)

    start = data_inicio
    end = data_fim

    dados_historicos = {}
    erros = []

    for simbolo in simbolos:
        try:
            if sufixo and "." not in simbolo:
                simbolo_completo = simbolo + sufixo
            else:
                simbolo_completo = simbolo

            ticker = yf.Ticker(simbolo_completo)
            hist = ticker.history(start=start, end=end, interval="1d")

            if not hist.empty and len(hist) > 5:
                dados_historicos[simbolo] = hist
            else:
                erros.append(simbolo)
        except Exception:
            erros.append(simbolo)

    if not dados_historicos:
        return None, f"Nenhum dado encontrado. Erros: {', '.join(erros)}"

    # Consolidar
    lista_dfs = []
    for simbolo, dados in dados_historicos.items():
        if 'Close' in dados.columns:
            df_temp = pd.DataFrame({simbolo: dados['Close']})
            if hasattr(df_temp.index, 'tz') and df_temp.index.tz is not None:
                df_temp.index = df_temp.index.tz_localize(None)
            lista_dfs.append(df_temp)

    if not lista_dfs:
        return None, "Erro ao consolidar dados"

    df_consolidado = pd.concat(lista_dfs, axis=1, sort=True)
    df_consolidado.index.name = "Data"
    df_consolidado = df_consolidado.reset_index()

    # Reorganizar referencia
    if usar_referencia and ativo_referencia.strip():
        ref = ativo_referencia.strip().upper()
        if ref in df_consolidado.columns:
            nome_ref = f"Taxa_Ref_{ref}"
            df_consolidado = df_consolidado.rename(columns={ref: nome_ref})
            cols = ['Data', nome_ref] + [c for c in df_consolidado.columns if c not in ['Data', nome_ref]]
            df_consolidado = df_consolidado[cols]

    msg = f"Yahoo Finance: {len(dados_historicos)} ativos carregados"
    if erros:
        msg += f" (erros: {', '.join(erros)})"

    return df_consolidado, msg


def transformar_base_zero(df_precos):
    """Transforma dados de precos para base 0"""
    if df_precos is None or df_precos.empty:
        return None, []

    df_limpo = df_precos.copy()
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

    if df_limpo.empty:
        return None, colunas_removidas

    for coluna in df_limpo.columns:
        df_limpo[coluna] = df_limpo[coluna].replace(0, np.nan)
        df_limpo[coluna] = df_limpo[coluna].ffill()
    df_limpo = df_limpo.fillna(0)

    df_base_zero = pd.DataFrame(index=df_limpo.index)

    for coluna in df_limpo.columns:
        valores = df_limpo[coluna].values
        if len(valores) == 0:
            continue
        cota_1 = valores[0]
        if cota_1 == 0:
            continue
        novos_valores = np.zeros(len(valores))
        novos_valores[0] = 0.0
        for i in range(1, len(valores)):
            novos_valores[i] = (valores[i] - valores[i-1]) / cota_1
        df_base_zero[coluna] = novos_valores

    return df_base_zero, colunas_removidas


def processar_periodo(df_bruto, data_inicio, data_fim, data_analise=None):
    """Processa dados brutos para o periodo selecionado"""
    try:
        if 'Data' in df_bruto.columns:
            df_trabalho = df_bruto.copy()
            df_trabalho['Data'] = pd.to_datetime(df_trabalho['Data'])
            df_trabalho = df_trabalho.set_index('Data')
        else:
            df_trabalho = df_bruto.copy()
            if not isinstance(df_trabalho.index, pd.DatetimeIndex):
                df_trabalho.index = pd.to_datetime(df_trabalho.index)

        data_inicio = pd.Timestamp(data_inicio)
        data_fim = pd.Timestamp(data_fim)

        df_otimizacao = df_trabalho[(df_trabalho.index >= data_inicio) &
                                     (df_trabalho.index <= data_fim)].copy()

        df_analise_estendida = None
        if data_analise and pd.Timestamp(data_analise) > data_fim:
            data_analise = pd.Timestamp(data_analise)
            df_analise_estendida = df_trabalho[(df_trabalho.index >= data_inicio) &
                                               (df_trabalho.index <= data_analise)].copy()

        df_base0_otim, cols_rem = transformar_base_zero(df_otimizacao)

        df_base0_analise = None
        if df_analise_estendida is not None:
            df_base0_analise, _ = transformar_base_zero(df_analise_estendida)

        if df_base0_otim is not None:
            df_base0_otim = df_base0_otim.reset_index()
            df_base0_otim.rename(columns={'index': 'Data'}, inplace=True)

        if df_base0_analise is not None:
            df_base0_analise = df_base0_analise.reset_index()
            df_base0_analise.rename(columns={'index': 'Data'}, inplace=True)

        return df_base0_otim, df_base0_analise, cols_rem
    except Exception as e:
        return None, None, []


# =============================================================================
# RANKING DE ATIVOS
# =============================================================================

def calculate_asset_ranking(df_base_zero, risk_free_column=None,
                            peso_inclinacao=0.33, peso_desvio=0.33, peso_correlacao=0.33):
    """Calcula ranking de ativos"""
    try:
        if 'Data' not in df_base_zero.columns:
            return None

        df_work = df_base_zero.copy()
        dates_col = pd.to_datetime(df_work['Data'])

        # Identificar referencia
        if risk_free_column and risk_free_column in df_work.columns:
            ref_col = risk_free_column
            asset_columns = [c for c in df_work.columns if c not in ['Data', risk_free_column]]
        elif len(df_work.columns) > 2:
            second_col = df_work.columns[1]
            if any(t in second_col.lower() for t in ['taxa', 'livre', 'risco', 'ibov', 'ref', 'cdi', 'selic']):
                ref_col = second_col
                asset_columns = [c for c in df_work.columns if c not in ['Data', second_col]]
            else:
                ref_col = df_work.columns[1]
                asset_columns = df_work.columns[2:].tolist()
        else:
            return None

        # Diferenca e Integral
        diferenca_data = {'Data': dates_col}
        for asset in asset_columns:
            diferenca_data[f"{asset}_diff"] = df_work[asset] - df_work[ref_col]
        df_diferenca = pd.DataFrame(diferenca_data)

        integral_data = {'Data': dates_col}
        for asset in asset_columns:
            integral_data[f"{asset}_integral"] = df_diferenca[f"{asset}_diff"].cumsum()
        df_integral = pd.DataFrame(integral_data)

        # Calcular parametros
        all_slopes, all_deviations = [], []
        for asset in asset_columns:
            try:
                x_data = np.arange(len(df_integral))
                y_data = df_integral[f"{asset}_integral"].values
                slope, _, _, _, _ = stats.linregress(x_data, y_data)
                std_dev = df_diferenca[f"{asset}_diff"].std()
                all_slopes.append(slope)
                all_deviations.append(std_dev)
            except:
                continue

        max_slope = max(all_slopes) if all_slopes else 1
        max_deviation = max(all_deviations) if all_deviations else 1

        rankings = []
        for asset in asset_columns:
            try:
                x_data = np.arange(len(df_integral))
                y_data = df_integral[f"{asset}_integral"].values
                slope, _, r_value, _, _ = stats.linregress(x_data, y_data)
                r_squared = r_value ** 2

                asset_integral = df_work[asset].cumsum().values
                ref_integral = df_work[ref_col].cumsum().values
                correlation_direct = np.corrcoef(asset_integral, ref_integral)[0, 1]

                std_dev = df_diferenca[f"{asset}_diff"].std()

                slope_norm = slope / max_slope if max_slope > 0 else 0
                std_dev_norm = std_dev / max_deviation if max_deviation > 0 else 0

                numerador = (peso_inclinacao * slope_norm +
                           peso_desvio * (1 - std_dev_norm) +
                           peso_correlacao * correlation_direct)
                denominador = peso_inclinacao + peso_desvio + peso_correlacao
                indice_bruto = numerador / denominador if denominador > 0 else 0

                rankings.append({
                    'Ativo': asset, 'Inclinacao': slope, 'Inclinacao_Norm': slope_norm,
                    'R2': r_squared, 'Correlacao': correlation_direct,
                    'Desvio_Padrao': std_dev, 'Desvio_Norm': std_dev_norm,
                    'Indice_Bruto': indice_bruto
                })
            except:
                rankings.append({
                    'Ativo': asset, 'Inclinacao': 0, 'Inclinacao_Norm': 0,
                    'R2': 0, 'Correlacao': 0, 'Desvio_Padrao': 0,
                    'Desvio_Norm': 0, 'Indice_Bruto': 0
                })

        df_ranking = pd.DataFrame(rankings)
        if len(df_ranking) > 0:
            max_idx = df_ranking['Indice_Bruto'].max()
            min_idx = df_ranking['Indice_Bruto'].min()
            if max_idx > min_idx:
                df_ranking['Indice'] = (df_ranking['Indice_Bruto'] - min_idx) / (max_idx - min_idx)
            else:
                df_ranking['Indice'] = 0.5
            df_ranking = df_ranking.drop(columns=['Indice_Bruto'])
        else:
            df_ranking['Indice'] = 0

        df_ranking = df_ranking.sort_values('Indice', ascending=False).reset_index(drop=True)
        df_ranking['Posicao'] = range(1, len(df_ranking) + 1)

        return {
            'ranking': df_ranking,
            'referencia': ref_col,
            'total_ativos': len(asset_columns)
        }
    except:
        return None


# =============================================================================
# TABELA MENSAL
# =============================================================================

def create_monthly_returns_table(returns_data, weights, dates=None, risk_free_returns=None):
    """Cria tabela de retornos mensais"""
    portfolio_returns_daily = np.dot(returns_data.values, weights)
    portfolio_cumulative = np.cumsum(portfolio_returns_daily)

    if dates is not None:
        portfolio_df = pd.DataFrame({'cumulative': portfolio_cumulative}, index=dates)
    else:
        dates_idx = pd.date_range(start='2020-01-01', periods=len(portfolio_cumulative), freq='D')
        portfolio_df = pd.DataFrame({'cumulative': portfolio_cumulative}, index=dates_idx)

    monthly_cumulative = portfolio_df['cumulative'].resample('ME').last()

    monthly_returns = []
    previous_cumulative = 0
    for _, current_cumulative in monthly_cumulative.items():
        if previous_cumulative != 0:
            monthly_return = (current_cumulative - previous_cumulative) / (1 + previous_cumulative)
        else:
            monthly_return = current_cumulative
        monthly_returns.append(monthly_return)
        previous_cumulative = current_cumulative

    monthly_returns_series = pd.Series(monthly_returns, index=monthly_cumulative.index)

    monthly_df = pd.DataFrame({
        'Year': monthly_returns_series.index.year,
        'Month': monthly_returns_series.index.month,
        'Return': monthly_returns_series.values
    })

    pivot_table = monthly_df.pivot(index='Year', columns='Month', values='Return')
    month_names = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',
                   7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
    pivot_table.columns = [month_names.get(c, f'M{c}') for c in pivot_table.columns]

    yearly_returns = []
    for year in pivot_table.index:
        year_data = pivot_table.loc[year].dropna()
        if len(year_data) > 0:
            annual = 1.0
            for mr in year_data:
                annual *= (1 + mr)
            annual -= 1
            yearly_returns.append(annual)
        else:
            yearly_returns.append(np.nan)
    pivot_table['Total Anual'] = yearly_returns

    return pivot_table


# =============================================================================
# WALK-FORWARD
# =============================================================================

def run_walk_forward(df_bruto, config, risk_free_column_name):
    """Executa walk-forward test"""
    try:
        period_to_days = {
            '3m': 90, '6m': 180, '1a': 365, '2a': 730, '3a': 1095,
            '1sem': 7, '2sem': 14, '1mes': 30, '2mes': 60, '3mes': 90
        }

        otim_days = period_to_days[config['otim_period']]
        rebal_days = period_to_days[config['rebal_period']]

        data_inicial = pd.to_datetime(df_bruto['Data'].iloc[0])
        data_final = pd.to_datetime(df_bruto['Data'].iloc[-1])
        total_calendar_days = (data_final - data_inicial).days + 1

        max_steps = (total_calendar_days - otim_days) // rebal_days
        if max_steps < 1:
            return None
        if max_steps > 1000000:
            max_steps = 1000000

        ret_acumulado = 1.0
        taxa_ref_acumulada = 1.0
        primeira_data = None
        ultima_data = None
        step_metrics = []
        volatilidades = []

        for step_num in range(1, max_steps + 1):
            try:
                inicio_otim_days = (step_num - 1) * rebal_days
                fim_otim_days = inicio_otim_days + otim_days
                fim_valid_days = fim_otim_days + rebal_days

                d_inicio_otim = data_inicial + pd.Timedelta(days=inicio_otim_days)
                d_fim_otim = data_inicial + pd.Timedelta(days=fim_otim_days - 1)
                d_fim_valid = data_inicial + pd.Timedelta(days=fim_valid_days - 1)

                if d_fim_valid > data_final:
                    break

                df_completo_bruto = df_bruto[
                    (pd.to_datetime(df_bruto['Data']) >= d_inicio_otim) &
                    (pd.to_datetime(df_bruto['Data']) <= d_fim_valid)
                ].copy().reset_index(drop=True)

                if len(df_completo_bruto) == 0:
                    continue

                df_completo_b0, cols_rem = transformar_base_zero(df_completo_bruto.set_index('Data'))
                if df_completo_b0 is None:
                    continue

                df_completo_b0 = df_completo_b0.reset_index()
                df_completo_b0.rename(columns={'index': 'Data'}, inplace=True)

                df_otim_b0 = df_completo_b0[
                    (pd.to_datetime(df_completo_b0['Data']) >= d_inicio_otim) &
                    (pd.to_datetime(df_completo_b0['Data']) <= d_fim_otim)
                ].copy().reset_index(drop=True)

                df_valid_b0 = df_completo_b0[
                    (pd.to_datetime(df_completo_b0['Data']) > d_fim_otim) &
                    (pd.to_datetime(df_completo_b0['Data']) <= d_fim_valid)
                ].copy().reset_index(drop=True)

                if len(df_otim_b0) < 10 or len(df_valid_b0) < 2:
                    continue

                # Ranking e selecao
                ranking_result = calculate_asset_ranking(df_otim_b0, risk_free_column_name)
                if not ranking_result:
                    continue

                df_ranking = ranking_result['ranking']
                score_min = config['rank_min'] / 100
                score_max = config['rank_max'] / 100

                filtered = df_ranking[
                    (df_ranking['Indice'] >= score_min) & (df_ranking['Indice'] <= score_max)
                ]
                if len(filtered) < 2:
                    continue

                selected_assets = filtered['Ativo'].tolist()

                # Otimizar
                optimizer = PortfolioOptimizer(df_otim_b0, selected_assets)
                risk_free_rate = getattr(optimizer, 'risk_free_rate_total', 0.0)

                result = optimizer.optimize_portfolio(
                    objective_type=config['objective'],
                    max_weight=config['weight_max'],
                    min_weight=config['weight_min'],
                    risk_free_rate=risk_free_rate
                )

                if not result['success']:
                    continue

                # Out-of-sample
                available = [a for a in result['assets'] if a in df_completo_b0.columns]
                if len(available) != len(result['assets']):
                    continue

                opt_completo = PortfolioOptimizer(df_completo_b0, available)
                port_ret = np.dot(opt_completo.returns_data.values, result['weights'])
                cumul = np.cumsum(port_ret)

                n_otim = len(df_otim_b0)
                n_total = len(df_completo_b0)
                n_valid = n_total - n_otim

                if n_valid <= 0:
                    continue

                p_fim_otim = cumul[n_otim - 1]
                p_fim_valid = cumul[-1]
                ret_valid = (1 + p_fim_valid) / (1 + p_fim_otim) - 1

                ret_acumulado *= (1 + ret_valid)

                # Taxa ref
                if hasattr(opt_completo, 'risk_free_cumulative') and opt_completo.risk_free_cumulative is not None:
                    try:
                        t_otim = opt_completo.risk_free_cumulative.iloc[n_otim - 1]
                        t_valid = opt_completo.risk_free_cumulative.iloc[-1]
                        taxa_valid = (1 + t_valid) / (1 + t_otim) - 1
                        taxa_ref_acumulada *= (1 + taxa_valid)
                    except:
                        pass

                # Volatilidade
                port_cum_v = cumul[n_otim:]
                if len(port_cum_v) > 1:
                    port_cum_wz = np.concatenate([[p_fim_otim], port_cum_v])
                    var_pu = (1 + port_cum_wz[1:]) / (1 + port_cum_wz[:-1])
                    vol = np.std(var_pu - 1, ddof=0) * np.sqrt(252)
                    volatilidades.append(vol)

                if primeira_data is None:
                    primeira_data = pd.to_datetime(df_valid_b0['Data'].iloc[0])
                ultima_data = pd.to_datetime(df_valid_b0['Data'].iloc[-1])

                step_metrics.append({
                    'n_assets': len(available),
                    'total_return': ret_valid
                })

            except:
                continue

        if not step_metrics:
            return None

        ret_total = ret_acumulado - 1
        taxa_total = taxa_ref_acumulada - 1

        if primeira_data and ultima_data:
            dias = (ultima_data - primeira_data).days + 1
            ret_anual = (1 + ret_total) ** (365/dias) - 1 if dias > 0 else 0
            taxa_anual = (1 + taxa_total) ** (365/dias) - 1 if dias > 0 else 0
        else:
            ret_anual = ret_total
            taxa_anual = taxa_total
            dias = 0

        vol_media = np.mean(volatilidades) if volatilidades else 0
        sharpe = (ret_anual - taxa_anual) / vol_media if vol_media > 0 else 0

        return {
            'config': config,
            'metrics': {
                'sharpe': sharpe,
                'annual_return': ret_anual,
                'risk_free_annual': taxa_anual,
                'volatility': vol_media,
                'n_assets': np.mean([s['n_assets'] for s in step_metrics]),
            },
            'n_steps': len(step_metrics),
            'total_return': ret_total,
            'total_days': dias
        }
    except:
        return None


# =============================================================================
# FUNCOES PRINCIPAIS DO GRADIO
# =============================================================================

def carregar_dados_exemplo(dataset_name, state):
    """Handler para carregar dados de exemplo"""
    df, msg = load_from_github(dataset_name)
    if df is not None:
        state['dados_brutos'] = df
        state['fonte'] = msg
        datas = pd.to_datetime(df['Data'])
        state['data_min'] = str(datas.min().date())
        state['data_max'] = str(datas.max().date())
        n_ativos = len(df.columns) - 1

        # Detectar referencia
        ref_info = ""
        if len(df.columns) > 2:
            col2 = df.columns[1]
            if any(t in col2.lower() for t in ['taxa','livre','risco','ibov','ref','cdi','selic']):
                ref_info = f" | Referencia: {col2}"
                n_ativos -= 1

        info = f"Dados carregados: {len(df)} dias, {n_ativos} ativos{ref_info}\nPeriodo: {state['data_min']} a {state['data_max']}"
        return state, info
    return state, msg


def carregar_dados_upload(file, state):
    """Handler para upload"""
    df, msg = load_from_upload(file)
    if df is not None:
        state['dados_brutos'] = df
        state['fonte'] = msg
        datas = pd.to_datetime(df['Data'])
        state['data_min'] = str(datas.min().date())
        state['data_max'] = str(datas.max().date())
        return state, msg + f"\nPeriodo: {state['data_min']} a {state['data_max']}"
    return state, msg


def carregar_yahoo(simbolos, tipo, d_inicio, d_fim, ref, usar_ref, state):
    """Handler para Yahoo Finance"""
    df, msg = buscar_dados_yahoo(simbolos, tipo, d_inicio, d_fim, ref, usar_ref)
    if df is not None:
        state['dados_brutos'] = df
        state['fonte'] = msg
        datas = pd.to_datetime(df['Data'])
        state['data_min'] = str(datas.min().date())
        state['data_max'] = str(datas.max().date())
        return state, msg
    return state, msg


def processar_periodo_handler(d_inicio, d_fim, d_analise, usar_validacao, state):
    """Processa o periodo selecionado e retorna ativos disponiveis"""
    if 'dados_brutos' not in state:
        return state, "Carregue dados primeiro!", gr.update(), gr.update()

    df_bruto = state['dados_brutos']

    d_analise_final = d_analise if usar_validacao else None
    df_otim, df_analise_ext, cols_rem = processar_periodo(df_bruto, d_inicio, d_fim, d_analise_final)

    if df_otim is None:
        return state, "Erro ao processar periodo!", gr.update(), gr.update()

    state['df_otim'] = df_otim
    state['df_analise'] = df_analise_ext
    state['data_inicio_otim'] = str(d_inicio)
    state['data_fim_otim'] = str(d_fim)
    state['data_fim_analise'] = str(d_analise) if usar_validacao else None

    # Identificar ativos
    has_risk_free = False
    if len(df_otim.columns) > 2 and isinstance(df_otim.columns[1], str):
        col_name = df_otim.columns[1].lower()
        if any(t in col_name for t in ['taxa','livre','risco','ibov','ref','cdi','selic']):
            has_risk_free = True
            state['risk_free_col'] = df_otim.columns[1]

    if 'data' in df_otim.columns[0].lower():
        start_col = 2 if has_risk_free else 1
        asset_columns = df_otim.columns[start_col:].tolist()
    else:
        asset_columns = df_otim.columns.tolist()

    state['asset_columns'] = asset_columns
    state['has_risk_free'] = has_risk_free

    dias_otim = (pd.Timestamp(d_fim) - pd.Timestamp(d_inicio)).days
    msg = f"Periodo processado: {len(df_otim)} registros, {len(asset_columns)} ativos, {dias_otim} dias"
    if cols_rem:
        msg += f"\nColunas removidas: {', '.join(cols_rem)}"
    if df_analise_ext is not None:
        dias_valid = (pd.Timestamp(d_analise) - pd.Timestamp(d_fim)).days
        msg += f"\nValidacao: {dias_valid} dias adicionais"

    return (state, msg,
            gr.update(choices=asset_columns, value=asset_columns[:min(250, len(asset_columns))]),
            gr.update(choices=asset_columns, value=[]))


def calcular_ranking_handler(score_min, score_max, p_inc, p_desv, p_cor, state):
    """Calcula ranking e retorna tabela"""
    if 'df_otim' not in state:
        return state, None, "Processe o periodo primeiro!"

    df = state['df_otim']
    risk_free_col = state.get('risk_free_col')

    ranking_result = calculate_asset_ranking(df, risk_free_col, p_inc, p_desv, p_cor)

    if ranking_result is None:
        return state, None, "Erro ao calcular ranking"

    state['ranking_result'] = ranking_result

    df_rank = ranking_result['ranking']

    # Filtrar por score
    filtered = df_rank[(df_rank['Indice'] >= score_min) & (df_rank['Indice'] <= score_max)]
    state['ranked_assets'] = filtered['Ativo'].tolist()

    # Formatar para exibicao
    display = df_rank[['Posicao', 'Ativo', 'Indice', 'Inclinacao_Norm', 'R2', 'Correlacao', 'Desvio_Norm']].copy()
    display['Indice'] = display['Indice'].round(4)
    display['Inclinacao_Norm'] = display['Inclinacao_Norm'].round(3)
    display['R2'] = display['R2'].round(3)
    display['Correlacao'] = display['Correlacao'].round(3)
    display['Desvio_Norm'] = display['Desvio_Norm'].round(3)

    msg = f"Ranking: {ranking_result['total_ativos']} ativos | Ref: {ranking_result['referencia']} | Selecionados (score {score_min:.2f}-{score_max:.2f}): {len(filtered)}"

    return state, display, msg


def otimizar_portfolio_handler(selected_assets, objective, min_weight, max_weight,
                                use_short, short_assets, short_weight_pct, state):
    """Executa otimizacao e retorna resultados"""
    if 'df_otim' not in state:
        return (state, "Processe o periodo primeiro!", None, None, None, None, None, None)

    if len(selected_assets) < 2:
        return (state, "Selecione pelo menos 2 ativos!", None, None, None, None, None, None)

    df = state['df_otim']
    df_analise = state.get('df_analise')
    has_risk_free = state.get('has_risk_free', False)

    # Mapear objetivo
    obj_map = {
        "Maximizar Sharpe Ratio": "sharpe",
        "Maximizar Sortino Ratio": "sortino",
        "Minimizar Risco": "volatility",
        "Maximizar Inclinacao": "slope",
        "Maximizar Inclinacao/[(1-R2)xVol]": "hc10",
        "Maximizar Qualidade da Linearidade": "quality_linear",
        "Maximizar Linearidade do Excesso": "excess_hc10",
    }
    obj_type = obj_map.get(objective, 'sharpe')

    min_w = min_weight / 100
    max_w = max_weight / 100

    try:
        # Preparar ativos
        all_assets = list(selected_assets)
        short_weights_dict = {}

        if use_short and short_assets:
            all_assets.extend(short_assets)
            for sa in short_assets:
                short_weights_dict[sa] = short_weight_pct / 100

        optimizer = PortfolioOptimizer(df, all_assets)

        if has_risk_free and hasattr(optimizer, 'risk_free_rate_total'):
            risk_free_rate = optimizer.risk_free_rate_total
        else:
            risk_free_rate = 0.0

        # Otimizar
        if use_short and short_assets:
            result = optimizer.optimize_portfolio_with_shorts(
                selected_assets=list(selected_assets),
                short_assets=list(short_assets),
                short_weights=short_weights_dict,
                objective_type=obj_type,
                max_weight=max_w,
                min_weight=min_w,
                risk_free_rate=risk_free_rate
            )
        else:
            result = optimizer.optimize_portfolio(
                objective_type=obj_type,
                max_weight=max_w,
                min_weight=min_w,
                risk_free_rate=risk_free_rate
            )

        if not result['success']:
            return (state, f"Otimizacao falhou: {result['message']}", None, None, None, None, None, None)

        state['result'] = result
        state['optimizer'] = optimizer

        metrics = result['metrics']

        # Calcular dias
        d_inicio = pd.Timestamp(state['data_inicio_otim'])
        d_fim = pd.Timestamp(state['data_fim_otim'])
        dias_otim = (d_fim - d_inicio).days

        ref_anualiz = (1 + metrics['risk_free_rate']) ** (365 / max(dias_otim, 1)) - 1
        sharpe_c = (metrics['annual_return'] - ref_anualiz) / metrics['volatility'] if metrics['volatility'] > 0 else 0
        sortino_c = (metrics['annual_return'] - ref_anualiz) / metrics['downside_deviation'] if metrics['downside_deviation'] > 0 else 0

        # ===== METRICAS IN-SAMPLE =====
        metricas_insample = pd.DataFrame({
            'Metrica': [
                'Retorno Total', 'Ganho Anual', 'Volatilidade',
                'Sharpe Ratio', 'Sortino Ratio',
                'R2', 'VaR 95% (Diario)', 'CVaR 95% (Diario)',
                'Taxa Ref Acum.', 'Excesso de Retorno'
            ],
            'Valor': [
                f"{metrics['gv_final']:.2%}", f"{metrics['annual_return']:.2%}",
                f"{metrics['volatility']:.2%}", f"{sharpe_c:.3f}", f"{sortino_c:.3f}",
                f"{metrics['r_squared']:.3f}", f"{metrics['var_95_daily']:.2%}",
                f"{metrics['cvar_95_daily']:.2%}", f"{metrics['risk_free_rate']:.2%}",
                f"{metrics['excess_return']:.2%}"
            ]
        })

        # ===== COMPOSICAO =====
        portfolio_df = optimizer.get_portfolio_summary(result['weights'])
        composicao = portfolio_df.copy()
        composicao['Peso Inicial (%)'] = composicao['Peso Inicial (%)'].apply(lambda x: f"{x:.2f}%")
        composicao['Peso Atual (%)'] = composicao['Peso Atual (%)'].apply(lambda x: f"{x:.2f}%")

        # ===== TABELA MENSAL IN-SAMPLE =====
        try:
            monthly_table = create_monthly_returns_table(
                optimizer.returns_data, result['weights'],
                optimizer.dates, getattr(optimizer, 'risk_free_returns', None)
            )
            monthly_display = monthly_table.copy()
            for col in monthly_display.columns:
                monthly_display[col] = monthly_display[col].apply(
                    lambda x: f"{x:.2%}" if pd.notna(x) else "-"
                )
            monthly_display.index.name = 'Ano'
            monthly_display = monthly_display.reset_index()
        except:
            monthly_display = None

        # ===== GRAFICO IN-SAMPLE =====
        dates = getattr(optimizer, 'dates', None)
        fig_insample = go.Figure()

        x_axis = pd.to_datetime(dates) if dates is not None else list(range(len(metrics['portfolio_cumulative'])))

        fig_insample.add_trace(go.Scatter(
            x=x_axis, y=metrics['portfolio_cumulative'] * 100,
            mode='lines', name='Portfolio Otimizado',
            line=dict(color='#1f77b4', width=2.5)
        ))

        if hasattr(optimizer, 'risk_free_cumulative') and optimizer.risk_free_cumulative is not None:
            fig_insample.add_trace(go.Scatter(
                x=x_axis, y=optimizer.risk_free_cumulative * 100,
                mode='lines', name='Taxa de Referencia',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
            excess = metrics['portfolio_cumulative'] - optimizer.risk_free_cumulative.values
            fig_insample.add_trace(go.Scatter(
                x=x_axis, y=excess * 100,
                mode='lines', name='Excesso de Retorno',
                line=dict(color='#2ca02c', width=2, dash='dot')
            ))

        fig_insample.update_layout(
            title='Evolucao do Retorno Acumulado - In-Sample',
            xaxis_title='Periodo', yaxis_title='Retorno Acumulado (%)',
            hovermode='x unified', height=500, showlegend=True,
            template='plotly_white',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )

        # ===== VALIDACAO (Out-of-Sample) =====
        fig_completo = None
        metricas_outsample = None
        comparacao = None

        if df_analise is not None:
            try:
                assets_used = list(selected_assets)
                if use_short and short_assets:
                    assets_used.extend(short_assets)

                optimizer_valid = PortfolioOptimizer(df_analise, assets_used)

                port_ret_valid = np.dot(optimizer_valid.returns_data.values, result['weights'])
                cumul_valid = np.cumsum(port_ret_valid)

                n_dias_otim = len(optimizer.returns_data)

                if len(port_ret_valid) > n_dias_otim:
                    ret_valid_only = port_ret_valid[n_dias_otim:]

                    d_analise_ts = pd.Timestamp(state['data_fim_analise'])
                    dias_valid = (d_analise_ts - d_fim).days

                    # Retorno validacao
                    p_total_valid = cumul_valid[-1]
                    p_total_otim = cumul_valid[n_dias_otim - 1]
                    ret_total_valid = (1 + p_total_valid) / (1 + p_total_otim) - 1

                    annual_ret_valid = (1 + ret_total_valid) ** (365/max(dias_valid, 1)) - 1 if dias_valid > 0 else 0

                    # Volatilidade validacao
                    port_cum_v = cumul_valid[n_dias_otim - 1:]
                    if len(port_cum_v) > 1:
                        port_cum_wz = np.concatenate([[port_cum_v[0]], port_cum_v])
                        var_pu = (1 + port_cum_wz[1:]) / (1 + port_cum_wz[:-1])
                        port_ret_pct_valid = var_pu - 1
                        vol_valid = np.std(port_ret_pct_valid, ddof=0) * np.sqrt(252)
                    else:
                        vol_valid = 0
                        port_ret_pct_valid = np.array([])

                    # Taxa ref validacao
                    risk_free_annual_valid = 0
                    if hasattr(optimizer_valid, 'risk_free_cumulative') and optimizer_valid.risk_free_cumulative is not None:
                        try:
                            rf_tot_valid = optimizer_valid.risk_free_cumulative.iloc[-1]
                            rf_tot_otim = optimizer_valid.risk_free_cumulative.iloc[n_dias_otim - 1]
                            rf_valid = (1 + rf_tot_valid) / (1 + rf_tot_otim) - 1
                            risk_free_annual_valid = (1 + rf_valid) ** (365/max(dias_valid, 1)) - 1 if dias_valid > 0 else 0
                        except:
                            pass

                    sharpe_valid = (annual_ret_valid - risk_free_annual_valid) / vol_valid if vol_valid > 0 else 0

                    neg_ret = port_ret_pct_valid[port_ret_pct_valid < 0] if len(port_ret_pct_valid) > 0 else np.array([])
                    if len(neg_ret) > 0:
                        dd_valid = np.std(neg_ret, ddof=0) * np.sqrt(252)
                        sortino_valid = (annual_ret_valid - risk_free_annual_valid) / dd_valid if dd_valid > 0 else sharpe_valid
                    else:
                        sortino_valid = sharpe_valid

                    metricas_outsample = pd.DataFrame({
                        'Metrica': ['Retorno Total', 'Retorno Anual', 'Volatilidade',
                                    'Sharpe Ratio', 'Sortino Ratio'],
                        'Valor': [f"{ret_total_valid:.2%}", f"{annual_ret_valid:.2%}",
                                  f"{vol_valid:.2%}", f"{sharpe_valid:.3f}", f"{sortino_valid:.3f}"]
                    })

                    # Comparacao
                    comparacao = pd.DataFrame({
                        'Metrica': ['Retorno Anual (%)', 'Volatilidade (%)'],
                        'In-Sample': [f"{metrics['annual_return']*100:.2f}", f"{metrics['volatility']*100:.2f}"],
                        'Out-of-Sample': [f"{annual_ret_valid*100:.2f}", f"{vol_valid*100:.2f}"],
                        'Diferenca': [f"{(annual_ret_valid - metrics['annual_return'])*100:.2f}",
                                      f"{(vol_valid - metrics['volatility'])*100:.2f}"]
                    })

                # Grafico completo
                dates_ext = getattr(optimizer_valid, 'dates', None)
                metrics_ext = optimizer_valid.calculate_portfolio_metrics(result['weights'], risk_free_rate)

                fig_completo = go.Figure()
                x_ext = pd.to_datetime(dates_ext) if dates_ext is not None else list(range(len(metrics_ext['portfolio_cumulative'])))

                fig_completo.add_trace(go.Scatter(
                    x=x_ext, y=metrics_ext['portfolio_cumulative'] * 100,
                    mode='lines', name='Portfolio Otimizado',
                    line=dict(color='#1f77b4', width=2.5)
                ))

                if hasattr(optimizer_valid, 'risk_free_cumulative') and optimizer_valid.risk_free_cumulative is not None:
                    fig_completo.add_trace(go.Scatter(
                        x=x_ext, y=optimizer_valid.risk_free_cumulative * 100,
                        mode='lines', name='Taxa de Referencia',
                        line=dict(color='#ff7f0e', width=2, dash='dash')
                    ))
                    if metrics_ext.get('excess_cumulative') is not None:
                        fig_completo.add_trace(go.Scatter(
                            x=x_ext, y=metrics_ext['excess_cumulative'] * 100,
                            mode='lines', name='Excesso de Retorno',
                            line=dict(color='#2ca02c', width=2, dash='dot')
                        ))

                fig_completo.add_vline(
                    x=x_ext[n_dias_otim - 1] if dates_ext is not None else n_dias_otim - 1,
                    line_dash="solid", line_color="red", line_width=2,
                    annotation_text="Fim Otimizacao"
                )

                fig_completo.add_vrect(x0=x_ext[0] if dates_ext is not None else 0,
                                       x1=x_ext[n_dias_otim-1] if dates_ext is not None else n_dias_otim-1,
                                       fillcolor="green", opacity=0.08)

                if len(metrics_ext['portfolio_cumulative']) > n_dias_otim:
                    fig_completo.add_vrect(
                        x0=x_ext[n_dias_otim-1] if dates_ext is not None else n_dias_otim-1,
                        x1=x_ext[-1] if dates_ext is not None else len(metrics_ext['portfolio_cumulative'])-1,
                        fillcolor="blue", opacity=0.08
                    )

                fig_completo.update_layout(
                    title='Evolucao Completa - In-Sample + Out-of-Sample',
                    xaxis_title='Periodo', yaxis_title='Retorno Acumulado (%)',
                    hovermode='x unified', height=500, showlegend=True,
                    template='plotly_white',
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                )

                # Tabela mensal completa
                try:
                    monthly_complete = create_monthly_returns_table(
                        optimizer_valid.returns_data, result['weights'],
                        optimizer_valid.dates, getattr(optimizer_valid, 'risk_free_returns', None)
                    )
                    monthly_complete_disp = monthly_complete.copy()
                    for col in monthly_complete_disp.columns:
                        monthly_complete_disp[col] = monthly_complete_disp[col].apply(
                            lambda x: f"{x:.2%}" if pd.notna(x) else "-"
                        )
                    monthly_complete_disp.index.name = 'Ano'
                    monthly_complete_disp = monthly_complete_disp.reset_index()
                    monthly_display = monthly_complete_disp  # Sobrescreve com completa
                except:
                    pass

            except Exception as e:
                pass

        msg = f"Otimizacao concluida com sucesso! Objetivo: {objective}"

        return (state, msg, metricas_insample, composicao, monthly_display,
                fig_insample, fig_completo if fig_completo else fig_insample,
                metricas_outsample, comparacao)

    except Exception as e:
        return (state, f"Erro: {str(e)}", None, None, None, None, None, None, None)


def auto_otimizar_handler(otim_windows, rebal_periods, objectives,
                          rank_min, rank_max, weight_min, weight_max, state):
    """Executa auto-otimizacao walk-forward"""
    if 'dados_brutos' not in state:
        return "Carregue dados primeiro!", None

    df_bruto = state['dados_brutos']

    # Detectar risk free
    risk_free_col = None
    if len(df_bruto.columns) > 2 and isinstance(df_bruto.columns[1], str):
        col_name = df_bruto.columns[1].lower()
        if any(t in col_name for t in ['taxa','livre','risco','ibov','ref','cdi','selic']):
            risk_free_col = df_bruto.columns[1]

    obj_map = {
        "Sharpe": "sharpe", "MinRisco": "volatility",
        "Inc/[(1-R2)xVol]": "hc10", "Qualidade Linear": "quality_linear"
    }

    configs = []
    for otim in otim_windows:
        for rebal in rebal_periods:
            for obj in objectives:
                configs.append({
                    'otim_period': otim, 'rebal_period': rebal,
                    'objective': obj_map.get(obj, 'sharpe'),
                    'rank_min': rank_min, 'rank_max': rank_max,
                    'weight_min': weight_min / 100, 'weight_max': weight_max / 100,
                    'use_shorts': False, 'short_asset': None, 'short_weight': 0,
                })

    if not configs:
        return "Selecione pelo menos 1 opcao de cada categoria!", None

    results = []
    for config in configs:
        try:
            r = run_walk_forward(df_bruto, config, risk_free_col)
            if r:
                results.append(r)
        except:
            continue

    if not results:
        return "Nenhum resultado valido obtido.", None

    results.sort(key=lambda x: x['metrics']['sharpe'], reverse=True)

    obj_names = {'sharpe': 'Sharpe', 'volatility': 'MinRisco',
                 'hc10': 'Inc/[(1-R2)xVol]', 'quality_linear': 'Qualidade'}

    rows = []
    for i, r in enumerate(results):
        c = r['config']
        m = r['metrics']
        rows.append({
            'Rank': i + 1,
            'Otimizacao': c['otim_period'],
            'Rebalanceamento': c['rebal_period'],
            'Objetivo': obj_names.get(c['objective'], c['objective']),
            'N_Ativos': int(m['n_assets']),
            'Sharpe': f"{m['sharpe']:.3f}",
            'Retorno(%)': f"{m['annual_return']:.1%}",
            'Taxa_Ref(%)': f"{m.get('risk_free_annual', 0):.1%}",
            'Volatilidade(%)': f"{m['volatility']:.1%}",
        })

    df_results = pd.DataFrame(rows)
    msg = f"Concluido! {len(results)}/{len(configs)} configuracoes validas"

    return msg, df_results


def download_data_handler(state):
    """Gera arquivo Excel para download"""
    if 'dados_brutos' not in state:
        return None

    df = state['dados_brutos']
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    output.seek(0)

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx',
                                          prefix='portfolio_data_')
    tmpfile.write(output.getvalue())
    tmpfile.close()
    return tmpfile.name


# =============================================================================
# INTERFACE GRADIO
# =============================================================================

def create_app():

    custom_css = """
    .gradio-container {
        max-width: 1400px !important;
        margin: auto !important;
    }
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 2em;
        font-weight: bold;
        margin-bottom: 0.2em;
    }
    .sub-title {
        text-align: center;
        color: #666;
        font-size: 1.1em;
        margin-bottom: 1em;
    }
    """

    with gr.Blocks(
        title="Otimizador de Portfolio v3.0",
    ) as app:

        # Estado global
        state = gr.State({})

        # Header
        gr.HTML('<div class="main-title">Otimizador de Portfolio v3.0</div>')
        gr.HTML('<div class="sub-title">Metodologia de Markowitz com Janelas Temporais e Auto-Otimizacao Walk-Forward</div>')

        # ===== ABA 1: CARREGAR DADOS =====
        with gr.Tab("1. Carregar Dados"):
            status_dados = gr.Textbox(label="Status", interactive=False, lines=2)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Dados de Exemplo (GitHub)")
                    dataset_choice = gr.Dropdown(
                        choices=list(SAMPLE_DATA.keys()),
                        label="Escolha o dataset",
                        value="Acoes Brasileiras"
                    )
                    btn_github = gr.Button("Carregar Exemplo", variant="primary")

                with gr.Column(scale=1):
                    gr.Markdown("### Upload Manual")
                    file_upload = gr.File(label="Planilha Excel (.xlsx)", file_types=[".xlsx", ".xls"])
                    btn_upload = gr.Button("Carregar Upload", variant="primary")

                with gr.Column(scale=1):
                    gr.Markdown("### Yahoo Finance")
                    yahoo_simbolos = gr.Textbox(
                        label="Simbolos (1 por linha)",
                        value="PETR4\nVALE3\nITUB4\nBBDC4\nABEV3",
                        lines=5
                    )
                    yahoo_tipo = gr.Dropdown(
                        choices=["Acoes Brasileiras (.SA)", "Criptomoedas",
                                 "Acoes Americanas", "ETFs Americanos", "Codigos Livres"],
                        label="Tipo de Ativo",
                        value="Acoes Brasileiras (.SA)"
                    )
                    with gr.Row():
                        yahoo_inicio = gr.Textbox(label="Data Inicio", value=str((datetime.now() - timedelta(days=365*3)).date()))
                        yahoo_fim = gr.Textbox(label="Data Fim", value=str(datetime.now().date()))
                    with gr.Row():
                        yahoo_ref = gr.Textbox(label="Ativo Referencia", value="BOVA11")
                        yahoo_usar_ref = gr.Checkbox(label="Incluir Ref", value=True)
                    btn_yahoo = gr.Button("Buscar Yahoo Finance", variant="primary")

            btn_download = gr.Button("Baixar Dados (Excel)")
            file_download = gr.File(label="Download", visible=True)

            # Eventos
            btn_github.click(
                carregar_dados_exemplo,
                inputs=[dataset_choice, state],
                outputs=[state, status_dados]
            )
            btn_upload.click(
                carregar_dados_upload,
                inputs=[file_upload, state],
                outputs=[state, status_dados]
            )
            btn_yahoo.click(
                carregar_yahoo,
                inputs=[yahoo_simbolos, yahoo_tipo, yahoo_inicio, yahoo_fim,
                        yahoo_ref, yahoo_usar_ref, state],
                outputs=[state, status_dados]
            )
            btn_download.click(download_data_handler, inputs=[state], outputs=[file_download])

        # ===== ABA 2: PERIODO & RANKING =====
        with gr.Tab("2. Periodo e Ranking"):
            gr.Markdown("### Definir Janelas Temporais")

            with gr.Row():
                periodo_inicio = gr.Textbox(label="Inicio Otimizacao (YYYY-MM-DD)", value="2020-01-01")
                periodo_fim = gr.Textbox(label="Fim Otimizacao (YYYY-MM-DD)", value="2023-12-31")

            with gr.Row():
                usar_validacao = gr.Checkbox(label="Usar Validacao (Forward Test)?", value=True)
                periodo_analise = gr.Textbox(label="Fim da Analise (YYYY-MM-DD)", value="2025-06-30")

            btn_processar = gr.Button("Processar Periodo", variant="primary", size="lg")
            status_periodo = gr.Textbox(label="Status do Processamento", interactive=False, lines=3)

            gr.Markdown("---")
            gr.Markdown("### Ranking de Ativos (Opcional)")

            with gr.Row():
                rank_score_min = gr.Slider(0, 1, value=0.7, step=0.05, label="Score Minimo")
                rank_score_max = gr.Slider(0, 1, value=1.0, step=0.05, label="Score Maximo")

            with gr.Row():
                peso_inc = gr.Slider(0, 1, value=0.33, step=0.05, label="Peso Inclinacao")
                peso_desv = gr.Slider(0, 1, value=0.33, step=0.05, label="Peso Desvio")
                peso_cor = gr.Slider(0, 1, value=0.33, step=0.05, label="Peso Correlacao")

            btn_ranking = gr.Button("Calcular Ranking", variant="secondary")
            status_ranking = gr.Textbox(label="Status Ranking", interactive=False)
            ranking_table = gr.Dataframe(label="Ranking de Ativos", interactive=False)

        # ===== ABA 3: OTIMIZACAO =====
        with gr.Tab("3. Otimizacao"):
            gr.Markdown("### Selecao de Ativos e Configuracao")

            with gr.Row():
                with gr.Column(scale=2):
                    selected_assets = gr.Dropdown(
                        choices=[], multiselect=True, label="Ativos para Otimizacao",
                        info="Minimo 2 ativos"
                    )
                with gr.Column(scale=1):
                    objective = gr.Dropdown(
                        choices=[
                            "Maximizar Sharpe Ratio",
                            "Maximizar Sortino Ratio",
                            "Minimizar Risco",
                            "Maximizar Inclinacao",
                            "Maximizar Inclinacao/[(1-R2)xVol]",
                            "Maximizar Qualidade da Linearidade",
                            "Maximizar Linearidade do Excesso",
                        ],
                        label="Objetivo", value="Maximizar Sharpe Ratio"
                    )

            with gr.Row():
                min_weight = gr.Slider(0, 20, value=0, step=1, label="Peso Minimo por Ativo (%)")
                max_weight = gr.Slider(5, 100, value=30, step=1, label="Peso Maximo por Ativo (%)")

            with gr.Accordion("Posicoes Short / Hedge (Opcional)", open=False):
                use_short = gr.Checkbox(label="Habilitar Short", value=False)
                short_assets = gr.Dropdown(choices=[], multiselect=True, label="Ativos Short")
                short_weight = gr.Slider(-100, 0, value=-100, step=1, label="Peso Short (%)")

            btn_otimizar = gr.Button("OTIMIZAR PORTFOLIO", variant="primary", size="lg")
            status_otim = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("---")

            with gr.Tab("In-Sample"):
                metricas_insample = gr.Dataframe(label="Metricas - Periodo de Otimizacao", interactive=False)
                composicao_df = gr.Dataframe(label="Composicao do Portfolio", interactive=False)
                tabela_mensal = gr.Dataframe(label="Performance Mensal", interactive=False)
                grafico_insample = gr.Plot(label="Evolucao In-Sample")

            with gr.Tab("Out-of-Sample"):
                metricas_outsample = gr.Dataframe(label="Metricas - Periodo de Validacao", interactive=False)
                grafico_completo = gr.Plot(label="Evolucao Completa")

            with gr.Tab("Comparacao"):
                comparacao_df = gr.Dataframe(label="In-Sample vs Out-of-Sample", interactive=False)

        # ===== ABA 4: AUTO-OTIMIZACAO =====
        with gr.Tab("4. Auto-Otimizacao Walk-Forward"):
            gr.Markdown("### Teste automatico de multiplas configuracoes")
            gr.Markdown("O sistema testa combinacoes de janelas, rebalanceamentos e objetivos para encontrar a melhor estrategia historica.")

            with gr.Row():
                with gr.Column():
                    auto_otim = gr.CheckboxGroup(
                        choices=["3m", "6m", "1a", "2a", "3a"],
                        value=["6m", "1a"],
                        label="Janelas de Otimizacao"
                    )
                with gr.Column():
                    auto_rebal = gr.CheckboxGroup(
                        choices=["1sem", "2sem", "1mes", "2mes", "3mes"],
                        value=["1mes", "2mes"],
                        label="Periodos de Rebalanceamento"
                    )
                with gr.Column():
                    auto_obj = gr.CheckboxGroup(
                        choices=["Sharpe", "MinRisco", "Inc/[(1-R2)xVol]", "Qualidade Linear"],
                        value=["Sharpe"],
                        label="Objetivos"
                    )

            with gr.Row():
                auto_rank_min = gr.Number(value=0, label="Score Ranking Min", precision=0)
                auto_rank_max = gr.Number(value=100, label="Score Ranking Max", precision=0)
                auto_weight_min = gr.Number(value=0, label="Peso Min (%)", precision=0)
                auto_weight_max = gr.Number(value=30, label="Peso Max (%)", precision=0)

            btn_auto = gr.Button("INICIAR AUTO-OTIMIZACAO", variant="primary", size="lg")
            status_auto = gr.Textbox(label="Status", interactive=False)
            auto_results = gr.Dataframe(label="Resultados (ordenados por Sharpe)", interactive=False)

        # ===== ABA 5: AJUDA =====
        with gr.Tab("Ajuda"):
            gr.Markdown("""
## Como Usar o Otimizador de Portfolio v3.0

### Passo 1: Carregar Dados
- **Exemplos**: Datasets pre-carregados (acoes BR, FIIs, fundos, ETFs, cripto)
- **Upload**: Sua propria planilha Excel (formato: Data | Taxa Ref | Ativo1 | Ativo2 | ...)
- **Yahoo Finance**: Busca dados online em tempo real

### Passo 2: Definir Periodo
- **Inicio/Fim Otimizacao**: Periodo de treinamento (recomendado: ~70% dos dados)
- **Fim da Analise**: Periodo de validacao/forward test (recomendado: ~30%)
- **Ranking**: Classifica ativos por qualidade (inclinacao + estabilidade + correlacao)

### Passo 3: Otimizar
- Selecione ativos e objetivo (Sharpe, Sortino, MinRisco, etc.)
- Configure pesos minimos/maximos
- Opcionalmente habilite posicoes short

### Passo 4: Auto-Otimizacao (Avancado)
- Testa multiplas combinacoes automaticamente
- Walk-forward: treina e valida em periodos deslizantes
- Encontra a melhor configuracao historica

### Objetivos de Otimizacao

| Objetivo | Descricao |
|----------|-----------|
| Sharpe Ratio | Retorno ajustado ao risco (classico) |
| Sortino Ratio | Retorno ajustado ao risco negativo |
| Minimizar Risco | Menor volatilidade possivel |
| Maximizar Inclinacao | Tendencia de crescimento |
| Inc/[(1-R2)xVol] | Qualidade da tendencia |
| Qualidade Linear | Linearidade do retorno |
| Linearidade Excesso | Linearidade do excesso sobre referencia |

### Metricas Principais

- **Retorno Total/Anual**: Performance do portfolio
- **Volatilidade**: Risco anualizado
- **Sharpe/Sortino**: Retorno por unidade de risco
- **R2**: Qualidade da tendencia linear
- **VaR/CVaR**: Risco de perda extrema
            """)

        # ===== CONECTAR EVENTOS =====

        # Processar periodo -> atualiza selecao de ativos
        btn_processar.click(
            processar_periodo_handler,
            inputs=[periodo_inicio, periodo_fim, periodo_analise, usar_validacao, state],
            outputs=[state, status_periodo, selected_assets, short_assets]
        )

        # Ranking
        btn_ranking.click(
            calcular_ranking_handler,
            inputs=[rank_score_min, rank_score_max, peso_inc, peso_desv, peso_cor, state],
            outputs=[state, ranking_table, status_ranking]
        )

        # Otimizacao
        btn_otimizar.click(
            otimizar_portfolio_handler,
            inputs=[selected_assets, objective, min_weight, max_weight,
                    use_short, short_assets, short_weight, state],
            outputs=[state, status_otim, metricas_insample, composicao_df,
                     tabela_mensal, grafico_insample, grafico_completo,
                     metricas_outsample, comparacao_df]
        )

        # Auto-otimizacao
        btn_auto.click(
            auto_otimizar_handler,
            inputs=[auto_otim, auto_rebal, auto_obj,
                    auto_rank_min, auto_rank_max, auto_weight_min, auto_weight_max, state],
            outputs=[status_auto, auto_results]
        )

    return app


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
