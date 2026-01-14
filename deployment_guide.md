# WFM-Pro Deployment Guide (HTTPS & Domain Name)

This guide explains how to configure your project to use your GoDaddy domain (`wfm-pro.com`) with HTTPS using Let's Encrypt.

## Prerequisite: DNS Configuration (GoDaddy)

1.  Log in to your [GoDaddy Domain Manager](https://dcc.godaddy.com/).
2.  Select your domain `wfm-pro.com`.
3.  Go to **DNS Management**.
4.  Add/Update the following records:
    *   **Type**: `A`
    *   **Name**: `@`
    *   **Value**: `Your_AWS_Public_IP` (e.g., 3.123.45.67)
    *   **TTL**: 600 seconds (or default)
    
    *   **Type**: `CNAME`
    *   **Name**: `www`
    *   **Value**: `wfm-pro.com` (or create another A record pointing to same IP)

## Prerequisite: AWS Security Group

Ensure your EC2 instance allows inbound traffic on ports 80 and 443.
1.  Go to AWS EC2 Console -> Security Groups.
2.  Edit Inbound Rules.
3.  Add Rule: Type `HTTP`, Port `80`, Source `0.0.0.0/0`.
4.  Add Rule: Type `HTTPS`, Port `443`, Source `0.0.0.0/0`.

## Deployment Steps on Server

1.  **Pull the latest code**:
    ```bash
    git pull origin main
    ```

2.  **Update Environment Variables**:
    Edit your `.env` file on the server:
    ```env
    ALLOWED_HOSTS=wfm-pro.com,www.wfm-pro.com,localhost
    CSRF_TRUSTED_ORIGINS=https://wfm-pro.com,https://www.wfm-pro.com
    ```

3.  **Initialize SSL Certificates**:
    We have added a script `init-letsencrypt.sh` to automate the certificate setup.
    
    Make it executable and run it:
    ```bash
    chmod +x init-letsencrypt.sh
    sudo ./init-letsencrypt.sh
    ```
    
    *This script will:*
    - *Download TLS parameters*
    - *Create a dummy certificate to let Nginx start*
    - *Start Nginx*
    - *Request the real certificate from Let's Encrypt*
    - *Reload Nginx*

4.  **Verify**:
    Visit `https://wfm-pro.com`. You should see your application with a secure lock icon.

## Troubleshooting

-   **Nginx fails to start**: Check logs with `docker-compose logs nginx`.
-   **Certificate error**: Ensure DNS has propagated (can take minutes to hours) before running the script.
-   **Application errors**: Check logs `docker-compose logs web`.
