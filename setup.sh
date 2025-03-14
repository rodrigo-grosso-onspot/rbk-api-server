#!/bin/bash

echo "Instalando dependências..."
sudo apt update && sudo apt install -y nginx python3-venv python3-pip gunicorn

echo "Configurando Nginx..."
sudo cp config/nginx.conf /etc/nginx/sites-available/app
sudo ln -sf /etc/nginx/sites-available/app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "Configurando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Dando permissão para execução do Gunicorn..."
chmod +x start.sh

echo "Iniciando aplicação com Gunicorn..."
nohup ./start.sh > output.log 2>&1 &

echo "Setup concluído! Acesse a API em http://127.0.0.1"
