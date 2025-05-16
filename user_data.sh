#!/usr/bin/env bash
set -eux          # e = exit on error, u = undefined var, x = trace

export DEBIAN_FRONTEND=noninteractive
export APT_LISTCHANGES_FRONTEND=none

# ---------------- Variables injected by templatefile --------------------------
# shellcheck disable=SC2154
GITHUB_REPO="${github_repo}"
DOMAIN_NAME="${domain_name}"   # FQDN for HTTPS (empty = no Nginx/Certbot)
APP_PORT=${app_port}           # Streamlit listen port (default 8501/8051 etc.)
# ------------------------------------------------------------------------------

# ---------------- Base packages & Python 3.12 ---------------------------------
apt-get update -yq
apt-get install -yq --no-install-recommends \
  software-properties-common git ufw curl build-essential \
  gdal-bin libgdal-dev libproj-dev libgeos-dev libhdf5-dev
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -yq
apt-get install -yq python3.12 python3.12-venv python3.12-dev python3-pip

# ---------------- Clone application ------------------------------------------
mkdir -p /opt/app
if [ ! -d /opt/app/src ]; then
  git clone --depth 1 "${GITHUB_REPO}" /opt/app/src
fi

# ---------------- Virtualenv & Python deps ------------------------------------
python3.12 -m venv /opt/app/venv
. /opt/app/venv/bin/activate
pip install --upgrade pip
pip install \
  folium geopandas h5netcdf netcdf4 pandas plotly \
  streamlit streamlit-folium streamlit-on-hover-tabs xarray

# ---------------- systemd unit ------------------------------------------------
cat >/etc/systemd/system/streamlit.service <<EOF
[Unit]
Description=Streamlit App (rice-ch4-simulator)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/app/src
Environment="PATH=/opt/app/venv/bin"
ExecStart=/opt/app/venv/bin/streamlit run rice_ch4_app.py \\
  --server.port ${APP_PORT} \\
  --server.address 0.0.0.0 \\
  --server.enableCORS false
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now streamlit.service

# ---------------- UFW firewall -------------------------------------------------
ufw default deny incoming          # block everything first
ufw default allow outgoing         # allow all egress

ufw allow OpenSSH                  # SSH (22) open
ufw allow ${APP_PORT}/tcp          # expose Streamlit port externally

if [ -n "${DOMAIN_NAME}" ]; then   # if we will run Nginx/HTTPS, open 80/443
  ufw allow 80/tcp
  ufw allow 443/tcp
fi

ufw --force enable                 # enable non-interactively

# ---------------- Optional Nginx + HTTPS --------------------------------------
if [ -n "${DOMAIN_NAME}" ]; then
  apt-get install -yq nginx certbot python3-certbot-nginx

  cat >/etc/nginx/sites-available/streamlit <<NGINX
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX

  ln -sf /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/streamlit
  nginx -t && systemctl restart nginx

  certbot --nginx -d "${DOMAIN_NAME}" \
          --non-interactive --agree-tos -m "admin@${DOMAIN_NAME}" --redirect
fi

echo "=== user_data.sh completed successfully (port ${APP_PORT}) ==="
