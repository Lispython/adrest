# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

try:
    from django.contrib.auth import get_user_model
except ImportError: # django < 1.5
    from django.contrib.auth.models import User
else:
    User = get_user_model()


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Access'
        db.create_table('adrest_access', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('uri', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('status_code', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('request', self.gf('django.db.models.fields.TextField')()),
            ('response', self.gf('django.db.models.fields.TextField')()),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('adrest', ['Access'])

        # Adding model 'AccessKey'
        db.create_table('adrest_accesskey', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm["%s.%s" % (User._meta.app_label, User._meta.object_name)])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('adrest', ['AccessKey'])

        # Adding unique constraint on 'AccessKey', fields ['user', 'key']
        db.create_unique('adrest_accesskey', ['user_id', 'key'])


    def backwards(self, orm):
        # Removing unique constraint on 'AccessKey', fields ['user', 'key']
        db.delete_unique('adrest_accesskey', ['user_id', 'key'])

        # Deleting model 'Access'
        db.delete_table('adrest_access')

        # Deleting model 'AccessKey'
        db.delete_table('adrest_accesskey')


    models = {
        'adrest.access': {
            'Meta': {'ordering': "['-created_at']", 'object_name': 'Access'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'request': ('django.db.models.fields.TextField', [], {}),
            'response': ('django.db.models.fields.TextField', [], {}),
            'status_code': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'uri': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': True}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'adrest.accesskey': {
            'Meta': {'ordering': "['-created']", 'unique_together': "(('user', 'key'),)", 'object_name': 'AccessKey'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s.%s']"% (User._meta.app_label, User._meta.object_name)})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        "%s.%s" % (User._meta.app_label, User._meta.module_name): {
        'Meta': {'object_name': User.__name__},
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['adrest']
