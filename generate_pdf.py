import os
import time
import logging
import fitz  # PyMuPDF
import platform
import sys
from urllib.parse import urlparse, unquote
from playwright.sync_api import sync_playwright

# Configuração de logging mais detalhado (apenas console)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configurações padrão
PRINT_MODE = True  # True para imprimir, False para não imprimir
ADD_MARGIN = False  # True para adicionar margens ao PDF

def log_system_info():
    """Registra informações do sistema para diagnóstico."""
    logger.info("=== INFORMAÇÕES DO SISTEMA ===")
    logger.info(f"Sistema Operacional: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Playwright versão: {sync_playwright.__version__ if hasattr(sync_playwright, '__version__') else 'Desconhecida'}")
    logger.info(f"PyMuPDF versão: {fitz.version if hasattr(fitz, 'version') else 'Desconhecida'}")
    logger.info(f"Diretório atual: {os.getcwd()}")
    logger.info("=============================")

def generate_filename(url):
    """Gera um nome de arquivo baseado no URL."""
    logger.info(f"Gerando nome de arquivo para URL: {url}")
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
    result = f"{filename}_{timestamp}.pdf"
    logger.info(f"Nome de arquivo gerado: {result}")
    return result

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
        logger.info(f"Tamanho da margem em pontos: {margin_size_pt}")
        
        logger.info(f"Abrindo documento original: {input_pdf_path}")
        original_doc = fitz.open(input_pdf_path)
        logger.info(f"Documento original aberto. Páginas: {len(original_doc)}")
        
        logger.info("Criando novo documento para margens")
        margin_doc = fitz.open()
        
        for i, page in enumerate(original_doc):
            logger.info(f"Processando página {i+1}/{len(original_doc)}")
            # Criar uma nova página com dimensões aumentadas para acomodar as margens
            new_width = page.rect.width + (2 * margin_size_pt)
            new_height = page.rect.height + (2 * margin_size_pt)
            logger.info(f"Dimensões originais: {page.rect.width}x{page.rect.height}")
            logger.info(f"Novas dimensões: {new_width}x{new_height}")
            
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
            logger.info(f"Página {i+1} processada com sucesso")

        logger.info(f"Salvando documento com margens: {output_pdf_path}")
        margin_doc.save(output_pdf_path)
        logger.info(f"Fechando documentos")
        margin_doc.close()
        original_doc.close()
        logger.info("Margens adicionadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao adicionar margens: {str(e)}", exc_info=True)
        raise

def scroll_to_bottom(page):
    """
    Rola gradualmente para baixo na página para garantir que todos os elementos sejam carregados.
    """
    logger.info("Iniciando rolagem da página...")
    try:
        logger.info("Executando script de rolagem")
        scroll_start = time.time()
        result = page.evaluate(
            """
            () => {
                return new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 100;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        console.log(`Rolagem: ${totalHeight}px / ${scrollHeight}px`);
                        
                        if (totalHeight >= scrollHeight) {
                            clearInterval(timer);
                            resolve({
                                success: true,
                                totalScrolled: totalHeight,
                                documentHeight: scrollHeight
                            });
                        }
                    }, 100);
                });
            }
            """
        )
        scroll_time = time.time() - scroll_start
        logger.info(f"Rolagem concluída em {scroll_time:.2f} segundos")
        logger.info(f"Resultado da rolagem: {result}")
    except Exception as e:
        logger.warning(f"Erro durante a rolagem: {str(e)}", exc_info=True)

