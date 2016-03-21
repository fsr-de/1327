# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(verbose_name='superuser status', help_text='Designates that this user has all permissions without explicitly assigning them.', default=False)),
                ('username', models.CharField(unique=True, max_length=255, verbose_name='User name')),
                ('email', models.EmailField(null=True, verbose_name='Email address', blank=True, max_length=255)),
                ('first_name', models.CharField(null=True, verbose_name='First name', blank=True, max_length=255)),
                ('last_name', models.CharField(null=True, verbose_name='Last name', blank=True, max_length=255)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('groups', models.ManyToManyField(to='auth.Group', verbose_name='groups', related_name='user_set', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_query_name='user', blank=True)),
                ('user_permissions', models.ManyToManyField(to='auth.Permission', verbose_name='user permissions', related_name='user_set', help_text='Specific permissions for this user.', related_query_name='user', blank=True)),
            ],
            options={
                'verbose_name_plural': 'User profiles',
                'verbose_name': 'User profile',
            },
        ),
    ]
