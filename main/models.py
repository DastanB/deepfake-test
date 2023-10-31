from django.db import models


# Create your models here.
class Order(models.Model):
    target_file = models.FileField(upload_to='static/upload')
    target_face = models.FileField(upload_to='static/upload', null=True, blank=True)


class SourceFile(models.Model):
    file = models.FileField(upload_to='static/upload')
    face = models.FileField(upload_to='static/upload', null=True, blank=True)
    trimmed = models.FileField(upload_to='static/upload', null=True, blank=True)
    preview = models.FileField(upload_to='static/upload', null=True, blank=True)
    preview_deepfaked = models.FileField(upload_to='static/upload', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='source_files', null=True, blank=True)


class ResultFile(models.Model):
    file = models.FileField(upload_to='static/results', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='result_files')
