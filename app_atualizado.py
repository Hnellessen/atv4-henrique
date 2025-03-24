import streamlit as st
import pandas as pd
import sqlite3
from faker import Faker

# Interface Streamlit
def main():
    st.title("ERP Financeiro com Streamlit")
    
    menu = ["Clientes", "Contas a Pagar", "Contas a Receber", "Lançamentos", "Relatórios"]
    choice = st.sidebar.selectbox("Selecione uma opção", menu)
    conn = sqlite3.connect("erp_finance.db", detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()
    
    if choice == "Clientes":
        st.subheader("Cadastro de Clientes")
        df = pd.read_sql_query("SELECT * FROM clientes", conn)
        st.dataframe(df)
        
    elif choice == "Contas a Pagar":
        st.subheader("Contas a Pagar")
        df = pd.read_sql_query("SELECT * FROM contas_pagar", conn)
        st.dataframe(df)
        
    elif choice == "Contas a Receber":
        st.subheader("Contas a Receber")
        df = pd.read_sql_query("SELECT * FROM contas_receber", conn)
        st.dataframe(df)
        
    elif choice == "Lançamentos":
        st.subheader("Lançamentos Financeiros")
        df = pd.read_sql_query("SELECT * FROM lancamentos", conn)
        st.dataframe(df)
        
    elif choice == "Relatórios":
    st.subheader("Relatórios Financeiros")
    
    relatorio = st.selectbox("Escolha um relatório", [
        "Fluxo de Caixa por Mês",
        "Distribuição das Contas a Pagar por Fornecedor",
        "Status das Contas a Pagar e Receber",
        "Top 5 Clientes com Maior Receita",
        "Comparação Receita vs Despesa (Mês Atual)",
        "Previsão de Fluxo de Caixa (Próximos 30 dias)"
    ])
    
    if relatorio == "Fluxo de Caixa por Mês":
        df = pd.read_sql_query("SELECT tipo, valor, data FROM lancamentos", conn)
        df['data'] = pd.to_datetime(df['data'])
        df['mes'] = df['data'].dt.to_period('M').astype(str)
        resumo = df.groupby(['mes', 'tipo'])['valor'].sum().unstack().fillna(0)
        st.bar_chart(resumo)
        st.dataframe(resumo)

    elif relatorio == "Distribuição das Contas a Pagar por Fornecedor":
        df = pd.read_sql_query("SELECT fornecedor, valor FROM contas_pagar", conn)
        resumo = df.groupby('fornecedor')['valor'].sum().sort_values(ascending=False)
        st.bar_chart(resumo)
        st.dataframe(resumo.reset_index())

    elif relatorio == "Status das Contas a Pagar e Receber":
        df_pagar = pd.read_sql_query("SELECT status FROM contas_pagar", conn)
        df_receber = pd.read_sql_query("SELECT status FROM contas_receber", conn)
        pagar_status = df_pagar['status'].value_counts()
        receber_status = df_receber['status'].value_counts()
        status_df = pd.DataFrame({
            'Contas a Pagar': pagar_status,
            'Contas a Receber': receber_status
        }).fillna(0)
        st.bar_chart(status_df)

    elif relatorio == "Top 5 Clientes com Maior Receita":
        df = pd.read_sql_query("""
            SELECT c.nome, SUM(cr.valor) as total
            FROM contas_receber cr
            JOIN clientes c ON cr.cliente_id = c.id
            WHERE cr.status = 'Recebido'
            GROUP BY c.nome
            ORDER BY total DESC
            LIMIT 5
        """, conn)
        st.bar_chart(df.set_index('nome'))
        st.dataframe(df)

    elif relatorio == "Comparação Receita vs Despesa (Mês Atual)":
        df = pd.read_sql_query("SELECT tipo, valor, data FROM lancamentos", conn)
        df['data'] = pd.to_datetime(df['data'])
        mes_atual = pd.Timestamp.now().month
        df = df[df['data'].dt.month == mes_atual]
        resumo = df.groupby('tipo')['valor'].sum()
        st.bar_chart(resumo)
        st.dataframe(resumo.reset_index())

    elif relatorio == "Previsão de Fluxo de Caixa (Próximos 30 dias)":
        hoje = pd.Timestamp.today()
        futuro = hoje + pd.Timedelta(days=30)

        df_pagar = pd.read_sql_query("SELECT valor, vencimento FROM contas_pagar WHERE status = 'Pendente'", conn)
        df_pagar['vencimento'] = pd.to_datetime(df_pagar['vencimento'])
        df_pagar_30d = df_pagar[(df_pagar['vencimento'] >= hoje) & (df_pagar['vencimento'] <= futuro)]

        df_receber = pd.read_sql_query("SELECT valor, vencimento FROM contas_receber WHERE status = 'Pendente'", conn)
        df_receber['vencimento'] = pd.to_datetime(df_receber['vencimento'])
        df_receber_30d = df_receber[(df_receber['vencimento'] >= hoje) & (df_receber['vencimento'] <= futuro)]

        total_pagar = df_pagar_30d['valor'].sum()
        total_receber = df_receber_30d['valor'].sum()
        saldo_futuro = total_receber - total_pagar

        st.metric("Recebimentos previstos (30 dias)", f"R$ {total_receber:,.2f}")
        st.metric("Pagamentos previstos (30 dias)", f"R$ {total_pagar:,.2f}")
        st.metric("Saldo estimado", f"R$ {saldo_futuro:,.2f}", delta_color="normal" if saldo_futuro >= 0 else "inverse")

        st.write("Detalhamento - Contas a Receber")
        st.dataframe(df_receber_30d)
        st.write("Detalhamento - Contas a Pagar")
        st.dataframe(df_pagar_30d)

    conn.close()
    
if __name__ == "__main__":
    main()
