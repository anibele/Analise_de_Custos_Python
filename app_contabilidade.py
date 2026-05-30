import pandas as pd
import re
import os
import math
from fpdf import FPDF
import matplotlib.pyplot as plt

def limpar_valor_monetario(valor_str):
    """
    Extrai o valor numérico de strings financeiras.
    Ex: 'R$ 8.000,00' -> 8000.00 | 'R$ 6,00 por unidade' -> 6.00
    """
    if pd.isna(valor_str):
        return 0.0
    numeros = re.findall(r'[\d.,]+', str(valor_str))
    if numeros:
        limpo = numeros[0].replace('.', '').replace(',', '.')
        return float(limpo)
    return 0.0

def classificar_gastos(nome_gasto):
    """
    Retorna a classificação contábil correta baseada no nome do gasto.
    """
    nome_gasto = str(nome_gasto).lower()
    
    if "leite" in nome_gasto or "embalagen" in nome_gasto or "energia" in nome_gasto:
        return "Custo Variável"
    elif "aluguel" in nome_gasto or "salário" in nome_gasto or "depreciação" in nome_gasto:
        return "Custo Fixo"
    elif "comissão" in nome_gasto:
        return "Despesa Variável"
    elif "pró-labore" in nome_gasto or "marketing" in nome_gasto:
        return "Despesa Fixa"
    else:
        return "Não Classificado"

def processar_dados(caminho_arquivo):
    """
    Lê o arquivo Excel, limpa os dados, classifica e calcula as métricas com 
    foco nas regras definidas pelo usuário.
    """
    try:
        df = pd.read_excel(caminho_arquivo)
    except Exception as e:
        print(f"Erro ao ler o arquivo {caminho_arquivo}: {e}")
        return None, None

    df['Valor Calculado (R$)'] = df['Valor Mensal (R$)'].apply(limpar_valor_monetario)
    df['Classificação Correta'] = df['Gasto'].apply(classificar_gastos)

    # --- Variáveis de Produção ---
    volume_producao = 4000
    preco_venda = 25.00

    # --- Separação de Custos e Despesas ---
    custo_variavel_unit = df[df['Classificação Correta'] == 'Custo Variável']['Valor Calculado (R$)'].sum()
    custo_fixo_total = df[df['Classificação Correta'] == 'Custo Fixo']['Valor Calculado (R$)'].sum()
    despesa_variavel_unit = df[df['Classificação Correta'] == 'Despesa Variável']['Valor Calculado (R$)'].sum()

    # --- Fórmulas Específicas do Projeto ---
    
    # 1. Custo Total por Pote: Rateio do Fixo + Variável Unitário
    custo_total_por_pote = (custo_fixo_total / volume_producao) + custo_variavel_unit
    
    # 2. Margem de Contribuição: Preço Venda - Custo Total - Comissão
    margem_contribuicao_unit = preco_venda - custo_total_por_pote - despesa_variavel_unit
    
    # 3. PEC: Custo Fixo Total / Margem (Arredondado para cima, pois não se vende fração de pote)
    pec_unidades = math.ceil(custo_fixo_total / margem_contribuicao_unit)

    # Dicionário de exibição configurado para mostrar apenas os dados solicitados
    metricas = {
        "Volume de Produção (unid.)": f"{volume_producao}",
        "Preço de Venda Unitário": f"R$ {preco_venda:.2f}",
        "Custo Variável Unitário Total": f"R$ {custo_variavel_unit:.2f}",
        "Custo Fixo Total": f"R$ {custo_fixo_total:,.2f}",
        "Custo Total por Pote": f"R$ {custo_total_por_pote:.2f}",
        "Margem de Contribuição Unitária": f"R$ {margem_contribuicao_unit:.2f}",
        "Ponto de Equilíbrio (PEC)": f"{pec_unidades} unidades"
    }

    return df, metricas

def exibir_relatorio_terminal(df, metricas):
    """
    Opção 1: Exibe os resultados limpos e formatados no terminal.
    """
    print("\n" + "="*60)
    print("CLASSIFICAÇÃO DOS GASTOS".center(60))
    print("="*60)
    for index, row in df.iterrows():
        print(f"- {row['Gasto'][:42]:<42} | {row['Classificação Correta']}")
    
    print("\n" + "="*60)
    print("RELATÓRIO FINANCEIRO".center(60))
    print("="*60)
    for chave, valor in metricas.items():
        print(f"{chave:<32} : {valor:>25}")
    print("="*60 + "\n")

