#!/usr/bin/env python
#coding: UTF-8

import os
import sys
import json
import re
import urllib2
import tempfile
import shutil
from datetime import date
from qiniu import Auth, put_file, etag, urlsafe_base64_encode
import qiniu.config

global config, ACCESS_KEY, SECRET_KEY, BUCKET

MD_PIC_CONF ='qiniu.json'

def qn_upload (q, BUCKET, pic):

	qn_pic_key = os.path.basename(pic)
	token = q.upload_token(BUCKET, qn_pic_key, 3600)
	qn_ret, qn_info = put_file(token, qn_pic_key, pic)
	ret = (qn_ret['key'] == qn_pic_key and qn_ret['hash'] == etag(pic))
	qn_pic_link = 'http://%s.qiniudn.com/%s' %(BUCKET, qn_pic_key)
	return ret, qn_pic_link

def process_md_pic (md):

	q = Auth(ACCESS_KEY, SECRET_KEY)

	if not q:
		print 'qiniu auth failure'
		sys.exit(-3)

	today = date.today()
	yyyymmdd = today.strftime('%Y-%m-%d')
	total   = 0
	success = 0
	failure = 0
	ignore  = 0

	with open(md) as f:
		text = f.read()
		new_md = text
		p = re.compile(r'!\[.*\]\((.*)\)')
		for m in p.finditer(text):
			total = total + 1
			old_link = m.group(1)
			print 'process: %s' %old_link
			if not old_link:
				continue

			pic_path = os.path.join(os.path.dirname(md), old_link)
			tmp_pic = tempfile.mkstemp(prefix=('%s_' %yyyymmdd), dir='/tmp')[1]

			if os.path.exists(pic_path):
				shutil.copyfile (pic_path, tmp_pic)
			else:
				# maybe a url
				# already from qiniu
				if old_link.find('%s.qiniudn.com' %BUCKET) != -1:
					ignore = ignore + 1
					print 'already in qiuniu: %s' %(old_link)
					continue

				# omit the query string section like:?arg1=val1&arg2=val2 in the url
				if old_link.find('?') != -1:
					old_link = old_link[: old_link.index('?')]

				con = urllib2.urlopen(old_link)
				if con.getcode() == 200:
					data = con.read()
					print 'download %s to %s' %(old_link, tmp_pic)
					f = open (tmp_pic, 'wb')
					f.write(data)
					f.close()
				else:
					failure = failure + 1
					print 'download error:%s' %(tmp_pic)
					continue

			ret, qn_pic_link = qn_upload (q, BUCKET, tmp_pic)
			if ret is not True:
				failure = failure + 1
				print 'upload failure: %s' %(tmp_pic) 
				continue

			os.remove(tmp_pic)

			new_md = update_pic_link(new_md, old_link, qn_pic_link)
			success = success + 1

	with open(md, 'w') as f:
		f.write(new_md)

	print 'Complete!'
	print ' total   :%d' %(total)
	print ' success :%d' %(success)
	print ' failure :%d' %(failure)
	print ' ignore  :%d' %(ignore)

def update_pic_link (text, old_src, new_src):
	p = re.compile(r'!\[.*\]\(%s.*\)' %old_src)
	new_tag = (u'![](%s)' %(new_src)).encode('UTF-8')
	text = re.sub(p, new_tag, text)
	#print text
	return text

if __name__ == '__main__':

	if len(sys.argv) != 2:
		print 'Usage:%s markdown_file' %(sys.argv[0])
		sys.exit(-1)

	md = sys.argv[1]
	if not os.path.exists(md) or not os.path.isfile(md):
		print '%s is not an exist file' %(md)
		sys.exit(-2)

	config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MD_PIC_CONF)
	if os.path.exists(config_path):
		with open (config_path) as f:
			conf_str = f.read()
			config = json.loads(conf_str)
			ACCESS_KEY = config['ACCESS_KEY']
			SECRET_KEY = config['SECRET_KEY']
			BUCKET = config['BUCKET']

	else:
		print 'Config file:%s Not Found! It should be next to the `qn.py`' % MD_PIC_CONF
		sys.exit(-3)

	bak_md = '%s.bak' %(os.path.abspath(md))
	shutil.copyfile(md, bak_md)
	print 'origin markdown file backup in: %s' %(bak_md)

	process_md_pic (md)
