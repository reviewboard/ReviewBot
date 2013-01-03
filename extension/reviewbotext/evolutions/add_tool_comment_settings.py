from django_evolution.mutations import AddField
from django.db import models

MUTATIONS = [
    AddField('ReviewBotTool', 'ship_it', models.BooleanField, initial=False),
    AddField('ReviewBotTool', 'open_issues', models.BooleanField,
             initial=False),
    AddField('ReviewBotTool', 'comment_unmodified', models.BooleanField,
             initial=False),
]
