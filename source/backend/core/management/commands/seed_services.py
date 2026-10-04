from django.core.management.base import BaseCommand
from core.models import ServiceResource,SystemConfig

RESOURCES=[
    ('报考流程 · 从筛选到确认','guide','一份离线可查的报考流程指南。','1. 查阅正式招录公告与岗位表。\n2. 完善个人档案，使用资格匹配逐项核对条件。\n3. 收藏目标并比较历年报名情况。\n4. 在官方报名系统提交材料、完成审核和缴费。\n5. 在本应用记录状态、添加考试计划与截止日期。\n注意：本应用的记录不代替官方报名，也不实时同步官方审核结果。',''),
    ('报名材料核对清单','materials','提交前检查身份证明、学历与岗位要求。','通用核对项：有效身份证明、学历学位证明、个人照片、岗位要求的资格证书、工作或基层经历证明、应届身份材料。\n具体材料以当期官方公告为准；不要在咨询正文填写完整身份证号、银行卡号等敏感信息。',''),
    ('资格匹配为什么显示待确认？','faq','了解不确定条件与人工审核的边界。','专业目录、年龄基准日期和基层经历口径可能随公告变化。算法对缺失档案标注“待完善”，对“相关专业”等描述标注“需人工确认”。请联系招录单位核实，不应把匹配结果视为资格审查结论。',''),
    ('研究生招考信息入口','portal','官方入口链接；访问外部网站需要网络。','中国研究生招生信息网提供官方招生信息。此入口不是本应用内置实时数据；当前离线题库与院校样本仅供演示和学习。','https://yz.chsi.com.cn/'),
    ('中国人事考试网入口','portal','官方入口链接；访问外部网站需要网络。','具体考试报名入口请以正式公告为准。此链接仅提供查找信息的官方入口，离线环境下无法打开外部网站。','https://www.cpta.com.cn/'),
    ('本地数据备份与隐私说明','guide','了解数据保存位置和安全备份方法。','所有用户资料、答题记录与报考记录保存在应用目录 data/db.sqlite3。管理员可在系统运行中生成和恢复备份。备份包含个人信息，请妥善保存。恢复前会自动创建安全备份，恢复后所有账号需要重新登录。\n关闭启动器前请先交卷或确认答案已保存。',''),
]

class Command(BaseCommand):
    help='Add missing public-services resources without overwriting user edits.'
    def handle(self,*args,**options):
        if SystemConfig.objects.filter(key='rebuild.services_initialized').exists(): return
        for i,(title,category,summary,content,url) in enumerate(RESOURCES):
            ServiceResource.objects.get_or_create(title=title,defaults={'category':category,'summary':summary,'content':content,'url':url,'sort_order':i})
        SystemConfig.objects.create(key='rebuild.services_initialized',value={'version':2},description='公共服务初始化标记，请勿删除')
        self.stdout.write('公共服务离线指南已初始化。')
