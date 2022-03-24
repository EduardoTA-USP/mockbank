# Generated by Django 3.2.12 on 2022-03-17 00:04

from django.db import migrations, models
import oauth.models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0004_auto_20220316_1053'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='oauth2userconsent',
            name='expires_in',
        ),
        migrations.AddField(
            model_name='oauth2userconsent',
            name='expires_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='oauth2userconsent',
            name='is_authorized',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='oauth2token',
            name='issued_at',
            field=models.IntegerField(default=oauth.models.now_timestamp),
        ),
        migrations.AlterField(
            model_name='oauth2userconsent',
            name='given_at',
            field=models.DateTimeField(null=True),
        ),
    ]
