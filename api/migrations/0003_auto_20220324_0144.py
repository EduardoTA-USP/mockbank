# Generated by Django 3.2.12 on 2022-03-24 04:44

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_transaction_transaction_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='cpf',
            field=models.CharField(max_length=14, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='phone_number',
            field=models.CharField(max_length=16, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_date',
            field=models.DateTimeField(default=datetime.datetime(2022, 3, 24, 4, 44, 52, 382117, tzinfo=utc)),
        ),
    ]
