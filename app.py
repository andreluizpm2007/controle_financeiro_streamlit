import streamlit as st
st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="favicon.png",
    layout="wide"
)

import pandas as pd
import datetime as dt
import uuid
import os
from dateutil.relativedelta import relativedelta

ARQUIVO = "financeiro.csv"


# ---------------- Funções auxiliares ----------------

def carregar_dados():
    if os.path.exists(ARQUIVO):
        df = pd.read_csv(ARQUIVO, dtype=str)
        if "valor" in df.columns:
            df["valor"] = df["valor"].astype(float)
        return df
    else:
        colunas = [
            "id",
            "data_lancamento",
            "descricao",
            "categoria",
            "forma_pagamento",
            "operadora",
            "tipo",
            "valor",
            "parcela_atual",
            "total_parcelas",
            "vencimento"
        ]
        return pd.DataFrame(columns=colunas)

def salvar_dados(df):
    df.to_csv(ARQUIVO, index=False)

def mascara_valor(valor_digitado):
    numeros = ''.join(filter(str.isdigit, valor_digitado))
    if numeros == "":
        return "0,00"
    while len(numeros) < 3:
        numeros = "0" + numeros
    return f"{numeros[:-2]},{numeros[-2:]}"


def converter_para_float(valor_formatado):
    return float(valor_formatado.replace(".", "").replace(",", "."))


def gerar_parcelas(id_compra, data_lancamento, descricao, categoria,
                   forma_pagamento, operadora, tipo,
                   valor_total, qtd_parcelas, primeiro_vencimento):
    linhas = []
    valor_parcela = round(valor_total / qtd_parcelas, 2)

    for i in range(qtd_parcelas):
        vencimento_parcela = primeiro_vencimento + relativedelta(months=i)
        linha = {
            "id": id_compra,
            "data_lancamento": data_lancamento.strftime("%Y-%m-%d"),
            "descricao": descricao,
            "categoria": categoria,
            "forma_pagamento": forma_pagamento,
            "operadora": operadora,
            "tipo": tipo,
            "valor": valor_parcela,
            "parcela_atual": str(i + 1),
            "total_parcelas": str(qtd_parcelas),
            "vencimento": vencimento_parcela.strftime("%Y-%m")
        }
        linhas.append(linha)

    return linhas

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ---------------- Carregar dados ----------------

df = carregar_dados()

# ---------------- Layout com sidebar ----------------

st.sidebar.title("Menu")
pagina = st.sidebar.radio(
    "Navegação",
    ["Dashboard", "Lançamentos", "Relatórios"]
)

# ---------------- DASHBOARD ----------------

if pagina == "Dashboard":
    st.title("Dashboard financeiro")

    if df.empty:
        st.info("Ainda não há lançamentos cadastrados.")
    else:
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

        total_geral = df["valor"].sum()
        col_kpi1.metric("Total geral", formatar_moeda(total_geral))

        # Total do mês atual
        mes_atual = dt.date.today().strftime("%Y-%m")
        df_mes_atual = df[df["vencimento"] == mes_atual]
        total_mes_atual = df_mes_atual["valor"].sum()
        col_kpi2.metric("Total do mês atual", formatar_moeda(total_mes_atual))

        # Número de lançamentos
        col_kpi3.metric("Quantidade de lançamentos", len(df))

        st.markdown("---")

        col_g1, col_g2 = st.columns(2)

        # Gráfico por mês de vencimento
        with col_g1:
            st.subheader("Total por mês de vencimento")
            df_mes = df.groupby("vencimento")["valor"].sum().reset_index()
            df_mes = df_mes.sort_values("vencimento")
            st.bar_chart(df_mes.set_index("vencimento"))

        # Gráfico por categoria
        with col_g2:
            st.subheader("Total por categoria")
            if "categoria" in df.columns:
                df_cat = df.groupby("categoria")["valor"].sum().reset_index()
                df_cat = df_cat.sort_values("valor", ascending=False)
                st.bar_chart(df_cat.set_index("categoria"))
            else:
                st.info("Não há coluna de categoria para agrupar.")

        st.markdown("---")

        st.subheader("Tabela geral")
        st.dataframe(df)

# ---------------- LANÇAMENTOS ----------------

