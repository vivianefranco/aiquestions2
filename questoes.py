import os
from dotenv import load_dotenv
import re
from docx import Document
import openai

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar a API do Azure OpenAI
api_key = os.getenv("AZURE_OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URI")  # Endpoint base da API do Azure
deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")  # Nome da implantação do modelo

# Criar cliente OpenAI com Azure
client = openai.AzureOpenAI(
    api_key=api_key,
    api_version="2023-12-01-preview",
    azure_endpoint=base_url
)

# Função para ler arquivos VTT
def ler_arquivo_vtt(caminho):
    with open(caminho, 'r', encoding='utf-8') as arquivo:
        conteudo = arquivo.read()
    return conteudo

# Função para limpar o conteúdo VTT (remover timestamps e formatações)
def limpar_conteudo_vtt(conteudo):
    # Remove timestamps (ex: 00:00:10.000 --> 00:00:12.000)
    conteudo = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\n', '', conteudo)
    # Remove linhas vazias e números de sequência (ex: 1)
    conteudo = re.sub(r'^\d+\n', '', conteudo, flags=re.MULTILINE)
    # Remove espaços em branco no início e no final
    conteudo = conteudo.strip()
    return conteudo

# Função para gerar questões usando a IA
def gerar_questoes(texto):
    prompt_questoes = """
    Elabore 10 questões múltipla-escolha com base nas transcrições. No total, deve haver 3 questões fáceis, 3 difíceis e 4 médias.
    
    Para as questões fáceis, siga os seguintes critérios:
    Essas questões devem testar a habilidade de compreensão dos conteúdos tratados.
    As questões não devem mencionar o texto que deu origem a ela.
    As questões devem possuir quatro alternativas (A, B, C, D), e destaque a alternativa correta.
    Os comandos precisa ser uma frase a ser completada pela opção correta.
    Acrescente um comentário que justifique a resposta correta.
    As opções erradas precisam ser plausíveis.
    Acrescente também uma breve contextualização sobre o tema tratado na questão antes do comando.
    Atente-se ao paralelismo gramatical entre as 4 opções.
    A extensão das 4 opções deve ser similar.
    A resposta correta não deve aparecer na contextualização.
    Evite questões que possam ser respondidas apenas com conhecimentos gerais, bom senso e interpretação de texto.
    
    Para as questões médias, siga os seguintes critérios:
    As questões devem exigir a aplicação dos conceitos apresentados no trecho, em um cenário prático.
    As perguntas devem ser claras e específicas, com quatro alternativas (A, B, C, D) e destaque a alternativa correta.
    Acrescente um comentário que justifique a resposta correta.
    As opções erradas precisam ser plausíveis.
    Acrescente também uma breve contextualização antes do comando.
    O comando deve ser uma frase incompleta a ser completada pela alternativa correta.
    A extensão das 4 opções deve ser similar.
    A resposta correta não deve aparecer na contextualização.
    
    Para as questões difíceis, siga os seguintes critérios:
    As questões devem exigir avaliação crítica sobre o trecho.
    Deve ser uma questão para cada tópico.
    A pergunta deve explorar diferentes perspectivas e incluir quatro alternativas (A, B, C, D), com a resposta correta destacada.
    Acrescente um comentário que justifique a resposta correta.
    As opções erradas precisam ser plausíveis.
    Acrescente também uma breve contextualização antes do comando.
    O comando deve ser uma frase incompleta a ser completada pela alternativa correta.
    A extensão das 4 opções deve ser similar.
    A resposta correta não deve aparecer na contextualização.
    Atente-se ao paralelismo gramatical entre as 4 opções.
    """

    prompt = (
        f"Com base nas transcrições de videoaulas abaixo, gere questões seguindo as diretrizes fornecidas:\n\n"
        f"Diretrizes para criação das questões:\n{prompt_questoes}\n\n"
        f"Transcrição:\n{texto}"
    )

    try:
        response = client.chat.completions.create(
            model=deployment_name,  # Nome da implantação no Azure
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,  # Aumentado para permitir textos mais longos
            temperature=0
        )
        
        questoes_geradas = response.choices[0].message.content.strip()
        return questoes_geradas

    except Exception as e:
        print(f"Erro ao gerar questões: {e}")
        return None

# Função para criar o documento de questões
def criar_documento_questoes(pasta_vtt, caminho_documento):
    doc = Document()

    # Percorre todos os arquivos VTT na pasta
    for nome_arquivo in os.listdir(pasta_vtt):
        if nome_arquivo.endswith('.vtt'):
            caminho_vtt = os.path.join(pasta_vtt, nome_arquivo)
            titulo_capitulo = os.path.splitext(nome_arquivo)[0]  # Remove a extensão .vtt

            # Adiciona o título do capítulo (nome do arquivo sem extensão)
            doc.add_heading(titulo_capitulo, level=3)

            # Lê e limpa o conteúdo do arquivo VTT
            conteudo_vtt = ler_arquivo_vtt(caminho_vtt)
            conteudo_limpo = limpar_conteudo_vtt(conteudo_vtt)

            # Gera questões usando a IA
            questoes_geradas = gerar_questoes(conteudo_limpo)

            if questoes_geradas:
                # Adiciona as questões geradas ao documento
                doc.add_paragraph(questoes_geradas)
            else:
                doc.add_paragraph(f"Não foi possível gerar questões para o arquivo {nome_arquivo}")

    # Salva o documento de questões
    doc.save(caminho_documento)
    print(f"Documento de questões salvo em: {caminho_documento}")

# Caminho da pasta com os arquivos VTT e onde salvar o documento de questões
pasta_vtt = r'C:\Users\viviane.franco\Documents\python\questoes\pasta_vtt'  # Substitua pelo caminho da sua pasta
caminho_documento = os.path.join(pasta_vtt, 'questoes.docx')

# Executa a criação do documento de questões
criar_documento_questoes(pasta_vtt, caminho_documento)
