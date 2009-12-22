
from south.db import db
from django.db import models
from cthulhubot.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Changing field 'Project.tracker_uri'
        # (to signature: django.db.models.fields.URLField(max_length=255))
        db.alter_column('cthulhubot_project', 'tracker_uri', orm['cthulhubot.project:tracker_uri'])
        
        # Changing field 'ProjectClient.project'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['cthulhubot.Project']))
        db.alter_column('cthulhubot_projectclient', 'project_id', orm['cthulhubot.projectclient:project'])
        
        # Changing field 'ProjectClient.computer'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['cthulhubot.BuildComputer']))
        db.alter_column('cthulhubot_projectclient', 'computer_id', orm['cthulhubot.projectclient:computer'])
        
        # Changing field 'JobAssignment.computer'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['cthulhubot.BuildComputer']))
        db.alter_column('cthulhubot_jobassignment', 'computer_id', orm['cthulhubot.jobassignment:computer'])
        
        # Changing field 'JobAssignment.project'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['cthulhubot.Project']))
        db.alter_column('cthulhubot_jobassignment', 'project_id', orm['cthulhubot.jobassignment:project'])
        
        # Changing field 'JobAssignment.job'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['cthulhubot.Job']))
        db.alter_column('cthulhubot_jobassignment', 'job_id', orm['cthulhubot.jobassignment:job'])
        
        # Changing field 'Buildmaster.project'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['cthulhubot.Project'], unique=True))
        db.alter_column('cthulhubot_buildmaster', 'project_id', orm['cthulhubot.buildmaster:project'])
        
    
    
    def backwards(self, orm):
        
        # Changing field 'Project.tracker_uri'
        # (to signature: models.URLField(max_length=255, verify_exists=False))
        db.alter_column('cthulhubot_project', 'tracker_uri', orm['cthulhubot.project:tracker_uri'])
        
        # Changing field 'ProjectClient.project'
        # (to signature: models.ForeignKey(orm['cthulhubot.Project']))
        db.alter_column('cthulhubot_projectclient', 'project_id', orm['cthulhubot.projectclient:project'])
        
        # Changing field 'ProjectClient.computer'
        # (to signature: models.ForeignKey(orm['cthulhubot.BuildComputer']))
        db.alter_column('cthulhubot_projectclient', 'computer_id', orm['cthulhubot.projectclient:computer'])
        
        # Changing field 'JobAssignment.computer'
        # (to signature: models.ForeignKey(orm['cthulhubot.BuildComputer']))
        db.alter_column('cthulhubot_jobassignment', 'computer_id', orm['cthulhubot.jobassignment:computer'])
        
        # Changing field 'JobAssignment.project'
        # (to signature: models.ForeignKey(orm['cthulhubot.Project']))
        db.alter_column('cthulhubot_jobassignment', 'project_id', orm['cthulhubot.jobassignment:project'])
        
        # Changing field 'JobAssignment.job'
        # (to signature: models.ForeignKey(orm['cthulhubot.Job']))
        db.alter_column('cthulhubot_jobassignment', 'job_id', orm['cthulhubot.jobassignment:job'])
        
        # Changing field 'Buildmaster.project'
        # (to signature: models.ForeignKey(orm['cthulhubot.Project'], unique=True))
        db.alter_column('cthulhubot_buildmaster', 'project_id', orm['cthulhubot.buildmaster:project'])
        
    
    
    models = {
        'cthulhubot.buildcomputer': {
            'basedir': ('django.db.models.fields.CharField', [], {'default': "'/var/buildslaves'", 'max_length': '255'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'ssh_key': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        'cthulhubot.buildmaster': {
            'buildmaster_port': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'}),
            'directory': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.Project']", 'unique': 'True'}),
            'webstatus_port': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'})
        },
        'cthulhubot.command': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'cthulhubot.job': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'cthulhubot.jobassignment': {
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.BuildComputer']"}),
            'config': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.Job']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.Project']"})
        },
        'cthulhubot.project': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'repository_uri': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'tracker_uri': ('django.db.models.fields.URLField', [], {'max_length': '255'})
        },
        'cthulhubot.projectclient': {
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.BuildComputer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cthulhubot.Project']"})
        }
    }
    
    complete_apps = ['cthulhubot']