def gerar_grafico_pizza(df, nome_arquivo="grafico_temp.png"):
    """
    Gera um gráfico visualizando a composição de onde vai o dinheiro de 1 pote vendido.
    Salva temporariamente para injeção no PDF.
    """
    volume_producao = 4000
    preco_venda = 25.00
    
    custo_variavel_unit = df[df['Classificação Correta'] == 'Custo Variável']['Valor Calculado (R$)'].sum()
    custo_fixo_total = df[df['Classificação Correta'] == 'Custo Fixo']['Valor Calculado (R$)'].sum()
    despesa_variavel_unit = df[df['Classificação Correta'] == 'Despesa Variável']['Valor Calculado (R$)'].sum()
    
    custo_total_por_pote = (custo_fixo_total / volume_producao) + custo_variavel_unit
    margem = preco_venda - custo_total_por_pote - despesa_variavel_unit
    
    # Montagem dos dados
    labels = ['Custo do Produto', 'Comissão', 'Margem de Contribuição']
    valores = [custo_total_por_pote, despesa_variavel_unit, margem]
    cores = ['#ff9999', '#ffcc99', '#99ff99'] # Vermelho (custo), Laranja (comissão), Verde (margem)
    
    plt.figure(figsize=(6, 4))
    plt.pie(valores, labels=labels, autopct='%1.1f%%', startangle=140, colors=cores, wedgeprops={'edgecolor': 'white'})
    plt.title('Composição do Preço de Venda (R$ 25,00)')
    
    plt.tight_layout()
    plt.savefig(nome_arquivo, dpi=150)
    plt.close() # Libera a memória

def gerar_pdf(df, metricas, nome_arquivo="Resultados.pdf"):
    """
    Opção 2: Gera um relatório PDF profissional e com gráficos usando FPDF e Matplotlib.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(190, 10, txt="Relatório Estratégico de Custos - Bella Itália", ln=True, align='C')
    pdf.line(10, 20, 200, 20)
    pdf.ln(10)

    # 1. Tabela de Classificações
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 10, txt="1. Classificação de Gastos", ln=True)
    pdf.set_font("Arial", size=10)
    
    preencher_linha = False
    for index, row in df.iterrows():
        pdf.set_fill_color(245, 245, 245)
        gasto = str(row['Gasto'])[:60]
        classificacao = str(row['Classificação Correta'])
        pdf.cell(130, 8, txt=f"- {gasto}", border=0, fill=preencher_linha)
        pdf.cell(60, 8, txt=classificacao, border=0, ln=True, align='R', fill=preencher_linha)
        preencher_linha = not preencher_linha

    pdf.ln(5)
    
    # 2. Tabela de Resultados
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="2. Indicadores Financeiros", ln=True)
    pdf.set_font("Arial", size=10)

    for chave, valor in metricas.items():
        if "Margem" in chave:
            pdf.set_fill_color(220, 245, 220)
            pdf.set_font("Arial", 'B', 10)
        elif "PEC" in chave:
            pdf.set_fill_color(220, 235, 255)
            pdf.set_font("Arial", 'B', 10)
        else:
            pdf.set_fill_color(250, 250, 250)
            pdf.set_font("Arial", '', 10)
            
        pdf.cell(100, 8, txt=chave, border=1, fill=True)
        pdf.cell(90, 8, txt=valor, border=1, ln=True, align='R', fill=True)

    pdf.ln(5)

    # 3. Gráfico Visual
    nome_grafico_temp = "grafico_composicao.png"
    gerar_grafico_pizza(df, nome_grafico_temp)
    
    # Injeta a imagem no PDF (Centralizado)
    pdf.image(nome_grafico_temp, x=45, w=120)
    
    # Deleta a imagem temporária
    if os.path.exists(nome_grafico_temp):
        os.remove(nome_grafico_temp)

    pdf.output(nome_arquivo)
    print(f"\n[+] Sucesso! Relatório salvo como '{nome_arquivo}' com gráficos.\n")

def salvar_excel(df, metricas, nome_arquivo="Resultados.xlsx"):
    """
    Opção 3: Salva o DataFrame processado e as métricas em abas separadas no Excel.
    """
    colunas_exportar = ['Gasto', 'Valor Mensal (R$)', 'Classificação Correta']
    df_metricas = pd.DataFrame(list(metricas.items()), columns=['Indicador Financeiro', 'Valor Calculado'])
    
    with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
        df[colunas_exportar].to_excel(writer, sheet_name='Classificação', index=False)
        df_metricas.to_excel(writer, sheet_name='Indicadores', index=False)
        
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for col in worksheet.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                worksheet.column_dimensions[col_letter].width = (max_length + 2)

    print(f"\n[+] Sucesso! Planilha salva e formatada como '{nome_arquivo}'.\n")


def menu():
    arquivo_base = "Dados Custos - Sorveteria.xlsx"
    
    print("Iniciando sistema...")
    if not os.path.exists(arquivo_base) and os.path.exists(arquivo_base + " - Página1.csv"):
       arquivo_base = arquivo_base + " - Página1.csv"
       
    df, metricas = processar_dados(arquivo_base)

    if df is None:
        print("Certifique-se de que o arquivo está no mesmo diretório do script.")
        return

    while True:
        print("="*30)
        print(" MENU ".center(30))
        print("="*30)
        print("1 - Exibir Relatório no terminal")
        print("2 - Salvar Relatório em PDF")
        print("3 - Salvar novo XLSX")
        print("4 - Sair")
        print("="*30)
        
        opcao = input("Escolha uma opção: ")

        if opcao == '1':
            exibir_relatorio_terminal(df, metricas)
        elif opcao == '2':
            gerar_pdf(df, metricas)
        elif opcao == '3':
            salvar_excel(df, metricas)
        elif opcao == '4':
            print("\nEncerrando aplicação!\n")
            break
        else:
            print("\nOpção inválida. Tente novamente.\n")

if __name__ == "__main__":
    menu()