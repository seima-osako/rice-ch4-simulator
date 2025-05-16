#!/usr/bin/env bash
set -eux
export DEBIAN_FRONTEND=noninteractive
export APT_LISTCHANGES_FRONTEND=none

# ----------------------- VARS (injected by templatefile) -----------------------
# shellcheck disable=SC2154
GITHUB_REPO="${github_repo}"
DOMAIN_NAME="${domain_name}"
APP_PORT=${app_port}
# ------------------------------------------------------------------------------

apt-get update -yq
apt-get install -yq software-properties-common git ufw curl build-essential \
                     gdal-bin libgdal-dev libproj-dev libgeos-dev libhdf5-dev
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -yq
apt-get install -yq python3.12 python3.12-venv python3.12-dev python3-pip


mkdir -p /opt/app
if [ ! -d /opt/app/src ]; then
  git clone --depth 1 "${GITHUB_REPO}" /opt/app/src
fi

python3.12 -m venv /opt/app/venv
. /opt/app/venv/bin/activate
pip install --upgrade pip
pip install \
  folium geopandas h5netcdf netcdf4 pandas plotly \
  streamlit streamlit-folium streamlit-on-hover-tabs xarray

cat >/etc/systemd/system/streamlit.service <<EOF
[Unit]
Description=Streamlit App (rice-ch4-simulator)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/app/src
Environment="PATH=/opt/app/venv/bin"
ExecStart=/opt/app/venv/bin/streamlit run rice_ch4_app.py \
  --server.port ${APP_PORT} \
  --server.address 0.0.0.0 \
  --server.enableCORS false
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now streamlit.service

# --- UFW & HTTPS optional ---
ufw allow ${APP_PORT}/tcp
ufw --force enable

if [ -n "${DOMAIN_NAME}" ]; then
  apt-get install -yq nginx certbot python3-certbot-nginx

  cat >/etc/nginx/sites-available/streamlit <<NGINX
server {
    listen 80;
    server_name ${DOMAIN_NAME};
    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

  ln -sf /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/streamlit
  nginx -t && systemctl restart nginx

  certbot --nginx -d "${DOMAIN_NAME}" --non-interactive --agree-tos \
          -m "admin@${DOMAIN_NAME}" --redirect

  ufw allow 443/tcp
fi

echo "=== user_data.sh completed (port ${APP_PORT}) ==="
