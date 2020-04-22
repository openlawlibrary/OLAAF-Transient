from django.db import models
from django.db.models import Q, Subquery


class PublicationManager(models.Manager):
  def __init__(self, repo_name=None, *args, **kwargs):
    self._repo_name = repo_name
    super().__init__(*args, **kwargs)

  def get_queryset(self):
    if self._repo_name is not None:
      queryset = super().get_queryset().filter(repository__name=self._repo_name, revoked=False)
    # append latest publication's name as field
    return queryset.annotate(
        latest=Subquery(
            queryset
            .order_by('-name')
            .values('name')[:1])
    )

  def by_name_or_latest(self, name=None):
    try:
      queryset = self.get_queryset()

      if name is not None:
        queryset = (
            queryset
            .filter(
                date=Subquery(
                    queryset
                    .filter(name=name)
                    .values_list('date')[:1]
                )
            )
        )

      return queryset.order_by('-name').first()
    except (IndexError, TypeError):
      raise Publication.DoesNotExist

  @classmethod
  def factory(cls, model, repo_name=None):
    manager = cls(repo_name)
    manager.model = model
    return manager


def publication_manager_for_partner(repo_name):
  from olaaf_django.models import Publication
  return PublicationManager.factory(model=Publication, repo_name=repo_name)
