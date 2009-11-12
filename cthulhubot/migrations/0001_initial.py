
from south.db import db
from django.db import models
from cthulhubot.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Project'
        db.create_table('cthulhubot_project', (
            ('id', models.AutoField(primary_key=True)),
            ('name', models.CharField(max_length=40)),
            ('slug', models.CharField(unique=True, max_length=40)),
            ('tracker_uri', models.URLField(max_length=255, verify_exists=False)),
            ('repository_uri', models.TextField()),
        ))
        db.send_create_signal('cthulhubot', ['Project'])
        
        # Adding model 'ProjectClient'
        db.create_table('cthulhubot_projectclient', (
            ('id', models.AutoField(primary_key=True)),
            ('project', models.ForeignKey(orm.Project)),
            ('computer', models.ForeignKey(orm.BuildComputer)),
            ('password', models.CharField(max_length=36)),
        ))
        db.send_create_signal('cthulhubot', ['ProjectClient'])
        
        # Adding model 'Command'
        db.create_table('cthulhubot_command', (
            ('id', models.AutoField(primary_key=True)),
            ('slug', models.CharField(unique=True, max_length=255)),
        ))
        db.send_create_signal('cthulhubot', ['Command'])
        
        # Adding model 'BuildComputer'
        db.create_table('cthulhubot_buildcomputer', (
            ('id', models.AutoField(primary_key=True)),
            ('name', models.CharField(unique=True, max_length=40)),
            ('slug', models.CharField(unique=True, max_length=40)),
            ('description', models.TextField()),
            ('hostname', models.CharField(unique=True, max_length=255)),
            ('username', models.CharField(max_length=40)),
            ('ssh_key', models.TextField(blank=True)),
            ('basedir', models.CharField(default='/var/buildslaves', max_length=255)),
        ))
        db.send_create_signal('cthulhubot', ['BuildComputer'])
        
        # Adding model 'JobAssignment'
        db.create_table('cthulhubot_jobassignment', (
            ('id', models.AutoField(primary_key=True)),
            ('job', models.ForeignKey(orm.Job)),
            ('computer', models.ForeignKey(orm.BuildComputer)),
            ('project', models.ForeignKey(orm.Project)),
            ('config', models.TextField()),
        ))
        db.send_create_signal('cthulhubot', ['JobAssignment'])
        
        # Adding model 'Job'
        db.create_table('cthulhubot_job', (
            ('id', models.AutoField(primary_key=True)),
            ('slug', models.CharField(unique=True, max_length=255)),
        ))
        db.send_create_signal('cthulhubot', ['Job'])
        
        # Adding model 'Buildmaster'
        db.create_table('cthulhubot_buildmaster', (
            ('id', models.AutoField(primary_key=True)),
            ('webstatus_port', models.PositiveIntegerField(unique=True)),
            ('buildmaster_port', models.PositiveIntegerField(unique=True)),
            ('project', models.ForeignKey(orm.Project, unique=True)),
            ('directory', models.CharField(max_length=255, unique=True)),
            ('password', models.CharField(max_length=40)),
        ))
        db.send_create_signal('cthulhubot', ['Buildmaster'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Project'
        db.delete_table('cthulhubot_project')
        
        # Deleting model 'ProjectClient'
        db.delete_table('cthulhubot_projectclient')
        
        # Deleting model 'Command'
        db.delete_table('cthulhubot_command')
        
        # Deleting model 'BuildComputer'
        db.delete_table('cthulhubot_buildcomputer')
        
        # Deleting model 'JobAssignment'
        db.delete_table('cthulhubot_jobassignment')
        
        # Deleting model 'Job'
        db.delete_table('cthulhubot_job')
        
        # Deleting model 'Buildmaster'
        db.delete_table('cthulhubot_buildmaster')
        
    
    
    models = {
        'cthulhubot.project': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '40'}),
            'repository_uri': ('models.TextField', [], {}),
            'slug': ('models.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'tracker_uri': ('models.URLField', [], {'max_length': '255', 'verify_exists': 'False'})
        },
        'cthulhubot.projectclient': {
            'computer': ('models.ForeignKey', ["orm['cthulhubot.BuildComputer']"], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'password': ('models.CharField', [], {'max_length': '36'}),
            'project': ('models.ForeignKey', ["orm['cthulhubot.Project']"], {})
        },
        'cthulhubot.command': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'slug': ('models.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'cthulhubot.buildcomputer': {
            'basedir': ('models.CharField', [], {'default': "'/var/buildslaves'", 'max_length': '255'}),
            'description': ('models.TextField', [], {}),
            'hostname': ('models.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'slug': ('models.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'ssh_key': ('models.TextField', [], {'blank': 'True'}),
            'username': ('models.CharField', [], {'max_length': '40'})
        },
        'cthulhubot.jobassignment': {
            'computer': ('models.ForeignKey', ["orm['cthulhubot.BuildComputer']"], {}),
            'config': ('models.TextField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'job': ('models.ForeignKey', ["orm['cthulhubot.Job']"], {}),
            'project': ('models.ForeignKey', ["orm['cthulhubot.Project']"], {})
        },
        'cthulhubot.job': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'slug': ('models.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'cthulhubot.buildmaster': {
            'buildmaster_port': ('models.PositiveIntegerField', [], {'unique': 'True'}),
            'directory': ('models.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'password': ('models.CharField', [], {'max_length': '40'}),
            'project': ('models.ForeignKey', ["orm['cthulhubot.Project']"], {'unique': 'True'}),
            'webstatus_port': ('models.PositiveIntegerField', [], {'unique': 'True'})
        }
    }
    
    complete_apps = ['cthulhubot']
