## Grant execute permissions

```zsh
cd kubernetes
chmod +x *.sh
```

## Deploy the service

```zsh
./deploy.sh
```
> [!NOTE]
> If deploying for the first time you must create the MySQL tables
> ```zsh
> ./create-tables.sh
> ```

## Shut down and cleanup

```zsh
./teardown.sh
```

> [!CAUTION]
> To delete the DB, you must delete te PVC and PV in this order
> ```zsh
> kubectl delete pvc mysql-pvc
> kubectl delete pv mysql-pv
> minikube ssh "rm -rf /mnt/data/mysql/*"
