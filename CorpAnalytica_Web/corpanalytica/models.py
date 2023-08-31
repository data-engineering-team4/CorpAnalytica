from django.db import models

class corp_basic(models.Model):
    entno = models.CharField(max_length=8, primary_key=True, null=False)
    corpname = models.CharField(max_length=100, null=False)
    code = models.CharField(max_length=6, null=False)
    crno = models.CharField(max_length=13, null=False)
    stock_type = models.CharField(max_length=30, null=True)

    class Meta:
        managed = False
        db_table = 'corp_basic'

    def __str__(self):
        return self.corpname

class corp_detail(models.Model):
    crno = models.CharField(max_length=15, null=False, primary_key=True)
    corpnm = models.CharField(max_length=100, null=False)
    enppbancmpynm = models.CharField(max_length=100)
    enprprfnm = models.CharField(max_length=20)
    corpregmrktdcdnm = models.CharField(max_length=50)
    bzno = models.CharField(max_length=15)
    enpbsadr = models.CharField(max_length=300)
    enpdtadr = models.CharField(max_length=100)
    enphmpgurl = models.CharField(max_length=200)
    enptlno = models.CharField(max_length=30)
    enpestbdt = models.DateField
    smenpyn = models.CharField(max_length=30)
    enpempecnt = models.IntegerField
    empeavgcnwktermctt = models.IntegerField
    enppn1avgslryamt = models.BigIntegerField
    enpmainbiznm = models.CharField(max_length=100)
    fstopegdt = models.DateField
    lastopegdt = models.DateField

    class Meta:
        managed = False
        db_table = 'corp_detail'

    def __str__(self):
        return self.corpnm
    
class corp_keyword(models.Model):
    corpname = models.CharField(max_length=15, null=False, primary_key=True)
    keyword = models.CharField(max_length=100, null=False)

    class Meta:
        managed = False
        db_table = 'corp_keyword'

    def __str__(self):
        return self.corpname
    
class naver_news(models.Model):
    id = models.CharField(max_length=500,primary_key=True)
    code = models.CharField(max_length=6, null=False)
    corpname = models.CharField(max_length=100, null=False)
    title = models.CharField(max_length=500, null=False)
    link = models.CharField(max_length=500, null=False)
    description = models.CharField(max_length=1000)
    pubdate = models.DateField()

    class Meta:
        managed = False
        db_table = 'naver_news'

    def __str__(self):
        return self.id
    
class news_article(models.Model):
    id = models.CharField(max_length=500,primary_key=True)
    corpname = models.CharField(max_length=256, null=False)
    link = models.CharField(max_length=256, null=False)
    article = models.TextField

    class Meta:
        managed = False
        db_table = 'news_article'

    def __str__(self):
        return self.id

class news_keyword(models.Model):
    id = models.CharField(max_length=500,primary_key=True)
    corpname = models.CharField(max_length=50, null=False)
    link = models.CharField(max_length=200, null=False)
    keyword = models.CharField(max_length=300, null=False)
    summary_sentence1 = models.TextField
    summary_sentence2 = models.TextField
    summary_sentence3 = models.TextField

    class Meta:
        managed = False
        db_table = 'news_keyword'

    def __str__(self):
        return self.id

class corp_total_info(models.Model):
    crno = models.CharField(max_length=256, primary_key=True)
    entno = models.CharField(max_length=8)
    corpname = models.CharField(max_length=256)
    public_corpname = models.CharField(max_length=256)
    owner = models.CharField(max_length=256)
    address = models.CharField(max_length=513)
    homepage_url = models.CharField(max_length=256)
    phone_number = models.CharField(max_length=256)
    keyword = models.CharField(max_length=255)
    
    class Meta:
        managed = False
        db_table = 'corp_total_info'

    def __str__(self):
        return self.corpname