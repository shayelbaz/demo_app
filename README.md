# Demo App
# Pizza-app Helm Chart

Pizza-app is an python app for managing pizza orders written in Flask framework.

# Intruduction

This chart was designed to be deployed on local standalone cluster in HA mode with shared PV.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PV provisioner support in the underlying infrastructure

## Deploy release in local

1. Clone the repo localy.
2. Prepare folder to be mounted as local PV.
3. Deploy the chart as bellow -
    ```console
    kubectl create namespace pizza
    helm template my-release charts/pizza_app --set persistence.local.hostPath.path=/local-folder -n pizza
    ```
4. Open port forward connection via the k8s service - 
     ```console
    kubectl -n pizza port-forward svc/pizza-chart 8081:8080
    ```
6. Place new order via CURL .e.g. - 
    ```console
    curl --location 'http://127.0.0.1:8081/order' \
    --header 'Content-Type: application/json' \
    --data '{
        "pizza-type": "margherita",
        "size": "personal",
        "amount": 3
        }'
    ```
