import streamlit as st
import locale
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# =============================================
# TENTATIVA DE FORÇAR O FORMATO BRASILEIRO
# =============================================
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    pass  # Caso o sistema não tenha pt_BR, ignora

st.set_page_config(page_title="Parcelar Auto de Infração", page_icon=":page_facing_up:")

# ================================
# CSS Global
# ================================
css = """
<style>
    /* Remove negrito dos itens do radio */
    div[data-baseweb="radio"] label {
        font-weight: normal !important;
        font-family: inherit !important;
        font-size: 1rem !important;
    }
    header {
        visibility: hidden;
    }
    .block-container {
        background-color: #f0f0f0;
    }
    .stApp {
        background-color: #f0f0f0;
    }
    .main .block-container {
        background-color: #ffffff;
        border-radius: 0.5rem;
        padding: 2rem;
        margin-top: 5rem;
        margin-bottom: 5rem;
        max-width: 800px;
        width: 60%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        position: relative;
    }
    .stApp .main .block-container h1 {
        text-align: center;
    }
    /* Oculta o botão de imprimir ao imprimir */
    @media print {
        .no-print, .print-button {
            display: none !important;
        }
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# make sure we have persistence for the first-step data and submission flag
if "auto_info_submitted" not in st.session_state:
    st.session_state["auto_info_submitted"] = False
if "data_requerimento" not in st.session_state:
    st.session_state["data_requerimento"] = datetime.today()
if "data_auto" not in st.session_state:
    st.session_state["data_auto"] = datetime.today()

# ================================
# Função para formatação de moeda
# ================================
def formatar_moeda_br(valor):
    """Converte float para BRL formatado, ex: 1234.5 -> R$ 1.234,50"""
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "R$ 0,00"

    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"

# ================================
# Título e Abas
# ================================
st.title("Parcelar Auto de Infração")
tabs = st.tabs(["Preencher Requerimento", "Tabela de Descontos"])

# ================================
# ABA 1: Preencher Requerimento
# ================================
with tabs[0]:
    # -------------------------------------------------
    # Expander para DADOS DO AUTO DE INFRAÇÃO
    # -------------------------------------------------
    with st.expander("Dados do Auto de Infração", expanded=True):
        st.subheader("Dados do Auto de Infração")

        if "N_auto" not in st.session_state:
            st.session_state["N_auto"] = ""

        with st.form("form_auto_info"):
            col1, col2 = st.columns(2)
            with col1:
                st.date_input(
                    "Data do requerimento",
                    value=st.session_state["data_requerimento"],
                    key="data_requerimento"
                )
            with col2:
                st.date_input(
                    "Data do Auto de Infração",
                    value=st.session_state["data_auto"],
                    key="data_auto"
                )

            st.text_input(
                "Número do Auto de Infração:",
                value=st.session_state["N_auto"],
                key="N_auto"
            )

            continuar = st.form_submit_button("Continuar")

        if continuar:
            st.session_state["auto_info_submitted"] = True

    if not st.session_state["auto_info_submitted"]:
        st.info(
            "Preencha os dados do auto acima e pressione Enter (ou Continuar) "
            "para liberar o restante do requerimento."
        )
        st.stop()

    data_requerimento = st.session_state["data_requerimento"]
    data_auto = st.session_state["data_auto"]

    # -------------------------------------------------
    # Expander para DADOS DO AUTUADO
    # -------------------------------------------------
    with st.expander("Dados do Autuado", expanded=True):
        st.subheader("Dados do Autuado")
        with st.form("form_requerimento"):
            # Garante chaves no session_state
            for campo in ["nome_completo", "cpf", "endereco", "municipio"]:
                if campo not in st.session_state:
                    st.session_state[campo] = ""

            nome_completo = st.text_input("Nome completo:", value=st.session_state["nome_completo"])
            cpf = st.text_input("N° do CPF:", value=st.session_state["cpf"])
            endereco = st.text_input("Endereço:", value=st.session_state["endereco"])
            municipio = st.text_input("Município:", value=st.session_state["municipio"])

            colA, colB, colC = st.columns(3)
            with colA:
                valor_upf = st.text_input("Valor da UPF:", value="119,14")
            with colB:
                # MUDOU AQUI
                qtd_upf_por_animal = st.number_input("Qtd UPF por animal/Auto:", min_value=0.0, step=0.5, value=2.5)
            with colC:
                qtd_upf_por_parcela = st.number_input("Qtd mínima de UPF por parcela:", min_value=0.0, step=0.5, value=3.0)

            # MUDOU AQUI
            n_animais = st.number_input("Número de Animais/Auto de Infração:", min_value=0, step=1)

            prazo_defesa_escolhido = st.radio(
                "No prazo de defesa até 30 dias?",
                ("Sim (Desconto de 20% pra uma parcela)", "Não (Desconto de 10% pra uma parcela)")
            )

            submit_form = st.form_submit_button("Aplicar / Atualizar")

        if submit_form:
            # Salva dados no session_state
            st.session_state["nome_completo"] = nome_completo
            st.session_state["cpf"] = cpf
            st.session_state["endereco"] = endereco
            st.session_state["municipio"] = municipio
            st.session_state["prazo_defesa"] = prazo_defesa_escolhido

            try:
                valor_upf_float = float(valor_upf.replace(",", "."))
            except ValueError:
                st.error("Valor da UPF inválido, usando 0.")
                valor_upf_float = 0.0

            st.session_state["valor_upf_float"] = valor_upf_float
            st.session_state["qtd_upf_por_animal"] = qtd_upf_por_animal
            st.session_state["qtd_upf_por_parcela"] = qtd_upf_por_parcela
            st.session_state["n_animais"] = n_animais

    # --------------------------
    # Cálculos de parcelas
    # --------------------------
    valor_upf_float = st.session_state.get("valor_upf_float", 0.0)
    total_upf = st.session_state.get("n_animais", 0) * st.session_state.get("qtd_upf_por_animal", 0) * valor_upf_float

    if total_upf > 0:
        st.metric("Valor do Auto", formatar_moeda_br(total_upf))
    else:
        st.write("Valor do Auto: R$ 0,00")

    if valor_upf_float > 0:
        min_valor_parcela = st.session_state["qtd_upf_por_parcela"] * valor_upf_float
    else:
        min_valor_parcela = 0

    if total_upf >= min_valor_parcela and min_valor_parcela > 0:
        num_max_parcelas = int(total_upf // min_valor_parcela)
    else:
        num_max_parcelas = 0
    num_max_parcelas = min(num_max_parcelas, 30)
    

    # ================================
    # Mensagem de desconto
    # ================================
    if prazo_defesa_escolhido == "Sim (Desconto de 20% pra uma parcela)":
        desconto_mensagem = "**Desconto aplicado para prazo dentro dos 30 dias**"
        coluna_desconto = "Desconto Concedido (Integral)"
    else:
        desconto_mensagem = "**Desconto aplicado para prazo fora dos 30 dias**"
        coluna_desconto = "Desconto Concedido (metade)"

    # Exibir desconto antes da legenda
    st.markdown(desconto_mensagem)



    if num_max_parcelas > 0:
        st.write(
            f"É possível parcelar em até {num_max_parcelas} vezes, respeitando "
            f"o valor mínimo de R$ {min_valor_parcela:.2f} por parcela."
        )
    else:
        st.write(
            f"O valor total é menor que o mínimo exigido para uma parcela: R$ {min_valor_parcela:.2f}."
        )

    global parcelas_selecionadas_df
    parcelas_selecionadas_df = pd.DataFrame(columns=['Parcela', 'Valor da Parcela', 'Data de Vencimento']).set_index("Parcela")

    if st.session_state.get("prazo_defesa") == "Sim (Desconto de 20% pra uma parcela)":
        coluna_desconto = "Desconto Concedido (Integral)"
    else:
        coluna_desconto = "Desconto Concedido (metade)"

    discount_percentage = 0
    valor_com_desconto = 0
    valor_parcela_final = 0
    num_parcelas_selecionadas = 0

    if num_max_parcelas > 0:
        with st.expander("Opções de Parcelamento", expanded=True):
            data_dict = {
                "Quantidade de Parcelas": list(range(1, 32)),
                "Desconto Concedido (Integral)": [
                    20, 12, 11.5, 11, 10.5, 10, 9.5, 9, 8.5, 8,
                    7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3,
                    2.5, 2, 1.75, 1.5, 1.25, 1, 0.75, 0.5, 0.25, 0, 0
                ],
                "Desconto Concedido (metade)": [
                    10, 6, 5.75, 5.5, 5.25, 5, 4.75, 4.5, 4.25, 4,
                    3.75, 3.5, 3.25, 3, 2.75, 2.5, 2.25, 2, 1.75, 1.5,
                    1.25, 1, 0.875, 0.75, 0.625, 0.5, 0.375, 0.25, 0.125, 0, 0
                ]
            }

            df_descontos = pd.DataFrame(data_dict)
            df_descontos["Desconto (%)"] = df_descontos[coluna_desconto].apply(lambda x: f"{x}%")
            df_descontos["Valor com Desconto"] = total_upf * (1 - df_descontos[coluna_desconto] / 100)
            df_descontos["Valor da Parcela"] = df_descontos["Valor com Desconto"] / df_descontos["Quantidade de Parcelas"]
            df_descontos["Desconto Concedido"] = total_upf - df_descontos["Valor com Desconto"]

            df_descontos_display = df_descontos.copy()
            for c in ["Valor com Desconto", "Valor da Parcela", "Desconto Concedido"]:
                df_descontos_display[c] = df_descontos_display[c].apply(formatar_moeda_br)

            tabela_para_exibir = df_descontos_display[
                ["Quantidade de Parcelas", "Desconto (%)", "Desconto Concedido", "Valor com Desconto", "Valor da Parcela"]
            ]
            tabela_para_exibir = tabela_para_exibir[tabela_para_exibir["Quantidade de Parcelas"] <= num_max_parcelas]

            st.dataframe(tabela_para_exibir, use_container_width=True)

            if num_max_parcelas > 1:
                num_parcelas_selecionadas = st.slider(
                    "Quantidade de parcelas desejada",
                    min_value=1,
                    max_value=num_max_parcelas,
                    value=1
                )
            else:
                num_parcelas_selecionadas = 1

            st.markdown(
                "Use o controle acima para escolher o parcelamento que melhor atende o requerimento."
            )

            discount_row = df_descontos[df_descontos["Quantidade de Parcelas"] == num_parcelas_selecionadas].iloc[0]
            discount_percentage = discount_row[coluna_desconto]
            valor_com_desconto = total_upf * (1 - discount_percentage / 100)
            valor_parcela_final = valor_com_desconto / num_parcelas_selecionadas

            dados_parcelas = []
            for i in range(1, num_parcelas_selecionadas + 1):
                data_venc = data_requerimento + pd.DateOffset(months=i - 1)
                dados_parcelas.append({
                    "Parcela": i,
                    "Valor da Parcela": formatar_moeda_br(valor_parcela_final),
                    "Data de Vencimento": data_venc.strftime("%d/%m/%Y")
                })

            parcelas_selecionadas_df = pd.DataFrame(dados_parcelas).set_index("Parcela")

    # ================================
    # Exibir Requerimento (HTML)
    # ================================
    if not parcelas_selecionadas_df.empty:
        # Recupera dados
        data_req_label = st.session_state["data_requerimento"].strftime('%d/%m/%Y')
        data_auto_label = st.session_state["data_auto"].strftime('%d/%m/%Y')
        N_auto = st.session_state.get("N_auto", "")
        nome_completo = st.session_state.get("nome_completo", "")
        cpf = st.session_state.get("cpf", "")
        endereco = st.session_state.get("endereco", "")
        municipio = st.session_state.get("municipio", "")

        total_upf_float = st.session_state.get("valor_upf_float",0.0)
        total_upf = st.session_state.get("n_animais",0) * st.session_state.get("qtd_upf_por_animal",0) * total_upf_float

        discount_percentage = locals().get("discount_percentage", 0)
        valor_com_desconto = locals().get("valor_com_desconto", 0)
        valor_parcela_final = locals().get("valor_parcela_final", 0)
        num_parcelas = parcelas_selecionadas_df.shape[0]

        desconto_reais = total_upf - valor_com_desconto
        if desconto_reais < 0:
            desconto_reais = 0

        # Texto principal do requerimento
        texto_requerimento = f"""
        Eu, {nome_completo}, brasileiro(a), portador(a) do CPF nº {cpf}, residente no endereço {endereco}, município de {municipio},
        venho, por meio deste requerimento datado de {data_req_label}, solicitar o parcelamento do Auto de Infração nº {N_auto}, 
        lavrado em {data_auto_label}, nos termos da legislação vigente.
        """

        if total_upf > 0 and num_parcelas > 0:
            texto_parcelamento = (
                f"O requerente solicitou o parcelamento em {num_parcelas} vezes, conforme a tabela de descontos, "
                f"o que lhe confere o direito a um desconto de {discount_percentage}% "
                f"(equivalente a {formatar_moeda_br(desconto_reais)}) "
                f"sobre o valor inicial. Assim, o valor total, que originalmente era de "
                f"{formatar_moeda_br(total_upf)}, passará a ser de {formatar_moeda_br(valor_com_desconto)}, "
                f"distribuído em {num_parcelas} parcelas de {formatar_moeda_br(valor_parcela_final)} cada."
            )
        else:
            texto_parcelamento = (
                "Não é possível parcelar, pois o valor total é inferior ao mínimo exigido para uma parcela."
            )

        # HTML final
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Requerimento de Parcelamento</title>
            <style>
                @page {{
                    margin: 20mm;
                    @bottom-center {{
                        content: "Página " counter(page) " de " counter(pages);
                        font-size: 10pt;
                    }}
                }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    padding: 20px;
                }}
                p {{
                    text-indent: 2em;
                }}
                .container {{
                    max-width: 800px;
                    margin: auto;
                    padding: 20px;
                    border: 1px solid #ccc;
                    border-radius: 10px;
                }}
                h2 {{
                    text-align: center;
                }}
                .texto-requerimento {{
                    margin-top: 20px;
                    line-height: 1.5;
                    text-align: justify;
                }}
                .texto-parcelamento {{
                    margin-top: 20px;
                    font-weight: bold;
                    text-align: justify;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: center;
                }}
                th {{
                    background-color: #f4f4f4;
                }}
                .signature {{
                    margin-top: 40px;
                    text-align: center;
                }}
                .signature p {{
                    margin: 0;
                    text-align: center;
                }}
                .print-button {{
                    display: block;
                    text-align: center;
                    margin-top: 20px;
                }}
                @media print {{
                    .no-print, .print-button {{
                        display: none !important;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Requerimento para Parcelamento de Auto de Infração - Emitido pela Agência IDARON</h2>

                <div class="texto-requerimento">
                    <p>{texto_requerimento}</p>
                </div>

                <div class="texto-parcelamento">
                    <p>{texto_parcelamento}</p>
                </div>

                <h3>Parcelas e Vencimentos</h3>
                <table>
                    <tr>
                        <th>Parcela</th>
                        <th>Valor da Parcela</th>
                        <th>Data de Vencimento</th>
                    </tr>
        """
        # Linhas da tabela
        for index, row in parcelas_selecionadas_df.iterrows():
            html += f"""
                    <tr>
                        <td>{index}</td>
                        <td>{row['Valor da Parcela']}</td>
                        <td>{row['Data de Vencimento']}</td>
                    </tr>
            """
        # Assinatura (2 linhas de espaço + linha mais longa)
        html += f"""
                </table>

                <div class="signature">
                    <p>Segue assinado</p>
                    <br><br>
                    <p>________________________________________</p>
                    <p>{nome_completo}</p>
                    <p>{cpf}</p>
                </div>

                <div class="print-button no-print">
                    <button onclick="window.print()">Imprimir Requerimento</button>
                </div>
            </div>
        </body>
        </html>
        """

        components.html(html, height=800, scrolling=True)

# ================================
# ABA 2: Tabela de Descontos
# ================================
with tabs[1]:
    st.markdown("### Tabela de Descontos")
    Dados = {
        "Quantidade de Parcelas": range(1, 31),
        "Desconto Concedido (Integral)": [
            20, 12, 11.5, 11, 10.5, 10, 9.5, 9, 8.5, 8,
            7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3,
            2.5, 2, 1.75, 1.5, 1.25, 1, 0.75, 0.5, 0.25, 0
        ],
        "Desconto Concedido (metade)": [
            10, 6, 5.75, 5.5, 5.25, 5, 4.75, 4.5, 4.25, 4,
            3.75, 3.5, 3.25, 3, 2.75, 2.5, 2.25, 2, 1.75, 1.5,
            1.25, 1, 0.875, 0.75, 0.625, 0.5, 0.375, 0.25, 0.125, 0
        ]
    }
    df_desc = pd.DataFrame(Dados)
    df_html = df_desc.to_html(index=False)
    df_html_styled = f"<style>td, th {{text-align: center;}}</style>{df_html}"
    st.markdown(df_html_styled, unsafe_allow_html=True)
