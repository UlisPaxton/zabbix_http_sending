# Отправка данных в Zabbix по Http
Написано на основе статьи https://habr.com/ru/post/253799/

Installation:
- разместить файл index.php на сервере zabbix в /var/www/html
- проверить наличие приложения/usr/bin/zabbix_sender
- файл main.py разместить в целевой системе.
- в main.py указать значения LOG_DIRECTORY, ZABBIX_HOST, MONITORED_HOST 
- импортировать шаблон zbx_export_templates.xml на сервер Zabbix
- натянуть шаблон указанный хост

