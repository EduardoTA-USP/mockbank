# Generated by Django 3.2.12 on 2022-03-17 00:35

from django.db import migrations, models
import oauth.models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0006_alter_oauth2token_issued_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oauth2token',
            name='issued_at',
            field=models.IntegerField(default=oauth.models.now_timestamp),
        ),
    ]
