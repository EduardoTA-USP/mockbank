# Generated by Django 3.2.12 on 2022-03-26 15:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='oauth2userconsent',
            old_name='given_at',
            new_name='status_updated_at',
        ),
    ]