elif pagina == "Lançamentos":
    st.title("Lançamentos e edição")

    st.header("Novo lançamento")

    col1, col2 = st.columns(2)
    with col1:
        data_lancamento = st.date_input("Data de lançamento", dt.date.today())
        descricao = st.text_input("Descrição")
        categoria = st.text_input("Categoria")
        forma_pagamento = st.text_input("Forma de pagamento")
    with col2:
        operadora = st.text_input("Operadora (se houver)")
        tipo = st.selectbox("Tipo", ["Crédito", "Débito", "Dinheiro", "Pix", "Outro"])

    st.subheader("Valor e parcelamento")

    colv1, colv2, colv3 = st.columns(3)
    with colv1:
        valor_digitado = st.text_input("Valor (R$)", value="0,00")
        valor_formatado = mascara_valor(valor_digitado)
        st.write("Valor formatado:", valor_formatado)
    with colv2:
        qtd_parcelas = st.number_input("Quantidade de parcelas", min_value=1, max_value=48, value=1)
    with colv3:
        primeiro_vencimento = st.date_input("Vencimento da 1ª parcela", dt.date.today())

    if st.button("Salvar lançamento"):
        try:
            valor_float = converter_para_float(valor_formatado)
            id_compra = str(uuid.uuid4())[:8]

            linhas = gerar_parcelas(
                id_compra=id_compra,
                data_lancamento=data_lancamento,
                descricao=descricao,
                categoria=categoria,
                forma_pagamento=forma_pagamento,
                operadora=operadora,
                tipo=tipo,
                valor_total=valor_float,
                qtd_parcelas=int(qtd_parcelas),
                primeiro_vencimento=primeiro_vencimento
            )

            df_novo = pd.DataFrame(linhas)
            df_novo["valor"] = df_novo["valor"].astype(float)

            df = pd.concat([df, df_novo], ignore_index=True)
            salvar_dados(df)

            st.success("Lançamento salvo com parcelamento automático!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    st.markdown("---")
    st.header("Editar ou excluir lançamentos")

    if not df.empty:
        linha_selecionada = st.selectbox(
            "Selecione uma linha para editar ou excluir",
            df.index,
            format_func=lambda x: f"{df.loc[x, 'descricao']} - Parcela {df.loc[x, 'parcela_atual']}/{df.loc[x, 'total_parcelas']} - {df.loc[x, 'vencimento']}"
        )

        st.subheader("Dados da linha selecionada")

        dados = df.loc[linha_selecionada]

        nova_descricao = st.text_input("Descrição", dados["descricao"], key="edit_desc")
        nova_categoria = st.text_input("Categoria", dados["categoria"], key="edit_cat")
        nova_forma = st.text_input("Forma de pagamento", dados["forma_pagamento"], key="edit_forma")
        nova_operadora = st.text_input("Operadora", dados["operadora"], key="edit_operadora")
        novo_tipo = st.text_input("Tipo", dados["tipo"], key="edit_tipo")
        novo_valor = st.number_input("Valor", value=float(dados["valor"]), key="edit_valor")
        novo_vencimento = st.text_input("Vencimento (AAAA-MM)", dados["vencimento"], key="edit_venc")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Salvar edição"):
                df.loc[linha_selecionada, "descricao"] = nova_descricao
                df.loc[linha_selecionada, "categoria"] = nova_categoria
                df.loc[linha_selecionada, "forma_pagamento"] = nova_forma
                df.loc[linha_selecionada, "operadora"] = nova_operadora
                df.loc[linha_selecionada, "tipo"] = novo_tipo
                df.loc[linha_selecionada, "valor"] = novo_valor
                df.loc[linha_selecionada, "vencimento"] = novo_vencimento

                salvar_dados(df)
                st.success("Lançamento atualizado!")
        with col_b2:
            if st.button("Excluir lançamento"):
                df = df.drop(linha_selecionada)
                salvar_dados(df)
                st.success("Lançamento excluído!")
    else:
        st.info("Nenhum lançamento para editar ou excluir.")

# ---------------- RELATÓRIOS ----------------

elif pagina == "Relatórios":
    st.title("Relatórios mensais")

    if df.empty:
        st.info("Ainda não há lançamentos cadastrados.")
    else:
        df["vencimento"] = df["vencimento"].astype(str)
        meses_disponiveis = sorted(df["vencimento"].unique())

        mes_relatorio = st.selectbox(
            "Selecione o mês para o relatório",
            meses_disponiveis
        )

        df_mes = df[df["vencimento"] == mes_relatorio].copy()

        st.subheader(f"Lançamentos de {mes_relatorio}")
        st.dataframe(df_mes)

        total_mes = df_mes["valor"].sum()
        st.metric("Total do mês", formatar_moeda(total_mes))

        st.markdown("---")
        st.subheader("Exportar relatório")

        # Exportar para Excel
if not df_mes.empty:
    from io import BytesIO

    excel_buffer = BytesIO()
    df_mes.to_excel(excel_buffer, index=False, sheet_name="Relatorio")
    excel_buffer.seek(0)

    st.download_button(
        label="Baixar em Excel",
        data=excel_buffer,
        file_name=f"relatorio_{mes_relatorio}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
            st.download_button(
                label="Baixar em Excel",
                data=excel_buffer,
                file_name=f"relatorio_{mes_relatorio}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Exportar para CSV
            csv_buffer = df_mes.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Baixar em CSV",
                data=csv_buffer,
                file_name=f"relatorio_{mes_relatorio}.csv",
                mime="text/csv"
            )
        else:
            st.info("Não há dados para o mês selecionado.")