def print_to_pdf(url, print_mode=True, add_margin=True):
    """Acessa a URL e gera um PDF a partir da página usando Playwright."""
    logger.info(f"Iniciando processamento da URL: {url}")
    
    with sync_playwright() as p:
        browser_type = p.chromium
        logger.info("Iniciando navegador Chromium...")
        logger.info("Argumentos do navegador: --no-sandbox, --disable-dev-shm-usage")
        
        browser_start = time.time()
        browser = browser_type.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        logger.info(f"Navegador iniciado em {time.time() - browser_start:.2f} segundos")
        
        # Configurando o timezone para Paris (Europa/Paris)
        logger.info("Configurando contexto do navegador: locale=fr-FR, timezone=Europe/Paris")
        context = browser.new_context(
            locale='fr-FR',
            timezone_id='Europe/Paris'
        )
        
        logger.info("Criando nova página")
        page = context.new_page()
        
        # Adicionar listeners para eventos da página
        page.on("console", lambda msg: logger.info(f"Console da página: {msg.text}"))
        page.on("pageerror", lambda err: logger.error(f"Erro na página: {err}"))
        page.on("request", lambda req: logger.debug(f"Requisição: {req.method} {req.url[:100]}..."))
        page.on("response", lambda res: logger.debug(f"Resposta: {res.status} {res.url[:100]}..."))
        page.on("dialog", lambda dialog: logger.warning(f"Diálogo aberto: {dialog.message}") or dialog.accept())
        
        try:
            logger.info(f"Navegando para a URL: {url}")
            logger.info(f"Timeout configurado: {1200000}ms (20 minutos)")
            
            navigation_start = time.time()
            logger.info("Chamando page.goto()...")
            
            try:
                response = page.goto(url, timeout=1200000)  # 20 minutos
                navigation_time = time.time() - navigation_start
                logger.info(f"Navegação concluída em {navigation_time:.2f} segundos")
                
                if response:
                    logger.info(f"Status da resposta: {response.status}")
                    logger.info(f"Tipo de conteúdo: {response.headers.get('content-type', 'desconhecido')}")
                    logger.info(f"URL final: {page.url}")
                else:
                    logger.warning("Navegação não retornou objeto de resposta")
            except Exception as nav_error:
                logger.error(f"Erro durante navegação: {str(nav_error)}", exc_info=True)
                # Vamos tentar continuar mesmo com erro
                logger.info("Tentando continuar mesmo após erro na navegação...")
            
            # Verificar se a página foi carregada
            try:
                title = page.title()
                logger.info(f"Título da página: {title}")
                
                # Verificar tamanho do conteúdo
                content_size = page.evaluate("() => document.documentElement.outerHTML.length")
                logger.info(f"Tamanho do conteúdo HTML: {content_size} caracteres")
                
                # Verificar altura e largura da página
                dimensions = page.evaluate("""
                    () => ({
                        scrollWidth: document.documentElement.scrollWidth,
                        scrollHeight: document.documentElement.scrollHeight,
                        clientWidth: document.documentElement.clientWidth,
                        clientHeight: document.documentElement.clientHeight,
                        bodyScrollHeight: document.body.scrollHeight
                    })
                """)
                logger.info(f"Dimensões da página: {dimensions}")
            except Exception as check_error:
                logger.error(f"Erro ao verificar estado da página: {str(check_error)}", exc_info=True)
            
            logger.info("Aguardando estado networkidle...")
            try:
                networkidle_start = time.time()
                logger.info("Chamando page.wait_for_load_state('networkidle')...")
                page.wait_for_load_state("networkidle", timeout=1200000)  # 20 minutos
                networkidle_time = time.time() - networkidle_start
                logger.info(f"Networkidle atingido em {networkidle_time:.2f} segundos")
            except Exception as e:
                logger.warning(f"Timeout esperando networkidle, mas continuando: {str(e)}", exc_info=True)
                
                # Verificar requisições pendentes
                try:
                    pending = page.evaluate("""
                        () => {
                            const performance = window.performance;
                            if (!performance || !performance.getEntriesByType) return 'API de Performance não disponível';
                            
                            const resources = performance.getEntriesByType('resource');
                            const pending = resources.filter(r => !r.responseEnd);
                            return {
                                total: resources.length,
                                pending: pending.length,
                                pendingUrls: pending.slice(0, 5).map(p => p.name)
                            };
                        }
                    """)
                    logger.info(f"Requisições pendentes: {pending}")
                except Exception as pe:
                    logger.error(f"Erro ao verificar requisições pendentes: {str(pe)}")
            
            # Rolagem exatamente como no código original
            scroll_to_bottom(page)
            
            if print_mode:
                filename = generate_filename(url)
                final_path = os.path.join(os.getcwd(), filename)
                temp_path = os.path.join(os.getcwd(), f"temp_{filename}")
                
                logger.info(f"Gerando PDF com o nome: {filename}")
                logger.info(f"Caminho temporário: {temp_path}")
                logger.info(f"Caminho final: {final_path}")
                
                # Configuração para impressão em PDF - exatamente como no código original, SEM MARGENS
                pdf_options = {
                    "path": temp_path,
                    "format": "A5",
                    "print_background": True
                }
                logger.info(f"Opções de PDF: {pdf_options}")
                
                # Primeiro geramos o PDF sem margens
                logger.info("Gerando PDF sem margens...")
                try:
                    pdf_start = time.time()
                    page.pdf(**pdf_options)
                    pdf_time = time.time() - pdf_start
                    logger.info(f"PDF gerado em {pdf_time:.2f} segundos")
                    
                    # Verificar se o arquivo foi criado e seu tamanho
                    if os.path.exists(temp_path):
                        file_size = os.path.getsize(temp_path)
                        logger.info(f"Arquivo PDF criado com sucesso. Tamanho: {file_size / 1024:.2f} KB")
                    else:
                        logger.error(f"Arquivo PDF não foi criado: {temp_path}")
                except Exception as pdf_error:
                    logger.error(f"Erro ao gerar PDF: {str(pdf_error)}", exc_info=True)
                    return {
                        "success": False,
                        "error": f"Erro ao gerar PDF: {str(pdf_error)}"
                    }
                
                # Depois adicionamos margens se necessário
                if add_margin:
                    logger.info("Aplicando margens ao PDF...")
                    add_margin_to_pdf(temp_path, final_path)
                    # Remover o arquivo temporário após o processamento
                    logger.info(f"Removendo arquivo temporário: {temp_path}")
                    os.remove(temp_path)
                    logger.info(f"PDF com margens gerado com sucesso e salvo em: {final_path}")
                else:
                    # Se não precisar adicionar margens, apenas move o arquivo
                    logger.info(f"Renomeando arquivo de {temp_path} para {final_path}")
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
            logger.error(f"Erro ao processar a página: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            logger.info("Fechando o navegador.")
            browser.close()

def main():
    """Função principal que executa o processo de geração de PDF."""
    logger.info("="*50)
    logger.info("INICIANDO PROCESSO DE GERAÇÃO DE PDF")
    logger.info("="*50)
    
    # Registrar informações do sistema
    log_system_info()
    
    # Solicitar URL através do console
    logger.info("Digite a URL da página para gerar o PDF:")
    url = input().strip()
    if not url:
        logger.error("URL não fornecida. Encerrando o programa.")
        return
    
    logger.info(f"URL fornecida: {url}")
    
    start_time = time.time()
    logger.info(f"URL alvo: {url}")
    logger.info(f"Modo de impressão: {'Ativado' if PRINT_MODE else 'Desativado'}")
    logger.info(f"Adicionar margens: {'Sim' if ADD_MARGIN else 'Não'}")
    
    result = print_to_pdf(url, PRINT_MODE, ADD_MARGIN)
    
    if result["success"]:
        if PRINT_MODE:
            logger.info(f"PDF gerado com sucesso: {result['filename']}")
            logger.info(f"Caminho completo: {result['path']}")
            
            # Verificar tamanho do arquivo final
            file_size = os.path.getsize(result['path'])
            logger.info(f"Tamanho do arquivo final: {file_size / 1024:.2f} KB")
        else:
            logger.info("Processamento concluído sem geração de PDF (modo de impressão desativado).")
    else:
        logger.error(f"Falha ao gerar o PDF: {result.get('error', 'Erro desconhecido')}")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Processo concluído em {elapsed_time:.2f} segundos.")
    logger.info("="*50)
    logger.info("FIM DO PROCESSO")
    logger.info("="*50)

if __name__ == "__main__":
    main()