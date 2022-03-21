# Generated by Django 3.2.12 on 2022-03-17 23:24

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='creditDebitType',
            field=models.TextField(choices=[('CREDIT', 'Crédito no Extrato'), ('DEBIT', 'Débito no Extrato')], default='DEBIT'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, unique=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='first_partie_type_of_sub_account',
            field=models.TextField(choices=[('CHECKING', 'Checking Account'), ('SAVINGS', 'Savings Account')], default='CHECKING'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_date',
            field=models.DateTimeField(default=datetime.datetime(2022, 3, 17, 23, 24, 19, 724703, tzinfo=utc)),
        ),
    ]