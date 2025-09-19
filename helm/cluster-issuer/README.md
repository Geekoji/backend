> ### 1. Adding the cert-manager repository
>   ```bash
>   helm repo add jetstack https://charts.jetstack.io
>   helm repo update
>   ```

> ### 2. Installing `cert-manager`
>   ```bash
>   helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true --atomic>   
>   ```
> Locally for Docker, you may need to enable additional flags:
>   ```bash
>   helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true --set securityContext.runAsUser=1001 --set securityContext.fsGroup=1001 --set webhook.securityContext.runAsUser=1001 --set webhook.securityContext.fsGroup=1001 --set cainjector.securityContext.runAsUser=1001 --set cainjector.securityContext.fsGroup=1001 --set startupapicheck.securityContext.runAsUser=1001 --set startupapicheck.securityContext.fsGroup=1001 --atomic
>   ```

> ### 3. Creating a ClusterIssuer and Cloudflare API Token secret
>   ```shell
>   cd helm/cluster-issuer
>   helm secrets upgrade --install cluster-issuer . -f values.yaml -f secrets.enc.yaml --namespace cert-manager --atomic
>   ```
