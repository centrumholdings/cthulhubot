# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'BuildComputer.username'
        db.alter_column('cthulhubot_buildcomputer', 'username', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True))

        # Adding field 'JobAssignment.version'
        db.add_column('cthulhubot_jobassignment', 'version', self.gf('django.db.models.fields.PositiveIntegerField')(default=0), keep_default=False)

        # Changing field 'Buildmaster.api_port'
        db.alter_column('cthulhubot_buildmaster', 'api_port', self.gf('django.db.models.fields.PositiveIntegerField')(unique=True))


    def backwards(self, orm):
        
        # Changing field 'BuildComputer.username'
        db.alter_column('cthulhubot_buildcomputer', 'username', self.gf('django.db.models.fields.CharField')(max_length=40))

        # Deleting field 'JobAssignment.version'
        db.delete_column('cthulhubot_jobassignment', 'version')

        # Changing field 'Buildmaster.api_port'
        db.alter_column('cthulhubot_buildmaster', 'api_port', self.gf('django.db.models.fields.PositiveIntegerField')(unique=True, null=False))


    models = {
        'cthulhubot.buildcomputer': {
            'Meta': {'object_name': 'BuildComputer'},
            'basedir': ('django.db.models.fields.CharField', [], {'default': "'/var/buildslaves'", 'max_length': '255'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'ssh_key': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        },
        'cthulhubot.buildmaster': {
            'Meta': {'object_name': 'Buildmaster'},
            'api_port': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'}),
            'buildmaster_port': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'}),
            'directory': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.Project']", 'unique': 'True'}),
            'webstatus_port': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'})
        },
        'cthulhubot.command': {
            'Meta': {'object_name': 'Command'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'cthulhubot.job': {
            'Meta': {'object_name': 'Job'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'cthulhubot.jobassignment': {
            'Meta': {'object_name': 'JobAssignment'},
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.BuildComputer']"}),
            'config': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.Job']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.Project']"}),
            'version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'cthulhubot.project': {
            'Meta': {'object_name': 'Project'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'repository_uri': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'tracker_uri': ('django.db.models.fields.URLField', [], {'max_length': '255'})
        },
        'cthulhubot.projectclient': {
            'Meta': {'object_name': 'ProjectClient'},
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.BuildComputer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.Project']"})
        }
    }

    complete_apps = ['cthulhubot']
