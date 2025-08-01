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
                    if sufixo == "LIVRE":
                        st.warning(f"⚠️ Códigos não encontrados: {', '.join(erros)}")
                        st.info("💡 Verifique se os códigos estão corretos no Yahoo Finance")
                    else:
                        st.warning(f"⚠️ Erros em: {', '.join(erros)}")
                
                # 2. Consolidar PREÇOS BRUTOS
                with st.spinner("🔄 Consolidando preços..."):
                    df_precos_brutos = criar_consolidado_yahoo(dados_yahoo)
                
                if df_precos_brutos is not None:
                    st.success(f"✅ Preços consolidados: {df_precos_brutos.shape}")
                    
                    # 🔥 NOVA LÓGICA: SALVAR PREÇOS BRUTOS NO SESSION STATE
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
                    
                    # 🎯 SALVAR PREÇOS BRUTOS (PERPÉTUA)
                    st.session_state['dados_brutos'] = df_precos_com_data
                    st.session_state['fonte_dados'] = f"Yahoo Finance ({len(dados_yahoo)} ativos)"
                    st.session_state['periodo_disponivel'] = {
                        'inicio': df_precos_com_data['Data'].min(),
                        'fim': df_precos_com_data['Data'].max()
                    }
                    
                    # 3. Converter para base 0 (PROCESSO NORMAL)
                    with st.spinner("🔄 Convertendo para base 0..."):
                        dados_base_zero, removidas = transformar_base_zero(df_precos_brutos)
                    
                    if dados_base_zero is not None and not dados_base_zero.empty:
                        st.success(f"✅ Base 0 criada: {dados_base_zero.shape}")
                        
                        # 4. Preparar DataFrame final para compatibilidade
                        df_final = dados_base_zero.copy()
                        df_final = df_final.reset_index()  # Data vira primeira coluna
                        
                        # Reorganizar ativo de referência se necessário (mesmo processo)
                        if usar_referencia and ativo_referencia.strip():
                            ativo_ref_clean = ativo_referencia.strip().upper()
                            
                            if ativo_ref_clean in df_final.columns:
                                nome_referencia = f"Taxa_Ref_{ativo_ref_clean}"
                                colunas_reorganizadas = ['Data']
                                outras_colunas = [col for col in df_final.columns 
                                                if col not in ['Data', ativo_ref_clean]]
                                
                                df_final = df_final.rename(columns={ativo_ref_clean: nome_referencia})
                                colunas_reorganizadas.append(nome_referencia)
                                colunas_reorganizadas.extend(outras_colunas)
                                df_final = df_final[colunas_reorganizadas]
                        
                        # 🎯 SALVAR DADOS EM BASE 0 (COMPATIBILIDADE)
                        st.session_state['df'] = df_final
                        st.session_state['data_source'] = f"Yahoo Finance ({len(dados_yahoo)} ativos)"
                        
                        st.success("🎉 Dados processados e perpetuados!")
                        
                        # 🔥 NOVO: Mostrar resumo dos dados perpetuados
                        periodo = st.session_state['periodo_disponivel']
                        resumo_texto = (
                            f"📊 **Dados Perpetuados:**\n"
                            f"• 💾 **Preços brutos salvos:** {df_precos_com_data.shape[0]} dias\n"
                            f"• 🎯 **Base 0 gerada:** {len(dados_base_zero.columns)} ativos\n"
                            f"• 📅 **Período disponível:** {periodo['inicio'].strftime('%d/%m/%Y')} a {periodo['fim'].strftime('%d/%m/%Y')}\n"
                            f"• 🚀 **Pronto para otimização em qualquer sub-período!**\n"
                        )
                        
                        if usar_referencia and ativo_referencia.strip():
                            resumo_texto += f"• 🏛️ **Ativo de referência:** {ativo_referencia.strip().upper()}\n"
                        
                        if removidas:
                            resumo_texto += f"• ⚠️ **Removidos:** {', '.join(removidas)}"
                        
                        st.info(resumo_texto)
                        
                        st.rerun()
                        
                    else:
                        st.error("❌ Erro na transformação para base 0")
                else:
                    st.error("❌ Erro ao consolidar dados")
            else:
                st.error("❌ Nenhum dado encontrado. Verifique os símbolos.")
