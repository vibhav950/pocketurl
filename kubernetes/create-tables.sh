#!/bin/zsh

MYSQL_POD=$(kubectl get pods -l app=mysql -o jsonpath='{.items[0].metadata.name}')

read -s "?Enter password: " MYSQL_PASSWORD

echo "\n"

kubectl exec -i $MYSQL_POD -- env MYSQL_PWD=$MYSQL_PASSWORD mysql -u pocketurl pocketurl_db < ../db/init.sql

kubectl exec -i $MYSQL_POD -- env MYSQL_PWD=$MYSQL_PASSWORD mysql -u pocketurl pocketurl_db -e "SHOW TABLES; DESCRIBE urls;"
