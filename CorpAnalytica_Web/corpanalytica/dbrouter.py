from .models import *

ANALYTICS_MODELS = [test_table]

class MultiDBRouter(object):

    # 조회의 경우
    def db_for_read(self, model, **hints):

        if model in ANALYTICS_MODELS:
            return 'analytics'
        
        return None

    # 쓰기의 경우
    def db_for_write(self, model, **hints):

        if model in ANALYTICS_MODELS:
            return 'analytics'
        
        return None

    # # 모델 관계 접근의 경우
    # def allow_relation(self, obj1, obj2, **hints):

    #     if obj1._meta.app_label == 'test_table' or obj2._meta.app_label == 'test_table':
    #         return 'analytics'
        
    #     return None

    # # migrate 경로의 경우
    # def allow_migrate(self, db, app_label, model_name=None, **hints):

    #     if app_label == 'test_table':
    #         return db == 'analytics'
        
    #     return None