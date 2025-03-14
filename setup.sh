#!/bin/bash

DOMAIN="rbk.onspot.travel"
APP_DIR="/var/app"
NGINX_CONF="/etc/nginx/sites-available/app"
REPO_URL="https://github.com/rodrigo-grosso-onspot/rbk-api-server.git"
EMAIL="hello@onspot.travel"

echo "🔄 Atualizando pacotes e instalando dependências..."
sudo apt update && sudo apt install -y nginx python3-venv python3-pip gunicorn git certbot python3-certbot-nginx

echo "📂 Criando diretório da aplicação..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

echo "🚀 Clonando ou atualizando o repositório..."
if [ ! -d "$APP_DIR/.git" ]; then
    git clone $REPO_URL $APP_DIR
else
    cd $APP_DIR
    git reset --hard
    git pull origin main
fi

cd $APP_DIR

echo "📁 Garantindo que a pasta de uploads existe..."
mkdir -p $APP_DIR/uploads
chmod -R 755 $APP_DIR/uploads
chown -R www-data:www-data $APP_DIR/uploads

echo "🌍 Configurando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️ Configurando Nginx..."
sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

if [ ! -f "$NGINX_CONF" ]; then
    echo "🔧 Criando configuração padrão para o Nginx..."
    sudo tee $NGINX_CONF > /dev/null <<EOL
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 80M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /uploads/ {
        alias $APP_DIR/uploads/;
        autoindex on;
    }
}
EOL
fi

sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "🔐 Gerando certificado SSL..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

echo "🔁 Configurando renovação automática do SSL..."
if ! crontab -l | grep -q "certbot renew"; then
    echo "0 0 * * * certbot renew --quiet" | sudo tee -a /etc/crontab > /dev/null
fi

echo "🔑 Dando permissão para execução do Gunicorn..."
chmod +x start.sh

echo "🔥 Criando e ativando o serviço Gunicorn..."
sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<EOL
[Unit]
Description=Gunicorn instance to serve $DOMAIN
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "✅ Setup concluído! Acesse a API em https://$DOMAIN"gti