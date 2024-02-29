import streamlit as st
import locale
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime
from fpdf import FPDF
import base64
from io import BytesIO
from babel.numbers import format_currency

# CSS to inject contained in a string
css = """
<style>
    /* This ensures that the navigation bar is styled */
    header {
        visibility: hidden;
    }
    /* This targets the main block area */
    .block-container {
        background-color: #f0f0f0;
    }
    /* This targets the entire app after Streamlit's default styles */
    .stApp {
        background-color: #f0f0f0;
    }
    /* This will style the main content area */
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
    /* Center the title in the container */
    .stApp .main .block-container h1 {
        text-align: center;
    }
    /* Additional styling can be added here for specific elements */
</style>
"""

# Inject custom CSS with markdown
st.markdown(css, unsafe_allow_html=True)

st.title("Parcelar Auto de Infração")
num_max_parcelas = 0 
data_inicio = st.date_input("Data do requerimento", datetime.today())

    
with st.expander("Preencher requerimento", expanded=True):
    st.subheader("Do Autuado")
    nome_completo = st.text_input("Nome completo:")
    cpf = st.text_input("N° do CPF:")
    endereco = st.text_input("Endereço:")
    municipio = st.text_input("Município:")
    N_auto = st.text_input("Numero do Auto de Infração:")
    # valor_upf = st.text_input("Valor da UPF:", value="113,61")  # Valor padrão para evitar erro
    col1, col2, col3 = st.columns(3)
    with col1:
        valor_upf = st.text_input("Valor da UPF:", value="113,61")  # Assume um valor padrão para evitar erro
    with col2:
        qtd_upf_por_animal = st.number_input("Qtd UPF por animal:", min_value=0.0, step=0.5, value=2.5)  # Assume um valor padrão para evitar erro
    with col3:
        qtd_upf_por_parcela = st.number_input("Qtd mínima de UPF por parcela:", min_value=0.0, step=0.5, value=3.0)  # Assume um valor padrão para evitar erro
    
    n_animais = st.number_input("Número de Animais:", min_value=0, step=1)

    def converter_valor_para_float(valor_formatado):
        return float(valor_formatado.replace('R$', '').replace('.', '').replace(',', '.'))

    try:
        valor_upf_float = float(valor_upf.replace(",", "."))
        total_upf = n_animais * qtd_upf_por_animal * valor_upf_float
        # total_upf_reais = converter_valor_para_float(locale.currency(total_upf, grouping=True))
        total_upf_reais = format_currency(total_upf, 'BRL', locale='pt_BR')

        # st.metric(label="Valor do Auto", value=locale.currency(total_upf, grouping=True))
        valor_formatado = format_currency(total_upf, 'BRL', locale='pt_BR')
        st.metric(label="Valor do Auto", value=valor_formatado)
    except ValueError:
        st.error("Por favor, insira um número válido para o Valor da UPF.")
        total_upf_reais = 0

    prazo_defesa = st.radio("No prazo de defesa até 30 dias?", ('Sim', 'Não'))
    coluna_desconto = "Desconto Concedido (Integral)" if prazo_defesa == 'Sim' else "Desconto Concedido (metade)"
    min_valor_parcela = qtd_upf_por_parcela * valor_upf_float
    num_max_parcelas = int(total_upf // min_valor_parcela) if total_upf >= min_valor_parcela else 0
    num_max_parcelas = min(num_max_parcelas, 31)  # Limita o número máximo de parcelas a 30
   
    num_max_parcelas = min(num_max_parcelas, 30) 
    mensagem = f"É possível parcelar em até {num_max_parcelas} vezes, respeitando o valor mínimo de R$ {min_valor_parcela:.2f} por parcela." if num_max_parcelas > 0 else f"O valor total é menor que o mínimo exigido para uma parcela: {min_valor_parcela:.2f}."
    
    
    
    st.write(mensagem)

    if num_max_parcelas > 0:
        parcelas = list(range(1, num_max_parcelas + 1))
        # valores_iniciais = [locale.currency(total_upf, grouping=True) for _ in range(num_max_parcelas)]
        valores_iniciais = [format_currency(total_upf, 'BRL', locale='pt_BR') for _ in range(num_max_parcelas)]

        data = {
             "Quantidade de Parcelas": range(1, 32),
             "Desconto Concedido (Integral)": [20, 12, 11.5, 11, 10.5, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2, 1.75, 1.5, 1.25, 1, 0.75, 0.5, 0.25, 0,0],
             "Desconto Concedido (metade)": [10, 6, 5.75, 5.5, 5.25, 5, 4.75, 4.5, 4.25, 4, 3.75, 3.5, 3.25, 3, 2.75, 2.5, 2.25, 2, 1.75, 1.5, 1.25, 1, 0.875, 0.75, 0.625, 0.5, 0.375, 0.25, 0.125, 0,0]
          }
        df_parcelas = pd.DataFrame(data)
    
        # Calcula o valor com desconto para cada parcela
        df_parcelas['Valor com Desconto'] = total_upf * (1 - df_parcelas[coluna_desconto] / 100)

        # Depois, para exibição ou outra necessidade, formate esses valores usando Babel
        df_parcelas['Valor da Parcela'] = df_parcelas['Valor com Desconto'] / df_parcelas['Quantidade de Parcelas']
   
        df_parcelas['Desconto Concedido'] = total_upf - df_parcelas['Valor com Desconto']

        # Aplica a formatação de moeda para exibição
        df_parcelas['Valor com Desconto Formatado'] = df_parcelas['Valor com Desconto'].apply(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
                   
        # Formatação final para moeda
        for coluna in ['Valor com Desconto', 'Valor da Parcela', 'Desconto Concedido']:
            df_parcelas[coluna] = df_parcelas[coluna].apply(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
       # Limitando o DataFrame a um máximo de 30 linhas antes de exibir
       
        df_parcelas = df_parcelas.head(num_max_parcelas)
        # Adicionando uma linha em branco para garantir a exibição completa da última linha
        linha_branco = pd.DataFrame([['' for _ in range(len(df_parcelas.columns))]], columns=df_parcelas.columns)
        df_parcelas = pd.concat([df_parcelas, linha_branco], ignore_index=True)
        
        # df_parcelas.rename(columns={'Quantidade de Parcelas': 'Qtd Parcelas'}, inplace=True)
        df_parcelas = df_parcelas[['Quantidade de Parcelas', 'Desconto Concedido', 'Valor com Desconto', 'Valor da Parcela']]
        gb = GridOptionsBuilder.from_dataframe(df_parcelas)

        # Ocultar colunas "Desconto Concedido (Integral)" e "Desconto Concedido (metade)"
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
        gb.configure_column("Desconto Concedido (Integral)", hide=True)
        gb.configure_column("Desconto Concedido (metade)", hide=True)

        # Habilita a seleção com checkboxes
        gb.configure_selection('single', use_checkbox=True, groupSelectsChildren=True)

        # Construir as opções do grid
        grid_options = gb.build()
        df_parcelas.reset_index(inplace=True)
        # Exibindo o DataFrame com AG Grid
        grid_response = AgGrid(
            df_parcelas,
            gridOptions=grid_options,
            height=300,
            width='100%',
            data_return_mode='AS_INPUT',
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=False,
            theme='streamlit',  # Verifique se 'streamlit' é um tema suportado na versão do pacote que você está usando
            allow_unsafe_jscode=True,  # Permite a execução de JavaScript (se necessário)
        )

        # Obtendo as linhas selecionadas
        selected = grid_response['selected_rows']
        selected_df = pd.DataFrame(selected)
        # data_inicio = st.date_input("Data do requerimento", datetime.today())
    
        # Verifica se alguma parcela foi selecionada
        if not selected_df.empty:
            # Obtém o número de parcelas e o valor de cada uma a partir do DataFrame selecionado
            num_parcelas = selected_df.iloc[0]['Quantidade de Parcelas']  # Assume que a seleção é única
            valor_parcela = selected_df.iloc[0]['Valor da Parcela']
            
            # Formatar o valor da parcela para float
            valor_parcela = converter_valor_para_float(valor_parcela)

            # Lista para armazenar os dados das parcelas selecionadas
            dados_parcelas_selecionadas = []

            # Preenche a lista com os dados das parcelas selecionadas
            for i in range(1, num_parcelas + 1):
               
                data_vencimento = data_inicio + pd.DateOffset(months=i - 1)  # Subtrai 1, pois a contagem começa do zero
                dados_parcelas_selecionadas.append({
                    'Parcela': i,
                    'Valor da Parcela': f"R$ {valor_parcela:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'Data de Vencimento': data_vencimento.strftime('%d/%m/%Y')
                })

            # Cria um DataFrame a partir da lista de dados
            parcelas_selecionadas_df = pd.DataFrame(dados_parcelas_selecionadas).set_index('Parcela')
        else:
            parcelas_selecionadas_df = pd.DataFrame(columns=['Parcela', 'Valor da Parcela', 'Data de Vencimento']).set_index('Parcela')
        if not parcelas_selecionadas_df.empty:
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                st.write('Parcelas Selecionadas:')
                st.dataframe(parcelas_selecionadas_df)
        else:
            # Exibe uma mensagem se não houver parcelas disponíveis
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                st.write("Marque a primeira coluna com a com a quantidade de parcelas escolhidas.")


# Classe personalizada que estende FPDF e inclui numeração de páginas no rodapé
class MyPDF(FPDF):
    def footer(self):
        self.set_y(-15)  # Posiciona o rodapé a 1,5 cm da parte inferior da página
        self.set_font('Arial', 'I', 10)  # Define a fonte para itálico, tamanho 8
        # Adiciona um número de página centralizado
        self.cell(0, 10, 'Página ' + str(self.page_no()), 0, 0, 'C')

def create_pdf(nome_completo, cpf, endereco, municipio, N_auto, data_inicio, df):

    pdf = MyPDF()  # Aqui você deve usar a classe MyPDF em vez de FPDF
    pdf.alias_nb_pages()
    pdf.set_margins(10, 25, 10)  # O segundo valor é a margem superior, ajuste conforme necessário
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Título do documento
    pdf.set_font("Arial", 'B', 12)  # Configura a fonte para Arial, negrito, tamanho 12
    pdf.cell(0, 10, "REQUERIMENTO PARA PARCELAMENTO DE AUTO DE INFRAÇÃO", ln=True, align='C')
    pdf.set_font("Arial", '', 12)  # Volta para Arial normal, tamanho 12
    pdf.ln(10)  # Adiciona uma linha em branco
    
    # Texto do requerimento
    texto_requerimento = (f"  Eu, {nome_completo}, brasileiro(a), portador(a) do CPF Nº {cpf}, "
                          f"domiciliado(a) no endereço {endereco}, município de: {municipio} - RO, "
                          "venho por meio deste instrumento de requerimento, requerer o parcelamento do valor da MULTA aplicada nos autos nº "
                          f"{N_auto}, no valores discriminados nas parcelas e vencimentos abaixo relacionados:")
    pdf.multi_cell(0, 10, texto_requerimento)
    pdf.ln(5)

    soma_parcelas = 0
    
    pdf.set_font("Arial", 'B', 12)  # Configura a fonte para Arial, negrito, tamanho 12
    pdf.cell(0, 10, "Parcelas e Vencimentos:", ln=True)
    pdf.set_font("Arial", '', 12)  # Volta para Arial normal, tamanho 12

    for index, row in df.iterrows():
        valor_limpo = row['Valor da Parcela'].replace('R$', '').replace('.', '').replace(',', '.')
        soma_parcelas += float(valor_limpo)
        parcela_info = f"Parcela {index}: {row['Valor da Parcela']} - Vencimento: {row['Data de Vencimento']}"
        pdf.cell(0, 10, parcela_info, ln=True)

    # Desenhar a linha abaixo das parcelas após o loop
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)

    pdf.set_font("Arial", size=12, style='B')  # Negrito para o total
    total_info = f"Total: R$ {soma_parcelas:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')
    pdf.cell(0, 10, total_info, ln=True, align='R')  # Alinha o total à direita

    # Adicionar espaço de 4 linhas após o total antes de começar a seção de assinatura
    for _ in range(4):
        pdf.ln(10)

    # Desativar quebra de página automática
    pdf.set_auto_page_break(auto=False)

    # Calcular espaço necessário para a seção de assinatura
    assinatura_height = 10 * 4  # 4 linhas com altura de 10 mm cada
    bottom_margin = 10  # Margem inferior de 10 mm

    # Verificar se ainda há espaço suficiente para a seção de assinatura
    if pdf.get_y() + assinatura_height + bottom_margin > pdf.h:
        pdf.add_page()  # Adiciona uma nova página se não houver espaço suficiente

    # Definir a posição Y da seção de assinatura
    pdf.set_y(pdf.get_y() + 10)  # Posiciona a seção de assinatura um pouco mais abaixo
    pdf.set_font("Arial", size=12, style='B')
    width_nome = pdf.get_string_width(nome_completo) + 6  # Aumenta a margem um pouco mais
    x_inicio = (pdf.w - width_nome) / 2  # Centraliza a linha baseada na largura do nome
    y = pdf.get_y()  # Posiciona a linha no local correto
    pdf.line(x_inicio, y, x_inicio + width_nome, y)
  
    pdf.set_font("Arial", size=12, style='B')
    pdf.cell(0, 5, nome_completo, ln=True, align='C')
    # Mover para baixo um pouco para não sobrepor os próximos textos
    pdf.ln(5)  # Pode ajustar a altura conforme necessário

    # Continua com o restante da seção de assinatura
    pdf.set_font("Arial", size=12)  # Resetar o tipo de letra para o restante do texto
    pdf.cell(0, 10, f"CPF: {cpf}", ln=True, align='C')  # Centraliza o CPF
    pdf.cell(0, 10, f"Município: {municipio}", ln=True, align='C')  # Centraliza o município
    pdf.cell(0, 10, f"Data: {data_inicio.strftime('%d/%m/%Y')}", ln=True, align='C')  # Centraliza a data
    
    pdf_bytes = pdf.output(dest='S').encode('latin-1')

    # Retorna o PDF como bytes
    return pdf.output(dest='S').encode('latin-1')  # Retorna o PDF como bytes
# Inicializa a variável pdf_bytes
pdf_bytes = None

# Criação de duas colunas para os botões
col1, col2 = st.columns(2)

# Botão para gerar o PDF na primeira coluna
with col1:
    generate_button = st.button('Gerar Requerimento')

# Quando o botão de geração for pressionado, cria o PDF
if generate_button:
    # Assume que você já tem as variáveis 'nome_completo', 'cpf', 'endereco', 'municipio', 'N_auto', 'data_inicio', 'df' definidas
    pdf_bytes = create_pdf(nome_completo, cpf, endereco, municipio, N_auto, data_inicio, parcelas_selecionadas_df)

# Botão para baixar o PDF na segunda coluna, que só aparece após o PDF ser gerado
with col2:
    if pdf_bytes:
        st.download_button(
            label="Baixar PDF",
            data=pdf_bytes,
            file_name="requerimento_parcelamento.pdf",
            mime="application/pdf"
        )

# Converter o DataFrame para HTML e aplicar o estilo CSS para centralizar os textos nas células
import streamlit as st
import pandas as pd

# Dados para o DataFrame.
Dados = {
    "Quantidade de Parcelas": range(1, 31),
    "Desconto Concedido (Integral)": [20, 12, 11.5, 11, 10.5, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2, 1.75, 1.5, 1.25, 1, 0.75, 0.5, 0.25, 0],
    "Desconto Concedido (metade)": [10, 6, 5.75, 5.5, 5.25, 5, 4.75, 4.5, 4.25, 4, 3.75, 3.5, 3.25, 3, 2.75, 2.5, 2.25, 2, 1.75, 1.5, 1.25, 1, 0.875, 0.75, 0.625, 0.5, 0.375, 0.25, 0.125, 0]
}       
df = pd.DataFrame(Dados)        

# Converter o DataFrame para HTML e aplicar o estilo CSS.
df_html = df.to_html(index=False)
df_html_styled = f"<style>td, th {{text-align: center;}}</style>{df_html}"

left_spacer, df_col, right_spacer = st.columns([2, 6, 2])

with df_col:  # Centraliza a tabela na coluna do meio.
    st.write("Tabela de Descontos")  # Título para a tabela de descontos
    # Usar st.markdown para exibir o DataFrame com HTML e estilos aplicados
    st.markdown(df_html_styled, unsafe_allow_html=True)