st.set_page_config(page_title="Controle Financeiro", page_icon="favicon.png")

import streamlit as st
import pandas as pd
import datetime as dt
import uuid
import os

ARQUIVO = "financeiro.csv"

# ----------------- Funções auxiliares -----------------

def carregar_dados():
    if os.path.exists(ARQUIVO):
        df = pd.read_csv(ARQUIVO, parse_dates=["data", "data_vencimento"])
    else:
        df = pd.DataFrame(columns=[
            "data", "descricao", "forma_pagamento", "categoria",
            "operadora_banco", "tipo", "valor",
            "parcelas_total", "parcela_atual",
            "data_vencimento", "id_compra"
        ])
    return df

def salvar_dados(df):
    df.to_csv(ARQUIVO, index=False)

def gerar_parcelas(lancamento):
    """Gera linhas de parcelas futuras a partir do primeiro lançamento."""
    linhas = []
    parcelas_total = lancamento["parcelas_total"]
    data_base = lancamento["data_vencimento"]
    for p in range(1, parcelas_total + 1):
        linha = lancamento.copy()
        linha["parcela_atual"] = p
        # cada parcela em meses subsequentes
        linha["data_vencimento"] = data_base + pd.DateOffset(months=p - 1)
        linhas.append(linha)
    return pd.DataFrame(linhas)

# ----------------- Configuração de tema escuro -----------------

st.set_page_config(page_title="Controle Financeiro", layout="wide")

# Força um visual escuro (Streamlit já tem tema dark nas configs,
# mas aqui damos um toque extra via CSS)
st.markdown("""
<style>
body {
    background-color: #121212;
    color: #e0e0e0;
}
[data-testid="stSidebar"] {
    background-color: #1e1e1e;
}
</style>
""", unsafe_allow_html=True)

# ----------------- Carregar dados -----------------

df = carregar_dados()

# ----------------- Sidebar: filtros e navegação -----------------

st.sidebar.title("Filtros e Navegação")

# Filtro de mês/ano
meses = sorted(df["data"].dropna().dt.to_period("M").astype(str).unique()) if not df.empty else []
mes_selecionado = st.sidebar.selectbox("Mês (lançamento)", options=["Todos"] + meses)

meses_venc = sorted(df["data_vencimento"].dropna().dt.to_period("M").astype(str).unique()) if not df.empty else []
mes_venc_selecionado = st.sidebar.selectbox("Mês (vencimento crédito)", options=["Todos"] + meses_venc)

forma_pagamento_filtro = st.sidebar.multiselect(
    "Forma de pagamento",
    options=["Crédito", "Débito", "Pix", "Dinheiro", "Transferência", "Outro"],
    default=[]
)

categoria_filtro = st.sidebar.multiselect(
    "Categoria",
    options=[
        "mercantil", "alimentação", "lazer", "educação", "saúde", "farmácia",
        "combustível", "manutenção", "empresa", "investimentos", "empréstimos",
        "imposto", "assinatura/stream", "salário/renda", "outros"
    ],
    default=[]
)

operadora_filtro = st.sidebar.multiselect(
    "Operadora/Banco",
    options=[
        "Itaú - Personnalité", "Itaú - Credicard", "Itaú - Gold", "Itaú - Luiza Ouro",
        "BB - Ourocard", "Bradesco - Infinite Prime", "Bradesco - Amazon Platinum",
        "Caixa - Sim", "Mercado Pago", "Nubank", "Santander - SX Master",
        "Shopee - Empréstimo", "Mercado Pago - Empréstimo", "BV", "Bradesco",
        "BB", "Caixa", "Itaú", "Nubank", "Livelo", "outros"
    ],
    default=[]
)

pagina = st.sidebar.radio("Tela", ["Lançamentos", "Resumo por mês"])

# ----------------- Tela de lançamentos -----------------

