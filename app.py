import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import sys
from datetime import datetime

# Importar sua classe original (sem modificações!)
from optimizer import PortfolioOptimizer

class PortfolioOptimizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 Otimizador de Portfólio - Versão Desktop Completa")
        self.root.geometry("1400x900")
        
        # Variáveis de dados
        self.df = None
        self.optimizer = None
        self.result = None
        self.has_risk_free = False
        self.risk_free_column_name = None
        self.detected_risk_free_rate = 0.0
        
        # Variáveis para restrições individuais
        self.individual_constraints = {}
        self.constraint_widgets = {}
        
        # Variáveis para short selling
        self.short_weights = {}
        self.short_widgets = {}
        
        # NOVO: Variáveis para tabelas mensais
        self.monthly_table = None
        self.excess_table = None
        
        # Configurar interface
        self.setup_ui()
        
    def setup_ui(self):
        """Criar interface do usuário"""
        # Notebook para organizar abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Aba 1: Carregar Dados
        self.tab_data = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="📁 Dados")
        self.setup_data_tab()
        
        # Aba 2: Configuração Básica
        self.tab_config = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_config, text="⚙️ Configuração")
        self.setup_config_tab()
        
        # Aba 3: Restrições Avançadas
        self.tab_advanced = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_advanced, text="🔧 Avançado")
        self.setup_advanced_tab()
        
        # Aba 4: Short Selling
        self.tab_short = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_short, text="🔄 Short/Hedge")
        self.setup_short_tab()
        
        # Aba 5: Resultados
        self.tab_results = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_results, text="📈 Resultados")
        self.setup_results_tab()
        
        # NOVA Aba 6: Tabelas Mensais
        self.tab_monthly = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_monthly, text="📅 Retornos Mensais")
        self.setup_monthly_tab()
        
    def setup_data_tab(self):
        """Configurar aba de carregamento de dados"""
        frame = ttk.LabelFrame(self.tab_data, text="Carregar Dados", padding="10")
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Botão para carregar arquivo
        ttk.Button(
            frame, 
            text="📂 Carregar Planilha Excel", 
            command=self.load_excel_file,
            width=30
        ).pack(pady=10)
        
        # Frame para mostrar info do arquivo
        self.info_frame = ttk.LabelFrame(frame, text="Informações do Arquivo")
        self.info_frame.pack(fill='both', expand=True, pady=10)
        
        # Label para mostrar status
        self.status_label = ttk.Label(self.info_frame, text="Nenhum arquivo carregado")
        self.status_label.pack(pady=5)
        
        # Frame para taxa de referência detectada
        self.risk_free_frame = ttk.LabelFrame(self.info_frame, text="Taxa de Referência Detectada")
        self.risk_free_frame.pack(fill='x', pady=10)
        
        self.risk_free_info = ttk.Label(self.risk_free_frame, text="Nenhuma taxa detectada")
        self.risk_free_info.pack(pady=5)
        
        # Listbox para seleção de ativos
        ttk.Label(self.info_frame, text="Selecione os ativos (Ctrl+clique para múltiplos):").pack(anchor='w', pady=(10,5))
        
        # Frame para listbox com scrollbar
        listbox_frame = ttk.Frame(self.info_frame)
        listbox_frame.pack(fill='both', expand=True, pady=5)
        
        self.assets_listbox = tk.Listbox(listbox_frame, selectmode='extended')
        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.assets_listbox.yview)
        self.assets_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.assets_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botões de seleção rápida
        button_frame = ttk.Frame(self.info_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Selecionar Todos", command=self.select_all_assets).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Limpar Seleção", command=self.clear_selection).pack(side='left', padx=5)
        
    def setup_config_tab(self):
        """Configurar aba de configurações básicas"""
        # Frame principal com scroll
        canvas = tk.Canvas(self.tab_config)
        scrollbar = ttk.Scrollbar(self.tab_config, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 1. Objetivo de Otimização
        obj_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Objetivo de Otimização", padding="10")
        obj_frame.pack(fill='x', padx=10, pady=5)
        
        self.objective_var = tk.StringVar(value="Maximizar Sharpe Ratio")
        
        # Lista COMPLETA de objetivos (como no Streamlit)
        self.base_objectives = [
            "Maximizar Sharpe Ratio",
            "Maximizar Sortino Ratio", 
            "Minimizar Risco",
            "Maximizar Inclinação",
            "Maximizar Inclinação/[(1-R²)×Vol]"
        ]
        
        # Objetivos que dependem de taxa livre serão adicionados dinamicamente
        self.risk_free_objectives = [
            "Maximizar Qualidade da Linearidade",
            "Maximizar Linearidade do Excesso"
        ]
        
        # Criar radiobuttons para objetivos base
        self.objective_buttons = {}
        for obj in self.base_objectives:
            btn = ttk.Radiobutton(obj_frame, text=obj, variable=self.objective_var, value=obj)
            btn.pack(anchor='w')
            self.objective_buttons[obj] = btn
        
        # Placeholder para objetivos de taxa livre
        self.risk_free_obj_frame = ttk.Frame(obj_frame)
        self.risk_free_obj_frame.pack(fill='x', pady=(10,0))
        
        # 2. Limites de Peso Globais
        limits_frame = ttk.LabelFrame(scrollable_frame, text="📊 Limites de Peso Globais", padding="10")
        limits_frame.pack(fill='x', padx=10, pady=5)
        
        # Min weight
        min_frame = ttk.Frame(limits_frame)
        min_frame.pack(fill='x', pady=2)
        ttk.Label(min_frame, text="Peso mínimo por ativo (%):").pack(side='left')
        self.min_weight_var = tk.DoubleVar(value=0.0)
        self.min_weight_label = ttk.Label(min_frame, text="0.0%")
        self.min_weight_label.pack(side='right')
        scale_min = ttk.Scale(limits_frame, from_=0, to=20, variable=self.min_weight_var, orient='horizontal',
                             command=lambda v: self.min_weight_label.config(text=f"{float(v):.1f}%"))
        scale_min.pack(fill='x', pady=2)
        
        # Max weight  
        max_frame = ttk.Frame(limits_frame)
        max_frame.pack(fill='x', pady=2)
        ttk.Label(max_frame, text="Peso máximo por ativo (%):").pack(side='left')
        self.max_weight_var = tk.DoubleVar(value=30.0)
        self.max_weight_label = ttk.Label(max_frame, text="30.0%")
        self.max_weight_label.pack(side='right')
        scale_max = ttk.Scale(limits_frame, from_=5, to=100, variable=self.max_weight_var, orient='horizontal',
                             command=lambda v: self.max_weight_label.config(text=f"{float(v):.1f}%"))
        scale_max.pack(fill='x', pady=2)
        
        # 3. Taxa Livre de Risco
        risk_frame = ttk.LabelFrame(scrollable_frame, text="🏛️ Taxa de Referência", padding="10")
        risk_frame.pack(fill='x', padx=10, pady=5)
        
        # Frame para taxa detectada vs manual
        self.risk_free_display_frame = ttk.Frame(risk_frame)
        self.risk_free_display_frame.pack(fill='x')
        
        # Taxa manual (será escondida se detectar automaticamente)
        manual_frame = ttk.Frame(risk_frame)
        manual_frame.pack(fill='x', pady=5)
        ttk.Label(manual_frame, text="Taxa de referência manual (% acumulada):").pack(anchor='w')
        self.risk_free_var = tk.DoubleVar(value=0.0)
        self.manual_risk_entry = ttk.Entry(manual_frame, textvariable=self.risk_free_var, width=10)
        self.manual_risk_entry.pack(anchor='w', pady=2)
        
        # 4. Botão Otimizar
        ttk.Button(
            scrollable_frame, 
            text="🚀 OTIMIZAR PORTFÓLIO", 
            command=self.optimize_portfolio,
            style="Accent.TButton"
        ).pack(pady=20, ipadx=20, ipady=10)
        
        # Empacotar canvas e scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_advanced_tab(self):
        """Configurar aba de restrições individuais"""
        frame = ttk.LabelFrame(self.tab_advanced, text="🚫 Restrições Individuais por Ativo", padding="10")
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Checkbox para habilitar restrições
        self.use_individual_constraints = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, 
            text="Habilitar limites específicos para ativos selecionados", 
            variable=self.use_individual_constraints,
            command=self.toggle_individual_constraints
        ).pack(anchor='w', pady=5)
        
        # Frame para scroll das restrições
        self.constraints_canvas = tk.Canvas(frame)
        constraints_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.constraints_canvas.yview)
        self.constraints_frame = ttk.Frame(self.constraints_canvas)
        
        self.constraints_frame.bind(
            "<Configure>",
            lambda e: self.constraints_canvas.configure(scrollregion=self.constraints_canvas.bbox("all"))
        )
        
        self.constraints_canvas.create_window((0, 0), window=self.constraints_frame, anchor="nw")
        self.constraints_canvas.configure(yscrollcommand=constraints_scrollbar.set)
        
        self.constraints_canvas.pack(side="left", fill="both", expand=True, pady=10)
        constraints_scrollbar.pack(side="right", fill="y")
        
        # Label inicial
        self.constraints_info = ttk.Label(self.constraints_frame, text="Carregue dados e selecione ativos primeiro")
        self.constraints_info.pack(pady=20)
        
    def setup_short_tab(self):
        """Configurar aba de short selling"""
        frame = ttk.LabelFrame(self.tab_short, text="🔄 Posições Short / Hedge", padding="10")
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Checkbox para habilitar shorts
        self.use_short = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, 
            text="Habilitar posições short/hedge (venda a descoberto)", 
            variable=self.use_short,
            command=self.toggle_short_selling
        ).pack(anchor='w', pady=5)
        
        # Frame para scroll dos shorts
        self.short_canvas = tk.Canvas(frame)
        short_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.short_canvas.yview)
        self.short_frame = ttk.Frame(self.short_canvas)
        
        self.short_frame.bind(
            "<Configure>",
            lambda e: self.short_canvas.configure(scrollregion=self.short_canvas.bbox("all"))
        )
        
        self.short_canvas.create_window((0, 0), window=self.short_frame, anchor="nw")
        self.short_canvas.configure(yscrollcommand=short_scrollbar.set)
        
        self.short_canvas.pack(side="left", fill="both", expand=True, pady=10)
        short_scrollbar.pack(side="right", fill="y")
        
        # Label inicial
        self.short_info = ttk.Label(self.short_frame, text="Carregue dados e selecione ativos principais primeiro")
        self.short_info.pack(pady=20)
        
    def setup_results_tab(self):
        """Configurar aba de resultados"""
        # PanedWindow para dividir em seções
        paned = ttk.PanedWindow(self.tab_results, orient='vertical')
        paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Frame superior para métricas
        metrics_frame = ttk.LabelFrame(paned, text="📊 Métricas do Portfólio", padding="10")
        paned.add(metrics_frame, weight=1)
        
        # Text widget para métricas
        self.metrics_text = scrolledtext.ScrolledText(metrics_frame, height=15, wrap='word')
        self.metrics_text.pack(fill='both', expand=True)
        
        # Frame inferior dividido
        bottom_paned = ttk.PanedWindow(paned, orient='horizontal')
        paned.add(bottom_paned, weight=2)
        
        # Frame para composição
        composition_frame = ttk.LabelFrame(bottom_paned, text="📋 Composição do Portfólio", padding="10")
        bottom_paned.add(composition_frame, weight=1)
        
        # NOVO: Botões de exportação
        export_frame = ttk.Frame(composition_frame)
        export_frame.pack(fill='x', pady=(0,10))
        
        self.export_csv_btn = ttk.Button(export_frame, text="💾 Exportar CSV", command=self.export_csv)
        self.export_csv_btn.pack(side='left', padx=(0,5))
        
        self.export_excel_btn = ttk.Button(export_frame, text="📊 Exportar Excel", command=self.export_excel)
        self.export_excel_btn.pack(side='left')
        
        self.export_csv_btn.config(state='disabled')
        self.export_excel_btn.config(state='disabled')
        
        # Treeview para mostrar pesos
        columns = ('Ativo', 'Peso (%)')
        self.portfolio_tree = ttk.Treeview(composition_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.portfolio_tree.heading(col, text=col)
            self.portfolio_tree.column(col, width=120)
        
        # Scrollbar para treeview
        tree_scroll = ttk.Scrollbar(composition_frame, orient='vertical', command=self.portfolio_tree.yview)
        self.portfolio_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.portfolio_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        # Frame para gráfico
        chart_frame = ttk.LabelFrame(bottom_paned, text="📈 Evolução do Portfólio", padding="10")
        bottom_paned.add(chart_frame, weight=2)
        
        # Placeholder para gráfico matplotlib
        self.chart_frame = chart_frame
        
    def setup_monthly_tab(self):
        """NOVA: Configurar aba de tabelas mensais"""
        # Frame principal com scroll
        main_frame = ttk.Frame(self.tab_monthly)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Notebook interno para tabelas
        self.monthly_notebook = ttk.Notebook(main_frame)
        self.monthly_notebook.pack(fill='both', expand=True)
        
        # Aba 1: Retornos do Portfólio
        self.tab_portfolio_monthly = ttk.Frame(self.monthly_notebook)
        self.monthly_notebook.add(self.tab_portfolio_monthly, text="📊 Retornos do Portfólio")
        
        # Frame com scroll para tabela do portfólio
        canvas1 = tk.Canvas(self.tab_portfolio_monthly)
        scrollbar1 = ttk.Scrollbar(self.tab_portfolio_monthly, orient="vertical", command=canvas1.yview)
        scrollable_frame1 = ttk.Frame(canvas1)
        
        scrollable_frame1.bind("<Configure>", lambda e: canvas1.configure(scrollregion=canvas1.bbox("all")))
        canvas1.create_window((0, 0), window=scrollable_frame1, anchor="nw")
        canvas1.configure(yscrollcommand=scrollbar1.set)
        
        self.portfolio_monthly_frame = scrollable_frame1
        
        canvas1.pack(side="left", fill="both", expand=True)
        scrollbar1.pack(side="right", fill="y")
        
        # Aba 2: Excesso de Retorno
        self.tab_excess_monthly = ttk.Frame(self.monthly_notebook)
        self.monthly_notebook.add(self.tab_excess_monthly, text="📈 Excesso de Retorno")
        
        # Frame com scroll para tabela do excesso
        canvas2 = tk.Canvas(self.tab_excess_monthly)
        scrollbar2 = ttk.Scrollbar(self.tab_excess_monthly, orient="vertical", command=canvas2.yview)
        scrollable_frame2 = ttk.Frame(canvas2)
        
        scrollable_frame2.bind("<Configure>", lambda e: canvas2.configure(scrollregion=canvas2.bbox("all")))
        canvas2.create_window((0, 0), window=scrollable_frame2, anchor="nw")
        canvas2.configure(yscrollcommand=scrollbar2.set)
        
        self.excess_monthly_frame = scrollable_frame2
        
        canvas2.pack(side="left", fill="both", expand=True)
        scrollbar2.pack(side="right", fill="y")
        
        # Labels iniciais
        ttk.Label(self.portfolio_monthly_frame, text="Execute uma otimização para ver as tabelas mensais").pack(pady=20)
        ttk.Label(self.excess_monthly_frame, text="Execute uma otimização para ver as tabelas mensais").pack(pady=20)
        
    def create_monthly_returns_table(self, returns_data, weights, dates=None, risk_free_returns=None):
        """Criar tabela de retornos mensais do portfólio otimizado"""
        # Calcular retornos diários do portfólio
        portfolio_returns_daily = np.dot(returns_data.values, weights)
        
        # Criar DataFrame com retornos diários
        portfolio_df = pd.DataFrame({
            'returns': portfolio_returns_daily
        }, index=range(len(portfolio_returns_daily)))
        
        # Adicionar taxa livre se disponível
        if risk_free_returns is not None:
            portfolio_df['risk_free'] = risk_free_returns.values
        
        # Usar datas reais se disponíveis, senão simular
        if dates is not None:
            portfolio_df.index = dates
        else:
            # Simular datas (assumindo dados diários consecutivos)
            start_date = pd.Timestamp('2020-01-01')
            dates = pd.date_range(start=start_date, periods=len(portfolio_returns_daily), freq='D')
            portfolio_df.index = dates
        
        # Calcular retornos mensais
        # Converter retornos diários para retornos compostos mensais
        portfolio_df['returns_factor'] = 1 + portfolio_df['returns']
        monthly_returns = portfolio_df['returns_factor'].resample('M').prod() - 1
        
        # Calcular retornos mensais da taxa livre se disponível
        if risk_free_returns is not None:
            portfolio_df['risk_free_factor'] = 1 + portfolio_df['risk_free']
            monthly_risk_free = portfolio_df['risk_free_factor'].resample('M').prod() - 1
        
        # Criar tabela pivotada (anos x meses)
        monthly_df = pd.DataFrame({
            'Year': monthly_returns.index.year,
            'Month': monthly_returns.index.month,
            'Return': monthly_returns.values
        })
        
        # Pivotar para ter anos nas linhas e meses nas colunas
        pivot_table = monthly_df.pivot(index='Year', columns='Month', values='Return')
        
        # Renomear colunas para nomes dos meses
        month_names = {
            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
        }
        pivot_table.columns = [month_names.get(col, f'M{col}') for col in pivot_table.columns]
        
        # Calcular total anual (soma dos retornos mensais compostos)
        yearly_returns = []
        for year in pivot_table.index:
            year_data = pivot_table.loc[year].dropna()
            if len(year_data) > 0:
                # Retorno anual composto
                annual_return = (1 + year_data).prod() - 1
                yearly_returns.append(annual_return)
            else:
                yearly_returns.append(np.nan)
        
        pivot_table['Total Anual'] = yearly_returns
        
        # Se temos taxa livre, criar tabela comparativa
        comparison_table = None
        if risk_free_returns is not None:
            # Criar tabela similar para taxa livre
            rf_monthly_df = pd.DataFrame({
                'Year': monthly_risk_free.index.year,
                'Month': monthly_risk_free.index.month,
                'Return': monthly_risk_free.values
            })
            
            rf_pivot = rf_monthly_df.pivot(index='Year', columns='Month', values='Return')
            rf_pivot.columns = [month_names.get(col, f'M{col}') for col in rf_pivot.columns]
            
            # Calcular total anual da taxa livre
            rf_yearly = []
            for year in rf_pivot.index:
                year_data = rf_pivot.loc[year].dropna()
                if len(year_data) > 0:
                    annual_return = (1 + year_data).prod() - 1
                    rf_yearly.append(annual_return)
                else:
                    rf_yearly.append(np.nan)
            
            rf_pivot['Total Anual'] = rf_yearly
            
            # Criar tabela de comparação (excesso de retorno)
            comparison_table = pivot_table - rf_pivot
        
        return pivot_table, comparison_table
        
    def display_monthly_tables(self):
        """NOVA: Exibir tabelas de retornos mensais"""
        if not self.result or not self.result['success']:
            return
        
        try:
            # Criar tabelas mensais
            dates = getattr(self.optimizer, 'dates', None)
            risk_free_returns = getattr(self.optimizer, 'risk_free_returns', None)
            
            self.monthly_table, self.excess_table = self.create_monthly_returns_table(
                self.optimizer.returns_data, 
                self.result['weights'],
                dates,
                risk_free_returns
            )
            
            # Limpar frames anteriores
            for widget in self.portfolio_monthly_frame.winfo_children():
                widget.destroy()
            for widget in self.excess_monthly_frame.winfo_children():
                widget.destroy()
            
            # Criar tabela do portfólio
            self.create_table_widget(self.portfolio_monthly_frame, self.monthly_table, "Retornos Mensais do Portfólio (%)")
            
            # Criar tabela do excesso se disponível
            if self.excess_table is not None:
                self.create_table_widget(self.excess_monthly_frame, self.excess_table, "Excesso de Retorno Mensal (%)")
            else:
                ttk.Label(self.excess_monthly_frame, text="Não disponível (sem taxa de referência detectada)").pack(pady=20)
                
        except Exception as e:
            ttk.Label(self.portfolio_monthly_frame, text=f"Erro ao gerar tabelas: {str(e)}").pack(pady=20)
            ttk.Label(self.excess_monthly_frame, text=f"Erro ao gerar tabelas: {str(e)}").pack(pady=20)
    
    def create_table_widget(self, parent, data_df, title):
        """Criar widget de tabela com cores para uma DataFrame"""
        # Título
        ttk.Label(parent, text=title, font=('TkDefaultFont', 12, 'bold')).pack(pady=(10,5))
        
        # Frame para tabela
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Preparar dados formatados
        display_data = data_df.copy()
        for col in display_data.columns:
            display_data[col] = display_data[col].apply(
                lambda x: f"{x:.2%}" if pd.notna(x) else "-"
            )
        
        # Criar Treeview
        columns = ['Ano'] + list(display_data.columns)
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        
        # Configurar cabeçalhos
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor='center')
        
        # Inserir dados
        for year, row in display_data.iterrows():
            values = [str(year)] + [str(val) for val in row]
            item = tree.insert('', 'end', values=values)
            
            # Colorir baseado nos valores (aproximação)
            try:
                # Verificar se maioria dos valores são positivos (verde) ou negativos (vermelho)
                numeric_values = []
                for val in row:
                    if val != "-" and pd.notna(val):
                        # Extrair valor numérico da string formatada
                        if isinstance(val, str) and '%' in val:
                            numeric_val = float(val.replace('%', '')) / 100
                        else:
                            numeric_val = float(val)
                        numeric_values.append(numeric_val)
                
                if numeric_values:
                    avg_return = sum(numeric_values) / len(numeric_values)
                    if avg_return > 0:
                        # Configurar tags para cores (se suportado pelo sistema)
                        tree.set(item, 'Ano', f"📈 {year}")
                    elif avg_return < 0:
                        tree.set(item, 'Ano', f"📉 {year}")
            except:
                pass  # Ignorar erros de formatação
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Layout da tabela
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Configurar peso das colunas/linhas
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
    def export_csv(self):
        """Exportar CSV - VERSÃO SUPER SIMPLES"""
        if not self.result or not self.result['success']:
            messagebox.showerror("Erro", "Execute uma otimização primeiro!")
            return
        
        try:
            # Diálogo simples - SEM initialfile
            filename = filedialog.asksaveasfilename(
                title="Salvar CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")]
            )
            
            if filename:
                # Dados simples
                data = []
                for i, asset in enumerate(self.result['assets']):
                    weight = self.result['weights'][i]
                    if abs(weight) > 0.001:
                        data.append([asset, f"{weight*100:.2f}%"])
                
                # Salvar direto
                df = pd.DataFrame(data, columns=['Ativo', 'Peso'])
                df.to_csv(filename, index=False)
                
                messagebox.showinfo("Sucesso", "CSV exportado!")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha: {str(e)}")

    def export_excel(self):
        """Exportar Excel - VERSÃO SUPER SIMPLES"""
        if not self.result or not self.result['success']:
            messagebox.showerror("Erro", "Execute uma otimização primeiro!")
            return
        
        try:
            # Diálogo simples - SEM initialfile
            filename = filedialog.asksaveasfilename(
                title="Salvar Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")]
            )
            
            if filename:
                # Dados simples
                data = []
                for i, asset in enumerate(self.result['assets']):
                    weight = self.result['weights'][i]
                    if abs(weight) > 0.001:
                        data.append([asset, f"{weight*100:.2f}%"])
                
                # Salvar direto
                df = pd.DataFrame(data, columns=['Ativo', 'Peso'])
                df.to_excel(filename, index=False)
                
                messagebox.showinfo("Sucesso", "Excel exportado!")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha: {str(e)}")
    
    def prepare_export_data(self):
        """Preparar dados da composição do portfólio para export"""
        # Obter todos os pesos (incluindo negativos)
        all_weights = self.result['weights']
        export_list = []
        
        for i, asset in enumerate(self.result['assets']):
            weight = all_weights[i]
            if abs(weight) > 0.001:  # Incluir pesos > 0.1%
                export_list.append({
                    'Ativo': asset,
                    'Peso_Decimal': weight,
                    'Peso_Percentual': weight * 100,
                    'Tipo': 'LONG' if weight > 0 else 'SHORT'
                })
        
        return pd.DataFrame(export_list)
    
    def prepare_metrics_export(self):
        """Preparar métricas do portfólio para export"""
        metrics = self.result['metrics']
        
        metrics_list = [
            {'Métrica': 'Retorno Total', 'Valor': metrics['gv_final'], 'Formato': f"{metrics['gv_final']:.4f}"},
            {'Métrica': 'Retorno Anualizado', 'Valor': metrics['annual_return'], 'Formato': f"{metrics['annual_return']:.4f}"},
            {'Métrica': 'Volatilidade', 'Valor': metrics['volatility'], 'Formato': f"{metrics['volatility']:.4f}"},
            {'Métrica': 'Sharpe Ratio', 'Valor': metrics['sharpe_ratio'], 'Formato': f"{metrics['sharpe_ratio']:.4f}"},
            {'Métrica': 'Sortino Ratio', 'Valor': metrics['sortino_ratio'], 'Formato': f"{metrics['sortino_ratio']:.4f}"},
            {'Métrica': 'Downside Deviation', 'Valor': metrics['downside_deviation'], 'Formato': f"{metrics['downside_deviation']:.4f}"},
            {'Métrica': 'Excesso de Retorno', 'Valor': metrics['excess_return'], 'Formato': f"{metrics['excess_return']:.4f}"},
            {'Métrica': 'R²', 'Valor': metrics['r_squared'], 'Formato': f"{metrics['r_squared']:.4f}"},
            {'Métrica': 'VaR 95% Diário', 'Valor': metrics['var_95_daily'], 'Formato': f"{metrics['var_95_daily']:.4f}"},
            {'Métrica': 'CVaR 95% Diário', 'Valor': metrics['cvar_95_daily'], 'Formato': f"{metrics['cvar_95_daily']:.4f}"},
            {'Métrica': 'Taxa de Referência', 'Valor': metrics['risk_free_rate'], 'Formato': f"{metrics['risk_free_rate']:.4f}"},
        ]
        
        # Adicionar métricas do excesso se disponíveis
        if self.objective_var.get() == "Maximizar Linearidade do Excesso" and metrics.get('excess_r_squared') is not None:
            if hasattr(self.optimizer, 'risk_free_returns') and self.optimizer.risk_free_returns is not None:
                excess_returns_daily = metrics['portfolio_returns_daily'] - self.optimizer.risk_free_returns.values
                excess_vol = np.std(excess_returns_daily, ddof=0) * np.sqrt(252)
                
                metrics_list.extend([
                    {'Métrica': 'R² do Excesso', 'Valor': metrics['excess_r_squared'], 'Formato': f"{metrics['excess_r_squared']:.4f}"},
                    {'Métrica': 'Volatilidade do Excesso', 'Valor': excess_vol, 'Formato': f"{excess_vol:.4f}"},
                ])
        
        return pd.DataFrame(metrics_list)
        
    def load_excel_file(self):
        """Carregar arquivo Excel com detecção completa de taxa livre"""
        file_path = filedialog.askopenfilename(
            title="Selecionar planilha Excel",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if file_path:
            try:
                self.df = pd.read_excel(file_path)
                
                # Reset variáveis
                self.has_risk_free = False
                self.risk_free_column_name = None
                self.detected_risk_free_rate = 0.0
                
                # Identificar colunas (mesma lógica do Streamlit)
                if isinstance(self.df.columns[0], str) and 'data' in self.df.columns[0].lower():
                    # Verificar taxa livre de risco na coluna B
                    if len(self.df.columns) > 2 and isinstance(self.df.columns[1], str):
                        col_name = self.df.columns[1].lower()
                        if any(term in col_name for term in ['taxa', 'livre', 'risco', 'ibov', 'ref', 'cdi', 'selic']):
                            self.has_risk_free = True
                            self.risk_free_column_name = self.df.columns[1]
                            asset_columns = self.df.columns[2:].tolist()  # Ativos começam na coluna C
                            
                            # CALCULAR TAXA ACUMULADA (como no Streamlit)
                            try:
                                # Criar um otimizador temporário para calcular a taxa
                                temp_optimizer = PortfolioOptimizer(self.df, [])
                                if hasattr(temp_optimizer, 'risk_free_rate_total'):
                                    self.detected_risk_free_rate = temp_optimizer.risk_free_rate_total
                                    
                            except Exception as e:
                                print(f"Erro ao calcular taxa livre: {e}")
                                self.detected_risk_free_rate = 0.0
                        else:
                            asset_columns = self.df.columns[1:].tolist()  # Ativos começam na coluna B
                    else:
                        asset_columns = self.df.columns[1:].tolist()
                else:
                    asset_columns = self.df.columns.tolist()
                
                # Atualizar interface
                file_name = os.path.basename(file_path)
                status_text = f"✅ Arquivo: {file_name}\nDimensões: {self.df.shape[0]} linhas x {self.df.shape[1]} colunas"
                self.status_label.config(text=status_text)
                
                # Atualizar info da taxa livre
                if self.has_risk_free:
                    risk_text = f"✅ Detectada: '{self.risk_free_column_name}'\nTaxa acumulada: {self.detected_risk_free_rate:.2%}"
                    self.risk_free_info.config(text=risk_text, foreground='green')
                    
                    # Esconder entrada manual e mostrar detectada
                    self.manual_risk_entry.config(state='disabled')
                    
                    # Habilitar objetivos de taxa livre
                    self.update_objective_options()
                else:
                    self.risk_free_info.config(text="❌ Nenhuma taxa detectada", foreground='red')
                    self.manual_risk_entry.config(state='normal')
                
                # Preencher listbox de ativos
                self.assets_listbox.delete(0, tk.END)
                for asset in asset_columns:
                    self.assets_listbox.insert(tk.END, asset)
                    
                # Resetar widgets avançados
                self.update_advanced_widgets()
                    
                messagebox.showinfo("Sucesso", "Arquivo carregado com sucesso!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar arquivo:\n{str(e)}")
                
    def update_objective_options(self):
        """Atualizar opções de objetivo baseado na taxa livre"""
        # Limpar objetivos de taxa livre anteriores
        for widget in self.risk_free_obj_frame.winfo_children():
            widget.destroy()
        
        if self.has_risk_free:
            # Adicionar separador
            ttk.Separator(self.risk_free_obj_frame, orient='horizontal').pack(fill='x', pady=5)
            ttk.Label(self.risk_free_obj_frame, text="Objetivos com Taxa de Referência:", 
                     font=('TkDefaultFont', 9, 'bold')).pack(anchor='w')
            
            # Adicionar objetivos de taxa livre
            for obj in self.risk_free_objectives:
                btn = ttk.Radiobutton(self.risk_free_obj_frame, text=obj, variable=self.objective_var, value=obj)
                btn.pack(anchor='w')
                self.objective_buttons[obj] = btn
    
    def update_advanced_widgets(self):
        """Atualizar widgets de restrições e shorts"""
        self.update_constraints_widgets()
        self.update_short_widgets()
    
    def update_constraints_widgets(self):
        """Atualizar widgets de restrições individuais"""
        # Limpar widgets existentes
        for widget in self.constraints_frame.winfo_children():
            widget.destroy()
        self.constraint_widgets.clear()
        
        if not self.use_individual_constraints.get():
            self.constraints_info = ttk.Label(self.constraints_frame, text="Habilite as restrições individuais acima")
            self.constraints_info.pack(pady=20)
            return
            
        selected_assets = self.get_selected_assets()
        if len(selected_assets) < 2:
            self.constraints_info = ttk.Label(self.constraints_frame, text="Selecione pelo menos 2 ativos na aba Dados")
            self.constraints_info.pack(pady=20)
            return
        
        # Criar widgets para cada ativo selecionado
        ttk.Label(self.constraints_frame, text="Configure limites específicos:", 
                 font=('TkDefaultFont', 10, 'bold')).pack(anchor='w', pady=(0,10))
        
        for asset in selected_assets:
            # Frame para cada ativo
            asset_frame = ttk.LabelFrame(self.constraints_frame, text=asset, padding="5")
            asset_frame.pack(fill='x', pady=5, padx=10)
            
            # Frame para min e max lado a lado
            limits_frame = ttk.Frame(asset_frame)
            limits_frame.pack(fill='x')
            
            # Min
            min_frame = ttk.Frame(limits_frame)
            min_frame.pack(side='left', fill='x', expand=True, padx=(0,5))
            ttk.Label(min_frame, text="Mín (%):").pack(anchor='w')
            min_var = tk.DoubleVar(value=self.min_weight_var.get())
            min_entry = ttk.Entry(min_frame, textvariable=min_var, width=8)
            min_entry.pack(anchor='w')
            
            # Max
            max_frame = ttk.Frame(limits_frame)
            max_frame.pack(side='left', fill='x', expand=True, padx=(5,0))
            ttk.Label(max_frame, text="Máx (%):").pack(anchor='w')
            max_var = tk.DoubleVar(value=self.max_weight_var.get())
            max_entry = ttk.Entry(max_frame, textvariable=max_var, width=8)
            max_entry.pack(anchor='w')
            
            # Guardar referências
            self.constraint_widgets[asset] = {
                'min_var': min_var,
                'max_var': max_var,
                'min_entry': min_entry,
                'max_entry': max_entry
            }
    
    def update_short_widgets(self):
        """Atualizar widgets de short selling"""
        # Limpar widgets existentes
        for widget in self.short_frame.winfo_children():
            widget.destroy()
        self.short_widgets.clear()
        
        if not self.use_short.get():
            self.short_info = ttk.Label(self.short_frame, text="Habilite posições short acima")
            self.short_info.pack(pady=20)
            return
        
        if self.df is None:
            self.short_info = ttk.Label(self.short_frame, text="Carregue dados primeiro")
            self.short_info.pack(pady=20)
            return
            
        selected_assets = self.get_selected_assets()
        if len(selected_assets) < 1:
            self.short_info = ttk.Label(self.short_frame, text="Selecione ativos principais na aba Dados")
            self.short_info.pack(pady=20)
            return
        
        # Identificar ativos disponíveis para short (não selecionados)
        all_assets = list(self.assets_listbox.get(0, tk.END))
        available_for_short = [asset for asset in all_assets if asset not in selected_assets]
        
        if len(available_for_short) == 0:
            self.short_info = ttk.Label(self.short_frame, text="Selecione menos ativos principais para liberar opções de short")
            self.short_info.pack(pady=20)
            return
        
        # Criar widgets para shorts
        ttk.Label(self.short_frame, text="Selecione ativos para posição short (venda a descoberto):", 
                 font=('TkDefaultFont', 10, 'bold')).pack(anchor='w', pady=(0,10))
        
        for asset in available_for_short:
            # Frame para cada ativo short
            asset_frame = ttk.Frame(self.short_frame)
            asset_frame.pack(fill='x', pady=2, padx=10)
            
            # Checkbox para habilitar short neste ativo
            use_var = tk.BooleanVar(value=False)
            check = ttk.Checkbutton(asset_frame, text=asset, variable=use_var,
                                   command=lambda a=asset: self.toggle_short_asset(a))
            check.pack(side='left', anchor='w')
            
            # Entry para peso (inicialmente desabilitado)
            weight_var = tk.DoubleVar(value=-10.0)
            weight_entry = ttk.Entry(asset_frame, textvariable=weight_var, width=8, state='disabled')
            weight_entry.pack(side='right', padx=(5,0))
            ttk.Label(asset_frame, text="Peso (%):").pack(side='right')
            
            # Guardar referências
            self.short_widgets[asset] = {
                'use_var': use_var,
                'weight_var': weight_var,
                'check': check,
                'entry': weight_entry
            }
    
    def toggle_individual_constraints(self):
        """Toggle restrições individuais"""
        self.update_constraints_widgets()
    
    def toggle_short_selling(self):
        """Toggle short selling"""
        self.update_short_widgets()
    
    def toggle_short_asset(self, asset):
        """Toggle short para ativo específico"""
        if asset in self.short_widgets:
            widgets = self.short_widgets[asset]
            if widgets['use_var'].get():
                widgets['entry'].config(state='normal')
            else:
                widgets['entry'].config(state='disabled')
    
    def get_individual_constraints(self):
        """Obter dicionário de restrições individuais"""
        if not self.use_individual_constraints.get():
            return None
        
        constraints = {}
        for asset, widgets in self.constraint_widgets.items():
            min_val = widgets['min_var'].get() / 100
            max_val = widgets['max_var'].get() / 100
            
            # Validar
            if min_val > max_val:
                messagebox.showerror("Erro", f"Peso mínimo > máximo para {asset}")
                return None
                
            constraints[asset] = {
                'min': min_val,
                'max': max_val
            }
        
        return constraints
    
    def get_short_configuration(self):
        """Obter configuração de shorts"""
        if not self.use_short.get():
            return [], {}
        
        short_assets = []
        short_weights = {}
        
        for asset, widgets in self.short_widgets.items():
            if widgets['use_var'].get():
                weight = widgets['weight_var'].get() / 100
                if weight > 0:
                    messagebox.showerror("Erro", f"Peso short deve ser negativo para {asset}")
                    return [], {}
                short_assets.append(asset)
                short_weights[asset] = weight
        
        return short_assets, short_weights
    
    def select_all_assets(self):
        """Selecionar todos os ativos"""
        self.assets_listbox.select_set(0, tk.END)
        self.update_advanced_widgets()
    
    def clear_selection(self):
        """Limpar seleção de ativos"""
        self.assets_listbox.selection_clear(0, tk.END)
        self.update_advanced_widgets()
    
    def get_selected_assets(self):
        """Obter ativos selecionados"""
        selected_indices = self.assets_listbox.curselection()
        return [self.assets_listbox.get(i) for i in selected_indices]
    
    def optimize_portfolio(self):
        """Executar otimização do portfólio com TODAS as funcionalidades"""
        if self.df is None:
            messagebox.showerror("Erro", "Carregue um arquivo Excel primeiro!")
            return
        
        selected_assets = self.get_selected_assets()
        if len(selected_assets) < 2:
            messagebox.showerror("Erro", "Selecione pelo menos 2 ativos!")
            return
        
        # Obter configurações avançadas
        individual_constraints = self.get_individual_constraints()
        if individual_constraints is None and self.use_individual_constraints.get():
            return  # Erro já mostrado na função
        
        short_assets, short_weights = self.get_short_configuration()
        if short_assets is None:
            return  # Erro já mostrado na função
        
        try:
            # Mostrar janela de progresso
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Otimizando...")
            progress_window.geometry("350x120")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            ttk.Label(progress_window, text="🔄 Otimizando portfólio...").pack(pady=15)
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(pady=10, padx=20, fill='x')
            progress_bar.start()
            
            status_label = ttk.Label(progress_window, text="Inicializando...")
            status_label.pack(pady=5)
            
            # Forçar atualização da interface
            self.root.update()
            
            # Preparar lista completa de ativos
            all_assets = selected_assets.copy()
            if len(short_assets) > 0:
                all_assets.extend(short_assets)
            
            status_label.config(text="Inicializando otimizador...")
            self.root.update()
            
            # Inicializar otimizador (SUA CLASSE ORIGINAL!)
            self.optimizer = PortfolioOptimizer(self.df, all_assets)
            
            status_label.config(text="Configurando parâmetros...")
            self.root.update()
            
            # Mapeamento completo de objetivos
            objective_map = {
                "Maximizar Sharpe Ratio": 'sharpe',
                "Maximizar Sortino Ratio": 'sortino',
                "Minimizar Risco": 'volatility',
                "Maximizar Inclinação": 'slope',
                "Maximizar Inclinação/[(1-R²)×Vol]": 'hc10',
                "Maximizar Qualidade da Linearidade": 'quality_linear',
                "Maximizar Linearidade do Excesso": 'excess_hc10'
            }
            
            objective_type = objective_map[self.objective_var.get()]
            min_weight = self.min_weight_var.get() / 100
            max_weight = self.max_weight_var.get() / 100
            
            # Determinar taxa livre de risco
            if self.has_risk_free and hasattr(self.optimizer, 'risk_free_rate_total'):
                risk_free_rate = self.optimizer.risk_free_rate_total
            else:
                risk_free_rate = self.risk_free_var.get() / 100
            
            status_label.config(text="Executando otimização...")
            self.root.update()
            
            # EXECUTAR OTIMIZAÇÃO com todas as funcionalidades
            if len(short_assets) > 0:
                # Otimização com shorts
                self.result = self.optimizer.optimize_portfolio_with_shorts(
                    selected_assets=selected_assets,
                    short_assets=short_assets,
                    short_weights=short_weights,
                    objective_type=objective_type,
                    max_weight=max_weight,
                    min_weight=min_weight,
                    risk_free_rate=risk_free_rate,
                    individual_constraints=individual_constraints
                )
            else:
                # Otimização normal
                self.result = self.optimizer.optimize_portfolio(
                    objective_type=objective_type,
                    max_weight=max_weight,
                    min_weight=min_weight,
                    risk_free_rate=risk_free_rate,
                    individual_constraints=individual_constraints
                )
            
            # Fechar janela de progresso
            progress_window.destroy()
            
            if self.result['success']:
                self.display_results()
                self.display_monthly_tables()  # NOVA: Exibir tabelas mensais
                self.export_csv_btn.config(state='normal')
                self.export_excel_btn.config(state='normal')
                messagebox.showinfo("Sucesso", "🎉 Otimização concluída com sucesso!")
                # Mudar para aba de resultados
                self.notebook.select(self.tab_results)
            else:
                messagebox.showerror("Erro", f"❌ {self.result['message']}")
                
        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            messagebox.showerror("Erro", f"Erro durante otimização:\n{str(e)}")
            
    def display_results(self):
        """Exibir resultados COMPLETOS da otimização (TODAS as métricas como no Streamlit)"""
        if not self.result or not self.result['success']:
            return
        
        metrics = self.result['metrics']
        
        # 1. Mostrar métricas COMPLETAS no texto (IDÊNTICAS ao Streamlit)
        metrics_text = f"""📈 MÉTRICAS DO PORTFÓLIO OTIMIZADO

🎯 RETORNOS:
• Retorno Total: {metrics['gv_final']:.4%}
• Retorno Anualizado: {metrics['annual_return']:.4%}
• Excesso de Retorno: {metrics['excess_return']:.4%}

⚡ RATIOS DE PERFORMANCE:
• Sharpe Ratio: {metrics['sharpe_ratio']:.4f}
• Sortino Ratio: {metrics['sortino_ratio']:.4f}

📊 MÉTRICAS DE RISCO:
• Volatilidade: {metrics['volatility']:.4%}
• Downside Deviation: {metrics['downside_deviation']:.4%}
• R²: {metrics['r_squared']:.4f}

⚠️ VALUE AT RISK (VaR):
• VaR 95% (Diário): {metrics['var_95_daily']:.4%}
• VaR 99% (Diário): {metrics['var_99_daily']:.4%}
• CVaR 95% (Diário): {metrics['cvar_95_daily']:.4%}
• CVaR 99% (Diário): {metrics['cvar_99_daily']:.4%}

📅 VaR ANUALIZADO:
• VaR 95% (Anual): {metrics['var_95_annual']:.4%}
• VaR 99% (Anual): {metrics['var_99_annual']:.4%}
• CVaR 95% (Anual): {metrics['cvar_95_annual']:.4%}
• CVaR 99% (Anual): {metrics['cvar_99_annual']:.4%}

🏛️ TAXA DE REFERÊNCIA:
• Taxa Usada: {metrics['risk_free_rate']:.4%}

📈 MÉTRICAS AVANÇADAS:
• Inclinação (Slope): {metrics['slope']:.6f}
• HC10: {metrics['hc10']:.6f}"""
        
        # Adicionar métricas específicas do excesso se disponíveis
        if self.objective_var.get() == "Maximizar Linearidade do Excesso" and metrics.get('excess_r_squared') is not None:
            # Calcular métricas do excesso
            if hasattr(self.optimizer, 'risk_free_returns') and self.optimizer.risk_free_returns is not None:
                excess_returns_daily = metrics['portfolio_returns_daily'] - self.optimizer.risk_free_returns.values
                excess_vol = np.std(excess_returns_daily, ddof=0) * np.sqrt(252)
                mean_excess_daily = np.mean(excess_returns_daily)
                std_excess_daily = np.std(excess_returns_daily, ddof=0)
                var_95_excess_daily = mean_excess_daily - 1.65 * std_excess_daily
                
                # Retorno anual do excesso
                excess_total = metrics['gv_final'] - metrics['risk_free_rate']
                annual_excess_return = (1 + excess_total) ** (252 / len(excess_returns_daily)) - 1
                
                metrics_text += f"""

🆕 MÉTRICAS DO EXCESSO DE RETORNO:
• R² do Excesso: {metrics['excess_r_squared']:.4f}
• Volatilidade do Excesso: {excess_vol:.4%}
• VaR 95% do Excesso (Diário): {var_95_excess_daily:.4%}
• Retorno Anual do Excesso: {annual_excess_return:.4%}
• Inclinação do Excesso: {metrics['excess_slope']:.6f}
• HC10 do Excesso: {metrics['excess_hc10']:.6f}"""
        
        # Adicionar explicações importantes (como no Streamlit)
        metrics_text += f"""

💡 EXPLICAÇÕES:
• VaR vs CVaR:
  - VaR 95% = {metrics['var_95_daily']:.2%}: Em 95% dos dias você não perderá mais que {abs(metrics['var_95_daily']):.2%}
  - CVaR 95% = {metrics['cvar_95_daily']:.2%}: Nos 5% piores dias, perderá em média {abs(metrics['cvar_95_daily']):.2%}

• Taxa de Referência: Representa o retorno de um investimento sem risco (ex: CDI, Tesouro).
  O Sharpe Ratio mede quanto retorno extra você obtém por unidade de risco adicional.

• Sortino Ratio: Similar ao Sharpe, mas considera apenas a volatilidade dos retornos negativos.
  É mais apropriado pois investidores se preocupam mais com perdas do que com ganhos voláteis.

• Objetivo de Otimização Usado: {self.objective_var.get()}"""
        
        self.metrics_text.delete('1.0', tk.END)
        self.metrics_text.insert('1.0', metrics_text)
        
        # 2. Mostrar composição COMPLETA do portfólio
        portfolio_df = self.optimizer.get_portfolio_summary(self.result['weights'])
        
        # Limpar TreeView
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)
        
        # Inserir dados (incluindo posições negativas se houver)
        total_positive = 0
        total_negative = 0
        
        # Mostrar TODOS os pesos (incluindo negativos)
        all_weights = self.result['weights']
        for i, asset in enumerate(self.result['assets']):
            weight = all_weights[i]
            if abs(weight) > 0.001:  # Mostrar se peso > 0.1%
                weight_pct = weight * 100
                if weight > 0:
                    total_positive += weight_pct
                    color_tag = 'positive'
                else:
                    total_negative += weight_pct
                    color_tag = 'negative'
                
                # Inserir com formatação
                if weight < 0:
                    item = self.portfolio_tree.insert('', 'end', values=(asset, f"{weight_pct:.2f}% (SHORT)"))
                else:
                    item = self.portfolio_tree.insert('', 'end', values=(asset, f"{weight_pct:.2f}%"))
        
        # Adicionar linha de total
        self.portfolio_tree.insert('', 'end', values=("─" * 20, "─" * 10))
        self.portfolio_tree.insert('', 'end', values=("TOTAL LONG", f"{total_positive:.1f}%"))
        if abs(total_negative) > 0.001:
            self.portfolio_tree.insert('', 'end', values=("TOTAL SHORT", f"{total_negative:.1f}%"))
        
        # 3. Criar gráfico de evolução COMPLETO
        self.create_performance_chart()
    
    def create_performance_chart(self):
        """Criar gráfico de performance completo"""
        # Limpar frame do gráfico
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Criar figura matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Dados do gráfico
        periods = range(1, len(self.result['metrics']['portfolio_cumulative']) + 1)
        portfolio_cumulative = self.result['metrics']['portfolio_cumulative'] * 100
        
        # Plot principal
        ax.plot(periods, portfolio_cumulative, 'b-', linewidth=2.5, label='Portfólio Otimizado')
        
        # Se tem taxa livre, adicionar TODAS as linhas
        if hasattr(self.optimizer, 'risk_free_cumulative') and self.optimizer.risk_free_cumulative is not None:
            risk_free_cumulative = self.optimizer.risk_free_cumulative * 100
            ax.plot(periods, risk_free_cumulative, color='orange', linestyle='--', linewidth=2, 
                   label='Taxa de Referência')
            
            # Excesso de retorno
            excess = portfolio_cumulative - risk_free_cumulative
            ax.plot(periods, excess, 'g:', linewidth=2, label='Excesso de Retorno')
        
        # Configurar gráfico
        ax.set_title('Evolução do Retorno Acumulado', fontsize=14, fontweight='bold')
        ax.set_xlabel('Dias de Negociação')
        ax.set_ylabel('Retorno Acumulado (%)')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Anotação com retorno final
        final_return = self.result['metrics']['gv_final']
        ax.annotate(f'Retorno Final: {final_return:.2%}', 
                   xy=(len(periods), final_return * 100),
                   xytext=(-60, -30), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # Adicionar ao Tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Toolbar para zoom/pan
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(canvas, self.chart_frame)
        toolbar.update()
        
        plt.tight_layout()


def main():
    """Função principal"""
    root = tk.Tk()
    
    # Configurar estilo
    style = ttk.Style()
    style.theme_use('clam')  # Tema mais moderno
    
    # Configurações de estilo personalizadas
    style.configure("Accent.TButton", background="#0078d4", foreground="white")
    
    # Criar aplicação
    app = PortfolioOptimizerGUI(root)
    
    # Executar
    root.mainloop()

if __name__ == "__main__":
    main()
