import logging

from south.db import db
from django.db import models
from django.utils.simplejson import loads, dumps
from cthulhubot.models import *


class Migration:
    
    def forwards(self, orm):
        "Write your forwards migration here"

        for assignment in orm.JobAssignment.objects.all():
            config = loads(assignment.config)
            if isinstance(config, list):
                config = {'commands' : config}
            assignment.config = dumps(config)
            assignment.save()
    
    
    def backwards(self, orm):
        "Write your backwards migration here"
        for assignment in orm.JobAssignment.objects.all():
            config = loads(assignment.config)
            if isinstance(config, dict):
                if 'commands' not in config:
                    config = []
                else:
                    if config.keys() != ['commands']:
                        logging.error("We can lose data, config contains not only commands: %s" % str(config))
                    config = config['commands']

            assignment.config = dumps(config)
            assignment.save()
    
    
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
