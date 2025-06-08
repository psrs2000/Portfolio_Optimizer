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
        # Assumir que primeira coluna é data, resto são ativos
        if isinstance(returns_data.columns[0], str) and 'data' in returns_data.columns[0].lower():
            self.returns_data = returns_data.iloc[:, 1:]  # Remove coluna de data
        else:
            self.returns_data = returns_data
        
        # Converter para numérico e remover NaNs
        self.returns_data = self.returns_data.apply(pd.to_numeric, errors='coerce').dropna()
        
        # Se há ativos selecionados, filtrar apenas esses
        if selected_assets is not None:
            self.returns_data = self.returns_data[selected_assets]
        
        self.assets = self.returns_data.columns.tolist()
        self.n_assets = len(self.assets)
        self.n_periods = len(self.returns_data)
        
        print(f"Otimizador inicializado com {self.n_assets} ativos selecionados e {self.n_periods} períodos")
    
    def calculate_portfolio_metrics(self, weights):
        """
        Calcula métricas do portfólio (EXATAMENTE como na planilha)
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
        
        # HC8: Sharpe ratio (GV_final / HC5, assumindo risk-free = 0)
        sharpe_ratio = gv_final / portfolio_vol if portfolio_vol > 0 else 0
        
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
        
        return {
            'gv_final': gv_final,
            'annual_return': annual_return,
            'volatility': portfolio_vol,
            'sharpe_ratio': sharpe_ratio,
            'hc10': hc10,
            'portfolio_returns_daily': portfolio_returns_daily,
            'portfolio_cumulative': portfolio_cumulative,
            'r_squared': r_squared,
            'slope': slope,
            'var_95_daily': var_95_daily,
            'var_99_daily': var_99_daily,
            'var_95_annual': var_95_annual,
            'var_99_annual': var_99_annual
        }
    
    def optimize_portfolio(self, objective_type='sharpe', target_return=None, max_weight=1.0):
        """
        Otimiza o portfólio (substitui o Solver do Excel)
        """
        
        def objective_function(weights):
            metrics = self.calculate_portfolio_metrics(weights)
            
            if objective_type == 'sharpe':
                # Maximizar Sharpe (minimizar -Sharpe)
                return -metrics['sharpe_ratio']
            elif objective_type == 'volatility':
                # Minimizar volatilidade
                return metrics['volatility']
            elif objective_type == 'hc10':
                # Maximizar HC10 (minimizar -HC10)
                return -metrics['hc10']
            elif objective_type == 'return':
                # Maximizar retorno (minimizar -retorno)
                return -metrics['annual_return']
        
        # Restrições
        constraints = [
            # Soma dos pesos = 1 (100%)
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        # Remover restrição de target_return (não usamos mais)
        
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
                metrics = self.calculate_portfolio_metrics(optimal_weights)
                
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