# Functionality
 
自动检测 `Markdown` 文件中所有的图片链接，将原始图片上传到七牛云存储并修改图片源。

Atomatically detect all of image tags in a `Markdown` file, upload those origin pictures content to `Qiniu`(http://www.qiniu.com/) cloud space and modify the image link in `()`

pictrue tag may be like:

```
![may be some info](local relative path)
![](local absolute path)
![](network url address)
```

## Prerequisite

```
pip install qiniu
pip install validators
```

## Usage

* The `qiniu.json` config file must be next to the `qn.py`, content format:

```
{
    "ACCESS_KEY": "your qiniu access key",
    "SECRET_KEY": "your qiniu secret key",
    "BUCKET": "your qiniu bucket"
}
```

* run `./qn.py markdownfile`
