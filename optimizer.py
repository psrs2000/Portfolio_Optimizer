import numpy as np
import pandas as pd
from scipy.optimize import minimize

class PortfolioOptimizer:
    def __init__(self, returns_data, selected_assets=None):
        """
        Inicializa o otimizador com dados de retorno
        returns_data: DataFrame com retornos dos ativos (base 0)
        selected_assets: Lista de ativos selecionados (None = todos)
        """
        self.original_data = returns_data.copy()  # Preservar dados originais com datas
        
        # Assumir que primeira coluna é data, resto são ativos
        if isinstance(returns_data.columns[0], str) and 'data' in returns_data.columns[0].lower():
            self.dates = pd.to_datetime(returns_data.iloc[:, 0])  # Guardar datas
            
            # Verificar se segunda coluna é Taxa Livre de Risco
            if len(returns_data.columns) > 2 and isinstance(returns_data.columns[1], str) and any(
                term in returns_data.columns[1].lower() for term in ['taxa', 'livre', 'risco', 'risk', 'free', 'cdi', 'selic']
            ):
                self.risk_free_returns = returns_data.iloc[:, 1].apply(pd.to_numeric, errors='coerce')  # Coluna B
                self.returns_data = returns_data.iloc[:, 2:]  # Ativos começam na coluna C
                # Calcular taxa livre de risco acumulada
                self.risk_free_cumulative = np.cumsum(self.risk_free_returns.dropna())
                if len(self.risk_free_cumulative) > 0:
                    self.risk_free_rate_total = self.risk_free_cumulative.iloc[-1]
                else:
                    self.risk_free_rate_total = 0.0
            else:
                self.risk_free_returns = None
                self.risk_free_cumulative = None
                self.risk_free_rate_total = 0.0
                self.returns_data = returns_data.iloc[:, 1:]  # Remove coluna de data
        else:
            self.returns_data = returns_data
            self.dates = None
            self.risk_free_returns = None
            self.risk_free_cumulative = None
            self.risk_free_rate_total = 0.0
        
        # Converter para numérico e remover NaNs
        self.returns_data = self.returns_data.apply(pd.to_numeric, errors='coerce').dropna()
        
        # Se temos datas, precisamos sincronizá-las com os dados após dropna
        if self.dates is not None:
            # Pegar os índices que sobraram após dropna
            valid_indices = self.returns_data.index
            self.dates = self.dates.iloc[valid_indices].reset_index(drop=True)
            self.returns_data = self.returns_data.reset_index(drop=True)
            
            # Sincronizar risk_free_returns também se existir
            if self.risk_free_returns is not None:
                self.risk_free_returns = self.risk_free_returns.iloc[valid_indices].reset_index(drop=True)
                # Recalcular acumulado com dados sincronizados
                self.risk_free_cumulative = np.cumsum(self.risk_free_returns)
                self.risk_free_rate_total = self.risk_free_cumulative.iloc[-1] if len(self.risk_free_cumulative) > 0 else 0.0
        
        # Se há ativos selecionados, filtrar apenas esses
        if selected_assets is not None:
            self.returns_data = self.returns_data[selected_assets]
        
        self.assets = self.returns_data.columns.tolist()
        self.n_assets = len(self.assets)
        self.n_periods = len(self.returns_data)
        
        print(f"Otimizador inicializado com {self.n_assets} ativos selecionados e {self.n_periods} períodos")
        if self.risk_free_rate_total > 0:
            print(f"Taxa livre de risco detectada: {self.risk_free_rate_total:.2%}")
    
    def calculate_portfolio_metrics(self, weights, risk_free_rate=0.0):
        """
        Calcula métricas do portfólio (EXATAMENTE como na planilha)
        weights: pesos do portfólio
        risk_free_rate: taxa livre de risco ACUMULADA do período (ex: 0.12 para 12%)
        """
        # Garante que weights é array numpy
        weights = np.array(weights)
        
        # COLUNA GU: Retornos diários do portfólio (SOMARPRODUTO de cada linha pelos pesos)
        portfolio_returns_daily = np.dot(self.returns_data.values, weights)
        
        # COLUNA GV: Retornos acumulados do portfólio (soma cumulativa da GU)
        portfolio_cumulative = np.cumsum(portfolio_returns_daily)
        
        # HC5: Volatilidade anualizada (DESVPAD.P da coluna GU * RAIZ(252))
        portfolio_vol = np.std(portfolio_returns_daily, ddof=0) * np.sqrt(252)
        
        # GV_final: Último valor da coluna GV (retorno acumulado total)
        gv_final = portfolio_cumulative[-1]
        
        # HC8: Sharpe ratio CORRIGIDO com taxa livre de risco
        # Fórmula: (Retorno Total - Taxa Livre de Risco) / Volatilidade
        excess_return = gv_final - risk_free_rate
        sharpe_ratio = excess_return / portfolio_vol if portfolio_vol > 0 else 0
        
        # Retorno anualizado (para comparação)
        annual_return = (1 + gv_final) ** (252 / self.n_periods) - 1
        
        # VaR (Value at Risk) - Método Paramétrico
        # VaR diário
        mean_daily_return = np.mean(portfolio_returns_daily)
        std_daily_return = np.std(portfolio_returns_daily, ddof=0)
        
        # VaR 95% (1.65 desvios padrão) e 99% (2.33 desvios padrão)
        var_95_daily = mean_daily_return - 1.65 * std_daily_return
        var_99_daily = mean_daily_return - 2.33 * std_daily_return
        
        # VaR anualizado (multiplicar pelo sqrt(252) para volatilidade anual)
        var_95_annual = mean_daily_return * 252 - 1.65 * std_daily_return * np.sqrt(252)
        var_99_annual = mean_daily_return * 252 - 2.33 * std_daily_return * np.sqrt(252)
        
        # HC10: Métrica de qualidade da tendência
        try:
            from scipy import stats
            # Criar array de "dias" (índices numéricos representando datas)
            days_numeric = np.arange(len(portfolio_cumulative))
            
            # Regressão linear: GV vs Tempo
            slope, intercept, r_value, p_value, std_err = stats.linregress(days_numeric, portfolio_cumulative)
            r_squared = r_value ** 2
            
            # HC10 = Inclinação / [Volatilidade × (1 - R²)]
            if portfolio_vol > 0 and r_squared < 1:
                hc10 = slope / (portfolio_vol * (1 - r_squared))
            else:
                hc10 = 0
                
        except Exception as e:
            print(f"Erro no cálculo HC10: {e}")
            hc10 = 0
            r_squared = 0
            slope = 0
        
        # NOVO: Métricas do EXCESSO DE RETORNO (v2.1)
        excess_slope = 0
        excess_r_squared = 0
        excess_hc10 = 0
        excess_cumulative = None
        
        if hasattr(self, 'risk_free_cumulative') and self.risk_free_cumulative is not None:
            try:
                # Calcular excesso acumulado diário
                excess_cumulative = portfolio_cumulative - self.risk_free_cumulative.values
                
                # Regressão linear do EXCESSO
                excess_slope, excess_intercept, excess_r_value, _, _ = stats.linregress(days_numeric, excess_cumulative)
                excess_r_squared = excess_r_value ** 2
                
                # Volatilidade do excesso diário
                excess_returns_daily = portfolio_returns_daily - self.risk_free_returns.values
                excess_vol = np.std(excess_returns_daily, ddof=0) * np.sqrt(252)
                
                # HC10 do excesso
                if excess_vol > 0 and excess_r_squared < 1:
                    excess_hc10 = excess_slope / (excess_vol * (1 - excess_r_squared))
                else:
                    excess_hc10 = 0
                    
            except Exception as e:
                print(f"Erro no cálculo de métricas do excesso: {e}")
        
        return {
            'gv_final': gv_final,
            'annual_return': annual_return,
            'volatility': portfolio_vol,
            'sharpe_ratio': sharpe_ratio,
            'excess_return': excess_return,
            'risk_free_rate': risk_free_rate,
            'hc10': hc10,
            'portfolio_returns_daily': portfolio_returns_daily,
            'portfolio_cumulative': portfolio_cumulative,
            'r_squared': r_squared,
            'slope': slope,
            'var_95_daily': var_95_daily,
            'var_99_daily': var_99_daily,
            'var_95_annual': var_95_annual,
            'var_99_annual': var_99_annual,
            # Novas métricas do excesso
            'excess_slope': excess_slope,
            'excess_r_squared': excess_r_squared,
            'excess_hc10': excess_hc10,
            'excess_cumulative': excess_cumulative
        }
    
    def optimize_portfolio(self, objective_type='sharpe', target_return=None, max_weight=1.0, risk_free_rate=0.0):
        """
        Otimiza o portfólio (substitui o Solver do Excel)
        risk_free_rate: taxa livre de risco acumulada do período
        """
        
        def objective_function(weights):
            metrics = self.calculate_portfolio_metrics(weights, risk_free_rate)
            
            if objective_type == 'sharpe':
                # Maximizar Sharpe (minimizar -Sharpe)
                return -metrics['sharpe_ratio']
            elif objective_type == 'volatility':
                # Minimizar volatilidade
                return metrics['volatility']
            elif objective_type == 'slope':
                # Maximizar Inclinação (minimizar -Inclinação)
                return -metrics['slope']
            elif objective_type == 'hc10':
                # Maximizar Inclinação/(1-R²)×Vol 
                # Mas para estabilidade, minimizamos o inverso: (1-R²)×Vol/Inclinação
                if metrics['volatility'] > 0 and metrics['r_squared'] < 1:
                    if metrics['slope'] > 0.000001:  # Inclinação positiva pequena
                        # Retornar o inverso para minimizar
                        return (1 - metrics['r_squared']) * metrics['volatility'] / metrics['slope']
                    elif metrics['slope'] < -0.000001:  # Inclinação negativa
                        # Penalizar fortemente inclinações negativas
                        return 1e10 - metrics['slope']  # Quanto mais negativo, pior
                    else:  # Inclinação muito próxima de zero
                        return 1e10
                else:
                    # Valor alto para penalizar casos inválidos
                    return 1e10
            elif objective_type == 'excess_hc10':
                # NOVO: Maximizar linearidade do EXCESSO de retorno
                if not hasattr(self, 'risk_free_cumulative') or self.risk_free_cumulative is None:
                    # Se não tem taxa livre, retornar erro alto
                    return 1e10
                
                # Calcular métricas incluindo excesso
                if metrics.get('excess_slope') is not None:
                    # Calcular volatilidade do excesso aqui para usar no objetivo
                    excess_returns_daily = metrics['portfolio_returns_daily'] - self.risk_free_returns.values
                    excess_vol = np.std(excess_returns_daily, ddof=0) * np.sqrt(252)
                    
                    if metrics['excess_slope'] > 0.000001 and excess_vol > 0 and metrics['excess_r_squared'] < 1:
                        # Retornar o inverso para minimizar
                        return (1 - metrics['excess_r_squared']) * excess_vol / metrics['excess_slope']
                    else:
                        # Penalizar casos ruins (inclinação negativa, zero ou vol zero)
                        if metrics['excess_slope'] <= 0:
                            # Quanto mais negativa a inclinação, pior
                            return 1e10 + abs(metrics['excess_slope']) * 1e6
                        else:
                            return 1e10
                else:
                    return 1e10
            elif objective_type == 'return':
                # Maximizar retorno (minimizar -retorno)
                return -metrics['annual_return']
        
        # Restrições
        constraints = [
            # Soma dos pesos = 1 (100%)
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        # Limites para cada peso (0% a max_weight%)
        bounds = tuple((0, max_weight) for _ in range(self.n_assets))
        
        # Chute inicial (pesos iguais)
        initial_weights = np.array([1/self.n_assets] * self.n_assets)
        
        # Otimização (aqui é onde a mágica acontece!)
        try:
            result = minimize(
                objective_function,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000, 'ftol': 1e-9}
            )
            
            if result.success:
                optimal_weights = result.x
                metrics = self.calculate_portfolio_metrics(optimal_weights, risk_free_rate)
                
                return {
                    'success': True,
                    'weights': optimal_weights,
                    'metrics': metrics,
                    'assets': self.assets
                }
            else:
                return {
                    'success': False,
                    'message': f"Otimização falhou: {result.message}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Erro na otimização: {str(e)}"
            }
    
    def get_portfolio_summary(self, weights):
        """
        Cria resumo do portfólio otimizado
        """
        # Filtrar apenas pesos significativos (> 0.1%)
        significant_weights = weights > 0.001
        
        portfolio_df = pd.DataFrame({
            'Ativo': np.array(self.assets)[significant_weights],
            'Peso (%)': weights[significant_weights] * 100
        }).sort_values('Peso (%)', ascending=False)
        
        return portfolio_df
