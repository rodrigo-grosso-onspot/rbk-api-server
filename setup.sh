#!/bin/bash

echo "🔄 Atualizando pacotes e instalando dependências..."
sudo apt update && sudo apt install -y nginx python3-venv python3-pip gunicorn git

echo "📂 Criando diretório da aplicação..."
sudo mkdir -p /var/app
sudo chown $USER:$USER /var/app

echo "🚀 Clonando ou atualizando o repositório..."
if [ ! -d "/var/app/.git" ]; then
    git clone https://github.com/rodrigo-grosso-onspot/rbk-api-server.git /var/app
else
    cd /var/app
    git pull origin main
fi

cd /var/app

echo "🌍 Configurando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️ Configurando Nginx..."
sudo cp config/nginx.conf /etc/nginx/sites-available/app
sudo ln -sf /etc/nginx/sites-available/app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "🔑 Dando permissão para execução do Gunicorn..."
chmod +x start.sh

echo "🔥 Iniciando aplicação com Gunicorn..."
nohup ./start.sh > output.log 2>&1 &

echo "✅ Setup concluído! Acesse a API em http://127.0.0.1"