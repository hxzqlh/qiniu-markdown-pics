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
import validators

global config

MD_PIC_CONF ='qiniu.json'

def qn_upload (q, bucket, pic):

    ret = False
    qn_pic_key = os.path.basename(pic)
    token = q.upload_token(bucket, qn_pic_key, 3600)
    qn_ret, qn_info = put_file(token, qn_pic_key, pic)
    if not qn_ret:
        print qn_info
    else:
        ret = (qn_ret['key'] == qn_pic_key and qn_ret['hash'] == etag(pic))
    qn_pic_link = 'http://%s.qiniudn.com/%s' %(bucket, qn_pic_key)
    return ret, qn_pic_link

def process_md_pic (md):

    q = Auth(config['ACCESS_KEY'], config['SECRET_KEY'])
    if not q:
        print 'qiniu auth failure'
        sys.exit(-3)

    today = date.today()
    yyyymmdd = today.strftime('%Y-%m-%d')
    total, success, failure, ignore  = 0 , 0, 0, 0

    with open(md) as f:
        text = f.read()
        new_md = text
        p = re.compile(r'!\[.*\]\((.*)\)')
        for m in p.finditer(text):
            total = total + 1
            old_link = m.group(1)
            print '%d, process: %s' % (total, m.group())
            if not old_link:
                print 'empty pic path, ignore'
                ignore = ignore + 1
                continue

            pic_path = os.path.join(os.path.dirname(md), old_link)

            if os.path.exists(pic_path):
                tmp_pic = tempfile.mkstemp(prefix=('%s_' %yyyymmdd))[1]
                shutil.copyfile (pic_path, tmp_pic)
            else:
                if validators.url(old_link) is not True:
                    ignore = ignore + 1
                    print 'invalid url, ignore'
                    continue

                # maybe a url
                # already from qiniu
                if old_link.find('%s.qiniudn.com' %config['BUCKET']) != -1:
                    ignore = ignore + 1
                    print 'already in qiuniu, ignore'
                    continue

                # omit the query string section like:?arg1=val1&arg2=val2 in the url
                if old_link.find('?') != -1:
                    old_link = old_link[: old_link.index('?')]

                tmp_pic = tempfile.mkstemp(prefix=('%s_' %yyyymmdd))[1]
                con = urllib2.urlopen(old_link)
                if con.getcode() == 200:
                    data = con.read()
                    f = open (tmp_pic, 'wb')
                    f.write(data)
                    f.close()
                else:
                    failure = failure + 1
                    os.remove(tmp_pic)
                    print 'download failure'
                    continue

            ret, qn_pic_link = qn_upload (q, config['BUCKET'], tmp_pic)
            if ret is not True:
                failure = failure + 1
                os.remove(tmp_pic)
                print 'upload failure' 
                continue

            os.remove(tmp_pic)

            new_md = update_pic_link(new_md, old_link, qn_pic_link)
            print 'success'
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

    else:
        print 'Config file:%s Not Found! It should be next to the `qn.py`' % MD_PIC_CONF
        sys.exit(-3)

    bak_md = '%s.bak' %(os.path.abspath(md))
    shutil.copyfile(md, bak_md)
    print 'origin markdown file backup in: %s' %(bak_md)

    process_md_pic (md)

    os.remove (bak_md)
