"""
apps/orchestration/models.py
KnowledgeItem — the documents the LLM can search via SearchKnowledgeBaseTool.
"""
from django.db import models


class KnowledgeItem(models.Model):
    """
    A piece of knowledge the LLM can retrieve via the search tool.
    In production this would be a vector-embedded document chunk.
    For this project, simple text search (icontains) is used.
    """
    title   = models.CharField(max_length=200)
    content = models.TextField()
    source  = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Knowledge Item"

    def __str__(self):
        return self.title
