# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='temporarydocumenttext',
            name='author',
            field=models.ForeignKey(related_name='temporary_documents', to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='temporarydocumenttext',
            name='document',
            field=models.ForeignKey(related_name='document', to='documents.Document', on_delete=models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='document',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, related_name='polymorphic_documents.document_set+', editable=False, on_delete=models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='attachment',
            name='document',
            field=models.ForeignKey(to='documents.Document', verbose_name='Document', related_name='attachments', on_delete=models.deletion.CASCADE),
        ),
    ]
