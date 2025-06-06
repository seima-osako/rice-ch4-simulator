# rice-ch4-simulator

## Overview

This application allows you to easily estimate the potential reduction in methane emissions from rice paddies by extending mid-season drainage in Japan

- Select a rice paddy polygon from the map
- Enter parameters and calculate
- View results in the sidebar and main screen


![Rice CH4 Simulator application interface](static/demo.png)

## Directory Structure

```
.
├── .gitignore
├── .streamlit/
│   └── config.toml         # Streamlit configuration file
├── .terraform.lock.hcl
├── data/
│   ├── inten_phsc_2021.nc  # GloRice-phsc Intensive rice physical area maps
│   └── prefectures.geojson # Polygon data for prefectures in Japan
├── markdown/
│   └── home_content.md     # Homepage content for the application
├── main.tf                 # Terraform configuration file (infrastructure definition)
├── pyproject.toml          # Python project configuration file
├── README.md               # This file
├── rice_ch4_app.py         # Main Streamlit application
├── rice_ch4_params.py      # Simulation parameter definitions
├── static/                 # Directory for static assets (e.g., images used in the app)
├── style.css               # Stylesheet for the application
├── user_data.sh            # EC2 instance user data script
└── variables.tf            # Terraform variable definitions file
```

## About Files in the `data` Directory

- **`data/inten_phsc_2021.nc`**:
    - Content: Annual data for GloRice-phsc Intensive rice physical area maps.
    - Source: Xie, Hanzhi, et al. "GloRice, a global rice database (v1. 0): I. Gridded paddy rice annual distribution from 1961 to 2021." Scientific Data 12.1 (2025): 182.
    - How to obtain: [Data download link](https://figshare.com/articles/dataset/GloRice_I_Gridded_5-arcmin_paddy_rice_annual_distribution_maps_for_the_years_1961_to_2021/27965832/2)
- **`data/prefectures.geojson`**:
    - Content: Polygon data showing the boundaries of prefectures in Japan.
    - How to obtain: [Data download link](https://japonyol.net/editor/article/47-prefectures-geojson.html)

## How to Run Locally
1.  **Install the required libraries:**
    Install the dependencies listed in `pyproject.toml`.
2.  **Run the Streamlit application:**
    ```bash
    streamlit run rice_ch4_app.py
    ```
    Open `http://localhost:8501` in your browser to view the application.

## How to Run on AWS using Terraform

You can deploy the application on AWS using Terraform.

1.  **Install and configure AWS CLI and Terraform.**
    - [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
    - [Install Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)
    - Configure your AWS credentials (e.g., `aws configure`).
2.  **Review and edit the Terraform configuration files.**
    - Modify variables such as region and instance type in `variables.tf` as needed.
3.  **Deploy with Terraform:**
    ```bash
    # Initialize Terraform configuration
    terraform init

    # Preview the changes to be applied
    terraform plan

    # Apply the configuration to create resources
    terraform apply
    ```
6.  **Verify deployment:**
    Access the public IP address of the EC2 instance (port 8501) displayed in the Terraform output in your browser.
    Example: `http://YOUR_EC2_PUBLIC_IP:8501`
7.  **Destroy resources:**
    If no longer needed, you can delete the created resources with the following command:
    ```bash
    terraform destroy
