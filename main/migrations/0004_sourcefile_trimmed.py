# Generated by Django 4.2.5 on 2023-10-09 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_sourcefile_face'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcefile',
            name='trimmed',
            field=models.FileField(blank=True, null=True, upload_to='static/upload'),
        ),
    ]