if pagina == "Lançamentos":
    st.title("Lançamentos financeiros")

    st.subheader("Novo lançamento")

    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data do lançamento", value=dt.date.today())
        descricao = st.text_input("Descrição (estabelecimento ou fonte pagadora)")
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    with col2:
        forma_pagamento = st.selectbox("Forma de pagamento", ["Crédito", "Débito", "Pix", "Dinheiro", "Transferência", "Outro"])
        categoria = st.selectbox("Categoria", [
            "mercantil", "alimentação", "lazer", "educação", "saúde", "farmácia",
            "combustível", "manutenção", "empresa", "investimentos", "empréstimos",
            "imposto", "assinatura/stream", "salário/renda", "outros"
        ])
        operadora_banco = st.selectbox("Operadora/Banco", [
            "Itaú - Personnalité", "Itaú - Credicard", "Itaú - Gold", "Itaú - Luiza Ouro",
            "BB - Ourocard", "Bradesco - Infinite Prime", "Bradesco - Amazon Platinum",
            "Caixa - Sim", "Mercado Pago", "Nubank", "Santander - SX Master",
            "Shopee - Empréstimo", "Mercado Pago - Empréstimo", "BV", "Bradesco",
            "BB", "Caixa", "Itaú", "Nubank", "Livelo", "outros"
        ])

    st.subheader("Parcelamento (opcional)")
    colp1, colp2 = st.columns(2)
    with colp1:
        parcelas_total = st.number_input("Número total de parcelas", min_value=1, step=1, value=1)
    with colp2:
        data_vencimento = st.date_input("Data de vencimento (crédito)", value=dt.date.today())

    if st.button("Salvar lançamento"):
        id_compra = str(uuid.uuid4())

        lancamento_base = {
            "data": pd.to_datetime(data),
            "descricao": descricao,
            "forma_pagamento": forma_pagamento,
            "categoria": categoria,
            "operadora_banco": operadora_banco,
            "tipo": tipo,
            "valor": valor,
            "parcelas_total": int(parcelas_total),
            "parcela_atual": 1,
            "data_vencimento": pd.to_datetime(data_vencimento),
            "id_compra": id_compra
        }

        if parcelas_total > 1:
            df_parcelas = gerar_parcelas(lancamento_base)
            df = pd.concat([df, df_parcelas], ignore_index=True)
        else:
            df = pd.concat([df, pd.DataFrame([lancamento_base])], ignore_index=True)

        salvar_dados(df)
        st.success("Lançamento salvo com sucesso e parcelas geradas automaticamente!")

    st.subheader("Lançamentos cadastrados")

    df_exibicao = df.copy()

    # Aplicar filtros
    if mes_selecionado != "Todos":
        periodo = pd.Period(mes_selecionado)
        df_exibicao = df_exibicao[df_exibicao["data"].dt.to_period("M") == periodo]

    if mes_venc_selecionado != "Todos":
        periodo_v = pd.Period(mes_venc_selecionado)
        df_exibicao = df_exibicao[df_exibicao["data_vencimento"].dt.to_period("M") == periodo_v]

    if forma_pagamento_filtro:
        df_exibicao = df_exibicao[df_exibicao["forma_pagamento"].isin(forma_pagamento_filtro)]

    if categoria_filtro:
        df_exibicao = df_exibicao[df_exibicao["categoria"].isin(categoria_filtro)]

    if operadora_filtro:
        df_exibicao = df_exibicao[df_exibicao["operadora_banco"].isin(operadora_filtro)]

    st.dataframe(df_exibicao)

    st.markdown("### Ajuste de parcelas (antecipação)")
    st.write("Selecione uma compra (id_compra) e ajuste o número de parcelas restantes.")

    if not df.empty:
        ids = df["id_compra"].unique()
        id_sel = st.selectbox("ID da compra", options=ids)
        novo_total = st.number_input("Novo total de parcelas (após antecipação)", min_value=1, step=1)

        if st.button("Atualizar parcelas"):
            # Filtra a compra
            mask = df["id_compra"] == id_sel
            df_compra = df[mask].sort_values("parcela_atual")
            if not df_compra.empty:
                primeira = df_compra.iloc[0]
                primeira["parcelas_total"] = int(novo_total)
                # Regera parcelas
                df_novo = gerar_parcelas(primeira)
                # Remove antigas e adiciona novas
                df = df[~mask]
                df = pd.concat([df, df_novo], ignore_index=True)
                salvar_dados(df)
                st.success("Parcelas atualizadas com sucesso!")
            else:
                st.error("Compra não encontrada.")

# ----------------- Tela de resumo por mês -----------------

elif pagina == "Resumo por mês":
    st.title("Resumo financeiro por mês")

    st.write("Selecione um ou mais meses para ver o balanço.")

    meses_disponiveis = sorted(df["data"].dropna().dt.to_period("M").astype(str).unique()) if not df.empty else []
    meses_escolhidos = st.multiselect("Meses (lançamento)", options=meses_disponiveis, default=meses_disponiveis[:1])

    if meses_escolhidos:
        mask = df["data"].dt.to_period("M").astype(str).isin(meses_escolhidos)
        df_resumo = df[mask]

        total_entradas = df_resumo[df_resumo["tipo"] == "Entrada"]["valor"].sum()
        total_saidas = df_resumo[df_resumo["tipo"] == "Saída"]["valor"].sum()
        saldo = total_entradas - total_saidas

        colr1, colr2, colr3 = st.columns(3)
        with colr1:
            st.markdown("#### Total de entradas (R$)")
            st.markdown(f"<h3 style='color:#4caf50;'>R$ {total_entradas:,.2f}</h3>", unsafe_allow_html=True)
        with colr2:
            st.markdown("#### Total de saídas (R$)")
            st.markdown(f"<h3 style='color:#f44336;'>R$ {total_saidas:,.2f}</h3>", unsafe_allow_html=True)
        with colr3:
            st.markdown("#### Saldo final (R$)")
            cor_saldo = "#4caf50" if saldo >= 0 else "#f44336"
            st.markdown(f"<h3 style='color:{cor_saldo};'>R$ {saldo:,.2f}</h3>", unsafe_allow_html=True)

        st.subheader("Detalhamento dos lançamentos")
        st.dataframe(df_resumo)
    else:
        st.info("Selecione pelo menos um mês para ver o resumo.")
