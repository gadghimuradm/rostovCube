# Generated by Django 3.1.7 on 2021-04-05 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0018_auto_20210406_0238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='color',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Цвет'),
        ),
        migrations.AlterField(
            model_name='product',
            name='size',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name='Длина стороны'),
        ),
        migrations.AlterField(
            model_name='product',
            name='weight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name='Вес'),
        ),
    ]
