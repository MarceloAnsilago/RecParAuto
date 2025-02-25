import streamlit as st
import locale
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime
from babel.numbers import format_currency
import streamlit.components.v1 as components

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

# ================================
# Título Principal
# ================================
st.title("Parcelar Auto de Infração")

# ================================
# Criação de Abas
# ================================
tabs = st.tabs(["Preencher Requerimento", "Tabela de Descontos"])

# ================================
# Função para formatação de moeda
# ================================
def formatar_moeda_br(valor):
    return format_currency(valor, 'BRL', locale='pt_BR')

# ================================
# Aba 1: Preencher Requerimento
# ================================
with tabs[0]:
    # Data do requerimento
    data_inicio = st.date_input("Data do requerimento", datetime.today())

    with st.expander("Preencher requerimento", expanded=True):
        # Form para evitar perda de foco
        with st.form("form_requerimento"):
            st.subheader("Do Autuado")

            # Inicializa os valores no session_state, se não existirem
            for campo in ["nome_completo","cpf","endereco","municipio","N_auto"]:
                if campo not in st.session_state:
                    st.session_state[campo] = ""

            # Campos de texto
            nome_completo = st.text_input(
                "Nome completo:",
                value=st.session_state["nome_completo"]
            )
            cpf = st.text_input(
                "N° do CPF:",
                value=st.session_state["cpf"]
            )
            endereco = st.text_input(
                "Endereço:",
                value=st.session_state["endereco"]
            )
            municipio = st.text_input(
                "Município:",
                value=st.session_state["municipio"]
            )
            N_auto = st.text_input(
                "Número do Auto de Infração:",
                value=st.session_state["N_auto"]
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                valor_upf = st.text_input("Valor da UPF:", value="119,14")
            with col2:
                qtd_upf_por_animal = st.number_input("Qtd UPF por animal:", min_value=0.0, step=0.5, value=2.5)
            with col3:
                qtd_upf_por_parcela = st.number_input("Qtd mínima de UPF por parcela:", min_value=0.0, step=0.5, value=3.0)

            n_animais = st.number_input("Número de Animais:", min_value=0, step=1)

            # Radio para desconto
            prazo_defesa_escolhido = st.radio(
                "No prazo de defesa até 30 dias?",
                ("Sim (Desconto de 20% pra uma parcela)", "Não (Desconto de 10% pra uma parcela)")
            )

            # Botão do form
            submit_form = st.form_submit_button("Aplicar / Atualizar")

        # Se clicar no botão do form, salvamos no session_state e calculamos
        if submit_form:
            st.session_state["nome_completo"] = nome_completo
            st.session_state["cpf"] = cpf
            st.session_state["endereco"] = endereco
            st.session_state["municipio"] = municipio
            st.session_state["N_auto"] = N_auto
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

    # Calcula total fora do form
    valor_upf_float = st.session_state.get("valor_upf_float", 0.0)
    total_upf = st.session_state.get("n_animais",0) * st.session_state.get("qtd_upf_por_animal",0) * valor_upf_float
    if total_upf > 0:
        st.metric(label="Valor do Auto", value=formatar_moeda_br(total_upf))
    else:
        st.write("Valor do Auto: R$ 0,00")

    # Calcula número máximo de parcelas
    if valor_upf_float > 0:
        min_valor_parcela = st.session_state["qtd_upf_por_parcela"] * valor_upf_float
    else:
        min_valor_parcela = 0

    if total_upf >= min_valor_parcela and min_valor_parcela > 0:
        num_max_parcelas = int(total_upf // min_valor_parcela)
    else:
        num_max_parcelas = 0
    num_max_parcelas = min(num_max_parcelas, 30)

    if num_max_parcelas > 0:
        st.write(f"É possível parcelar em até {num_max_parcelas} vezes, respeitando o valor mínimo de R$ {min_valor_parcela:.2f} por parcela.")
    else:
        st.write(f"O valor total é menor que o mínimo exigido para uma parcela: R$ {min_valor_parcela:.2f}.")

    global parcelas_selecionadas_df
    parcelas_selecionadas_df = pd.DataFrame(columns=['Parcela','Valor da Parcela','Data de Vencimento']).set_index("Parcela")

    # Verifica se o desconto é integral ou metade
    if st.session_state.get("prazo_defesa") == "Sim (Desconto de 20% pra uma parcela)":
        coluna_desconto = "Desconto Concedido (Integral)"
    else:
        coluna_desconto = "Desconto Concedido (metade)"

    # ================================
    # NOVO: Expander com AGrid e Legenda
    # ================================
    if num_max_parcelas > 0:
        with st.expander("Opções de Parcelamento", expanded=True):
            # Construímos a tabela AG Grid aqui dentro
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
            if len(data_dict["Desconto Concedido (metade)"]) < len(data_dict["Quantidade de Parcelas"]):
                data_dict["Desconto Concedido (metade)"].append(0)

            df_descontos = pd.DataFrame(data_dict)
            df_descontos["Desconto (%)"] = df_descontos[coluna_desconto].apply(lambda x: f"{x}%")

            df_descontos["Valor com Desconto"] = total_upf * (1 - df_descontos[coluna_desconto]/100)
            df_descontos["Valor da Parcela"] = df_descontos["Valor com Desconto"] / df_descontos["Quantidade de Parcelas"]
            df_descontos["Desconto Concedido"] = total_upf - df_descontos["Valor com Desconto"]

            df_descontos["Valor com Desconto Formatado"] = df_descontos["Valor com Desconto"].apply(formatar_moeda_br)
            for c in ["Valor com Desconto","Valor da Parcela","Desconto Concedido"]:
                df_descontos[c] = df_descontos[c].apply(formatar_moeda_br)

            df_parcelas = df_descontos.head(num_max_parcelas)
            linha_branco = pd.DataFrame([["" for _ in range(len(df_parcelas.columns))]], columns=df_parcelas.columns)
            df_parcelas = pd.concat([df_parcelas, linha_branco], ignore_index=True)
            df_parcelas = df_parcelas[
                ["Quantidade de Parcelas","Desconto (%)","Desconto Concedido","Valor com Desconto","Valor da Parcela"]
            ]

            gb = GridOptionsBuilder.from_dataframe(df_parcelas)
            gb.configure_default_column(
                groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True
            )
            gb.configure_column("Desconto Concedido (Integral)", hide=True)
            gb.configure_column("Desconto Concedido (metade)", hide=True)
            gb.configure_selection('single', use_checkbox=True, groupSelectsChildren=True)
            grid_options = gb.build()
            df_parcelas.reset_index(inplace=True)
            grid_response = AgGrid(
                df_parcelas,
                gridOptions=grid_options,
                height=300,
                width='100%',
                data_return_mode='AS_INPUT',
                update_mode='MODEL_CHANGED',  # reatividade na seleção
                fit_columns_on_grid_load=False,
                theme='streamlit',
                allow_unsafe_jscode=True,
            )

            # Mensagem logo abaixo do AgGrid
            st.write("**Selecione a quantidade de parcelas** na primeira coluna para gerar o requerimento")

            selected = grid_response['selected_rows']
            selected_df = pd.DataFrame(selected)

            if not selected_df.empty:
                num_parcelas_selecionadas = int(selected_df.iloc[0]["Quantidade de Parcelas"])
                discount_row = df_descontos[df_descontos["Quantidade de Parcelas"] == num_parcelas_selecionadas].iloc[0]
                discount_percentage = discount_row[coluna_desconto]

                valor_com_desconto = total_upf * (1 - discount_percentage / 100)
                valor_parcela_final = valor_com_desconto / num_parcelas_selecionadas

                dados_parcelas = []
                for i in range(1, num_parcelas_selecionadas + 1):
                    data_venc = data_inicio + pd.DateOffset(months=i - 1)
                    dados_parcelas.append({
                        "Parcela": i,
                        "Valor da Parcela": f"R$ {valor_parcela_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'),
                        "Data de Vencimento": data_venc.strftime("%d/%m/%Y")
                    })
                parcelas_selecionadas_df = pd.DataFrame(dados_parcelas).set_index("Parcela")

    # ================================
    # Exibir Requerimento (HTML)
    # ================================
    if 'parcelas_selecionadas_df' not in globals():
        parcelas_selecionadas_df = pd.DataFrame(columns=['Parcela','Valor da Parcela','Data de Vencimento']).set_index("Parcela")

    if not parcelas_selecionadas_df.empty:
        # Monta o texto
        nome_completo = st.session_state.get("nome_completo", "")
        cpf = st.session_state.get("cpf", "")
        endereco = st.session_state.get("endereco", "")
        municipio = st.session_state.get("municipio", "")
        N_auto = st.session_state.get("N_auto", "")
        data_label = data_inicio.strftime('%d/%m/%Y')

        # Se não estiverem definidas, fallback
        if 'discount_percentage' not in locals():
            discount_percentage = 0
        if 'valor_com_desconto' not in locals():
            valor_com_desconto = 0
        if 'valor_parcela_final' not in locals():
            valor_parcela_final = 0

        texto_requerimento = f"""
        Eu, {nome_completo}, brasileiro(a), portador(a) do CPF nº {cpf}, residente no endereço {endereco}, município de {municipio},
        venho, por meio deste requerimento, solicitar o parcelamento do Auto de Infração nº {N_auto}, lavrado em {data_label},
        nos termos da legislação vigente.
        """

        # Precisamos do total_upf e num_max_parcelas
        total_upf_float = st.session_state.get("valor_upf_float",0.0)
        total_upf = st.session_state.get("n_animais",0) * st.session_state.get("qtd_upf_por_animal",0) * total_upf_float
        if total_upf > 0 and num_max_parcelas > 0:
            texto_parcelamento = (
                f"O requerente solicitou o parcelamento em {parcelas_selecionadas_df.shape[0]} vezes, conforme a tabela de descontos, "
                f"o que lhe confere o direito a um desconto de {discount_percentage}% sobre o valor inicial. "
                f"Assim, o valor total, que originalmente era de {formatar_moeda_br(total_upf)}, "
                f"passará a ser de {formatar_moeda_br(valor_com_desconto)}, "
                f"distribuído em {parcelas_selecionadas_df.shape[0]} parcelas "
                f"de {formatar_moeda_br(valor_parcela_final)} cada."
            )
        else:
            texto_parcelamento = "Não é possível parcelar, pois o valor total é inferior ao mínimo exigido para uma parcela."

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
        for index, row in parcelas_selecionadas_df.iterrows():
            html += f"""
                    <tr>
                        <td>{index}</td>
                        <td>{row['Valor da Parcela']}</td>
                        <td>{row['Data de Vencimento']}</td>
                    </tr>
            """
        html += f"""
                </table>

                <div class="signature">
                    <p>Segue assinado</p>
                    <p>___________________________</p>
                    <p>{{nome}} - CPF: {{cpf}}</p>
                </div>

                <div class="print-button no-print">
                    <button onclick="window.print()">Imprimir Requerimento</button>
                </div>
            </div>
        </body>
        </html>
        """.replace("{nome}", nome_completo).replace("{cpf}", cpf)
        components.html(html, height=800, scrolling=True)


# --------------------------------
# Aba 2: Tabela de Descontos
# --------------------------------
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
