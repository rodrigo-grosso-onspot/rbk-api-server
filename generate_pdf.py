import os
import time
import logging
import fitz  # PyMuPDF
from urllib.parse import urlparse, unquote
from playwright.sync_api import sync_playwright

# Configuração de logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações - Substitua estas variáveis conforme necessário
URL = "https://app.onspot.travel/rb_new_roadbook/1741686574049x281543307179065340"  # Coloque o URL desejado aqui
PRINT_MODE = True  # True para imprimir, False para não imprimir
ADD_MARGIN = False  # True para adicionar margens ao PDF

def generate_filename(url):
    """Gera um nome de arquivo baseado no URL."""
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    
    # Remove caracteres inválidos para o nome de arquivo
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        path = path.replace(char, '_')
    
    # Cria um nome de arquivo baseado no caminho da URL
    if path and path != '/':
        filename = path.strip('/').replace('/', '_')
    else:
        filename = parsed_url.netloc.replace('.', '_')
    
    # Adiciona timestamp para evitar sobrescritas
    timestamp = int(time.time())
    return f"{filename}_{timestamp}.pdf"

def add_margin_to_pdf(input_pdf_path, output_pdf_path, margin_size=15):
    """
    Adiciona margens a cada página do PDF usando PyMuPDF (fitz).
    Por padrão, margin_size=15 (aproximadamente ~11.25 pontos em cada lado).
    
    Importante: esta função AUMENTA o tamanho da página para acomodar as margens,
    mantendo o tamanho original do conteúdo, em vez de encolher o conteúdo.
    """
    logger.info(f"Adicionando margens ao PDF: {input_pdf_path}")
    try:
        margin_size_pt = margin_size * 0.75  # 1 pt = 1/72 polegada, ~0.75 "pixel" de aproximação        
        original_doc = fitz.open(input_pdf_path)
        margin_doc = fitz.open()

        for page in original_doc:
            # Criar uma nova página com dimensões aumentadas para acomodar as margens
            new_width = page.rect.width + (2 * margin_size_pt)
            new_height = page.rect.height + (2 * margin_size_pt)
            new_page = margin_doc.new_page(width=new_width, height=new_height)
            
            # Mostrar a página original no centro da nova página maior
            new_page.show_pdf_page(
                fitz.Rect(
                    margin_size_pt,
                    margin_size_pt,
                    new_width - margin_size_pt,
                    new_height - margin_size_pt
                ),
                original_doc,
                page.number
            )

        margin_doc.save(output_pdf_path)
        margin_doc.close()
        original_doc.close()
        logger.info("Margens adicionadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao adicionar margens: {str(e)}")
        raise

def scroll_to_bottom(page):
    """
    Rola gradualmente para baixo na página para garantir que todos os elementos sejam carregados.
    """
    logger.info("Iniciando rolagem da página...")
    try:
        page.evaluate(
            """
            () => {
                return new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 100;
                    const timer = setInterval(() => {
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if (totalHeight >= document.body.scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            }
            """
        )
        logger.info("Rolagem concluída.")
    except Exception as e:
        logger.warning(f"Erro durante a rolagem: {str(e)}")

def print_to_pdf(url, print_mode=True, add_margin=True):
    """Acessa a URL e gera um PDF a partir da página usando Playwright."""
    logger.info(f"Iniciando processamento da URL: {url}")
    
    with sync_playwright() as p:
        browser_type = p.chromium
        logger.info("Iniciando navegador Chromium...")
        
        browser = browser_type.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Configurando o timezone para Paris (Europa/Paris)
        context = browser.new_context(
            locale='fr-FR',
            timezone_id='Europe/Paris'
        )
        
        page = context.new_page()
        
        try:
            logger.info("Navegando para a URL...")
            # Timeout aumentado para 20 minutos como no código original
            page.goto(url, timeout=1200000)  # 20 minutos
            
            logger.info("Aguardando estado networkidle...")
            try:
                page.wait_for_load_state("networkidle", timeout=1200000)  # 20 minutos
            except Exception as e:
                logger.warning(f"Timeout esperando networkidle, mas continuando: {str(e)}")
            
            # Rolagem exatamente como no código original
            scroll_to_bottom(page)
            
            if print_mode:
                filename = generate_filename(url)
                final_path = os.path.join(os.getcwd(), filename)
                temp_path = os.path.join(os.getcwd(), f"temp_{filename}")
                
                logger.info(f"Gerando PDF com o nome: {filename}")
                
                # Configuração para impressão em PDF - exatamente como no código original, SEM MARGENS
                pdf_options = {
                    "path": temp_path,
                    "format": "A5",
                    "print_background": True
                }
                
                # Primeiro geramos o PDF sem margens
                logger.info("Gerando PDF sem margens...")
                page.pdf(**pdf_options)
                
                # Depois adicionamos margens se necessário
                if add_margin:
                    logger.info("Aplicando margens ao PDF...")
                    add_margin_to_pdf(temp_path, final_path)
                    # Remover o arquivo temporário após o processamento
                    os.remove(temp_path)
                    logger.info(f"PDF com margens gerado com sucesso e salvo em: {final_path}")
                else:
                    # Se não precisar adicionar margens, apenas move o arquivo
                    os.rename(temp_path, final_path)
                    logger.info(f"PDF sem margens gerado com sucesso e salvo em: {final_path}")
                
                return {
                    "success": True,
                    "filename": filename,
                    "path": final_path
                }
            else:
                logger.info("Modo de impressão desativado, pulando a geração do PDF.")
                return {
                    "success": True,
                    "message": "Impressão não solicitada"
                }
        
        except Exception as e:
            logger.error(f"Erro ao processar a página: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            logger.info("Fechando o navegador.")
            browser.close()

def main():
    """Função principal que executa o processo de geração de PDF."""
    start_time = time.time()
    logger.info("Iniciando o processo de geração de PDF...")
    
    result = print_to_pdf(URL, PRINT_MODE, ADD_MARGIN)
    
    if result["success"]:
        if PRINT_MODE:
            logger.info(f"PDF gerado com sucesso: {result['filename']}")
        else:
            logger.info("Processamento concluído sem geração de PDF (modo de impressão desativado).")
    else:
        logger.error(f"Falha ao gerar o PDF: {result.get('error', 'Erro desconhecido')}")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Processo concluído em {elapsed_time:.2f} segundos.")

if __name__ == "__main__":
    main()