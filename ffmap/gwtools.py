#!/usr/bin/python3

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/' + '..'))

from ffmap.mysqltools import FreifunkMySQL
from ffmap.misc import *
from ffmap.config import CONFIG
from flask import request, url_for

import datetime
import time

def import_gw_data(mysql, gw_data):
	if "hostname" in gw_data and "netifs" in gw_data:
		time = utcnow().strftime('%Y-%m-%d %H:%M:%S')
		stats_page = gw_data.get("stats_page","")

		if not stats_page:
			stats_page = None
		newid = mysql.findone("SELECT id FROM gw WHERE name = %s LIMIT 1",(gw_data["hostname"],),"id")
		if newid:
			mysql.execute("""
				UPDATE gw
				SET stats_page = %s, last_contact = %s
				WHERE id = %s
			""",(gw_data["stats_page"],time,newid,))
		else:
			mysql.execute("""
				INSERT INTO gw (name, stats_page, last_contact)
				VALUES (%s, %s, %s)
			""",(gw_data["hostname"],gw_data["stats_page"],time,))
			newid = mysql.cursor().lastrowid
		
		nmacs = {}
		for n in gw_data["netifs"]:
			nmacs[n["netif"]] = n["mac"]
		
		ndata = []
		for n in gw_data["netifs"]:
			if len(n["mac"])<17:
				continue
			if n["netif"].startswith("l2tp"): # Filter l2tp interfaces
				continue
			if "vpnif" in n and n["vpnif"]:
				n["vpnmac"] = nmacs.get(n["vpnif"],None)
			else:
				n["vpnmac"] = None
			
			ndata.append((newid,n["mac"],n["netif"],n["vpnmac"],time,))
		
		mysql.executemany("""
			INSERT INTO gw_netif (gw, mac, netif, vpnmac, last_contact)
			VALUES (%s, %s, %s, %s, %s)
			ON DUPLICATE KEY UPDATE
				gw=VALUES(gw),
				netif=VALUES(netif),
				vpnmac=VALUES(vpnmac),
				last_contact=VALUES(last_contact)
		""",ndata)

		adata = []
		aid = 0
		for a in gw_data["admins"]:
			aid += 1
			adata.append((newid,a,aid,))
		
		mysql.execute("DELETE FROM gw_admin WHERE gw = %s",(newid,))
		mysql.executemany("""
			INSERT INTO gw_admin (gw, name, prio)
			VALUES (%s, %s, %s)
			ON DUPLICATE KEY UPDATE
				prio=VALUES(prio)
		""",adata)
	else:
		writelog(CONFIG["debug_dir"] + "/fail_gwinfo.txt", "{} - Corrupted file.".format(request.environ['REMOTE_ADDR']))

def gw_name(gw):
	if gw["gw"] and gw["gwif"]:
		s = gw["gw"] + " (" + gw["gwif"] + ")"
	else:
		s = gw["mac"]
	return s

def gw_bat(gw):
	if gw["batif"] and gw["batmac"]:
		s = gw["batmac"] + " (" + gw["batif"] + ")"
	else:
		s = "---"
	return s

def delete_unlinked_gws(mysql):
	# Delete entries in gw_* tables without corresponding gw in master table
	
	tables = ["gw_admin","gw_netif"]
	
	for t in tables:
		start_time = time.time()
		mysql.execute("""
			DELETE d FROM {} AS d
			LEFT JOIN gw AS g ON g.id = d.gw
			WHERE g.id IS NULL
		""".format(t))
		print("--- Deleted %i rows from %s: %.3f seconds ---" % (mysql.cursor().rowcount,t,time.time() - start_time))
	mysql.commit()

