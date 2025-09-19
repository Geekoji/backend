# Helm Deployment Guide

This document describes how to install and use Helm with the `helm-secrets` plugin and the `sops` encryption manager to deploy microservices.

---

## 📦 Installation

### 1. Install Helm
Download the latest version from the [official website](https://helm.sh/docs/intro/install/) or use [Chocolatey](https://chocolatey.org/) package manager to install for Windows:

   ```bash
   choco install kubernetes-helm
   ```

Check the version:

   ```bash   
   helm version
   ```

### 2. Install the `helm-secrets` plugin

   ```bash
   helm plugin install https://github.com/jkroepke/helm-secrets
   ```

Check the installation:

   ```bash
   helm secrets --help
   ```

### 3. Install `sops` encryption manager

SOPS is needed for encryption/decryption of secrets.

For Windows (through `choco`):

   ```bash
   choco install sops
   ```

Check the version:

   ```bash
   sops --version
   ```

---

## 📄 Creating a chart

> ### Default chart
> We have a **default chart** `app` that describes the basic structure (`deployment`, `service`, `configmap`, `secret`).
Services are inherited from it through `Chart.yaml`:
>   ```yaml
>   apiVersion: v2
>   name: your-service
>   description: Your microservice
>   version: 0.1.0  # Chart version
>   appVersion: "v7.7.7"  # App version
>   
>   dependencies:
>     - name: service
>       version: "1.0.0"
>       repository: "file://../../../helm/.base-service"
>   ```

> ### 📝 Configuration of variables (`values.yaml`)
> All configuration parameters (non-sensitive data) are passed to the `app.env` section:
>   ```yaml
>   service:
>     env:
>        API_VERSION: "7.7.7"
>        ENV_STATE: "development"
>        POSTGRES_DB: "postgres"
>        POSTGRES_HOST: "postgres"
>        POSTGRES_PORT: 12039
>  ```

> ### 🔑 Configuration of secrets (`secrets.yaml`)
> All sensitive data is stored in the `app.secrets` section:
>   ```yaml
>   service:
>     secrets:
>       POSTGRES_PASSWORD: "__secret__"
>       JWT_PRIVATE_KEY: |
>         -----BEGIN PRIVATE KEY-----
>         ...
>         -----END PRIVATE KEY-----
>       REDIS_PASSWORD: "__secret__"
>       SECRET_KEY: "__secret__"
>   ```

---

## 🔐 Encryption of secrets

The file `secrets.yaml` is **never stored in git** in plain text.
It must always be encrypted. Only `secrets.enc.yaml` is added to the repository.

> ### 🔓 Decrypt secrets
>   ```bash
>   make helm-decrypt <SERVICE>
>   ```
> Decrypt `secrets.enc.yaml` into `secrets.yaml`.


> ### 🔒 Encrypt secrets
>   ```bash
>   make helm-encrypt <SERVICE>
>   ```
> Encrypts `secrets.yaml` into `secrets.enc.yaml`.

---

## 🚀 Deployment

* `SERVICE`: The name of the service, e.g., `auth`, `user`, etc.
* `NAMESPACE`: (Optional) The namespace to deploy the release into. The default namespace is `development`.

> ### 🧩 Install / Update a release
>   ```bash
>   make helm-deploy <SERVICE> [NAMESPACE]
>   ```
> Installs or updates (if already installed) the chart.

> ### 🗑️ Uninstall a release
>   ```bash
>   make helm-uninstall <SERVICE> [NAMESPACE]
>   ```
> Fully removes the release from the namespace.

---

## ✅ Recommendations

* **ConfigMap** -→ `values.yaml` (non-sensitive data)
* **Secret** ----→ `secrets.enc.yaml` (sensitive data)
* Always check the chart after editing:

  ```bash
  make helm-check <SERVICE>
  ```
  
* Use `quotes` for values, except multi-line values like PEM-keys. [Read more here](CHECKLIST.md)