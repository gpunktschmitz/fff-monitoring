## Debian Dependencies
```bash
apt-get install mysql-server python3-mysqldb python python3 python3-requests python3-lxml python3-pip python3-flask python3-dateutil python3-numpy python3-scipy python3-mapnik python3-pip uwsgi-plugin-python3 nginx
pip3 install wheel pymongo pillow modestmaps simplejson werkzeug
```

## When updating
```bash
apt-get install mysql-server python3-mysqldb python3-mapnik
apt-get uninstall mongodb python-mapnik uwsgi-plugin-python tilestache
pip3 install wheel pillow modestmaps simplejson werkzeug
pip3 uninstall uuid
```

## Prerequisites
* Datenbank in MySQL anlegen
* Git vorbereiten:
```bash
git clone https://github.com/asdil12/fff-monitoring
git clone https://github.com/TileStache/TileStache
cd fff-monitoring
cp ffmap/mysqlconfig.example.py ffmap/mysqlconfig.py
```
* MySQL Zugangsdaten in mysqlconfig.py eintragen


## Installation
```bash
./install.sh
systemctl daemon-reload
systemctl enable uwsgi-ffmap
systemctl enable uwsgi-tiles
systemctl start uwsgi-ffmap
systemctl start uwsgi-tiles
cd ffmap/db/
./init_db.py
# Then apply NGINX Config
cd ../.. # go back to fff-monitoring root directory
./scripts/setupcron.sh
```

## NGINX Config
```nginx
server {
	listen 443 ssl default_server;
	listen [::]:443 ssl default_server;

...

	location / {
		include uwsgi_params;
		uwsgi_pass 127.0.0.1:3031;
		client_max_body_size 30M;
	}

	location /tiles {
		include uwsgi_params;
		uwsgi_pass 127.0.0.1:3032;
	}
	
	location /static/ {
		root /usr/share/ffmap/;
		expires max;
		add_header Cache-Control "public";
	}

...

}
```

## Admin anlegen
* User über WebUI anlegen
* Dann über z.B. phpmyadmin in der Tabelle users 'admin' auf 1 setzen
