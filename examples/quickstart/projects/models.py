from django.db import models
from ordloom.components import fields
from ordloom.editor.fields import MDTextField, RichTextField

class Team(models.Model):
    name = models.CharField('团队名称', max_length=80)

    class Meta:
        verbose_name = verbose_name_plural = '团队'

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField('项目名称', max_length=80)
    budget = models.DecimalField('预算', max_digits=14, decimal_places=2, default=0)
    status = fields.SegmentedField('状态', max_length=16, choices=[('draft', '草稿'), ('active', '进行中'), ('done', '已完成')], default='draft')
    teams = fields.TransferField(Team, verbose_name='协作团队', blank=True, titles=['可选团队', '已选团队'])
    body = RichTextField('项目介绍', blank=True)
    notes = MDTextField('协作文档', blank=True)
    settings = models.JSONField('项目配置', default=dict, blank=True)
    cover = models.ImageField('封面', upload_to='projects/covers/', blank=True)
    attachment = models.FileField('附件', upload_to='projects/files/', blank=True)

    class Meta:
        verbose_name = verbose_name_plural = '项目'

    def __str__(self):
        return self.name

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField('任务名称', max_length=100)
    done = models.BooleanField('已完成', default=False)

    class Meta:
        verbose_name = verbose_name_plural = '任务'
