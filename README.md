# dict_server
AI vocabulary database and dictionary


### Install
```sh
python3 -m venv venv
source venv/bin/activate
pip install pipenv && pipenv install
scp .env <remote>:~/dict_server
scp dictionary/oxfordstu.db <remote>:~/dict_server/dictionary
```
* #### systemd service
systemd服务的`/usr/lib/systemd/system/monitor.service`文件里只能执行一个脚本，而且这脚本结尾必须是一个持续性的process，不然`.service`会一直重新启动，因为内容有`Restart`，造成错误。\
想要一个`.service`能执行多个脚本，就新创一个第三方脚本来执行多个目标脚本，要注意是这些脚本都是持续process，因此前面执行的脚本运行在后台，不然这第三方脚本会卡在前面持续process的脚本。\
__e.g. (third party ~/cmd.sh):__
```sh
#!/bin/bash
set -e;
# 注意要将前面的process运行在后台，以免脚本运行卡住
nohup bash /home/yoyo/dict_server/cmd.sh > /dev/null &
# 最后维持一个process避免一直重启
bash /home/yoyo/monitor/cmd.sh
```
编辑`sudo vim /usr/lib/systemd/system/monitor.service`
```sh
ExecStart=/home/yoyo/cmd.sh
```
### Nginx
新增path给监听的port：
```config
# sudo vim /etc/nginx/sites-available/cia1099.cloudns.ch
location /dict/ {
        proxy_pass http://localhost:8866/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```