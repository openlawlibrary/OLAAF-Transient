from django.db import models
from django.db.models import Q, Subquery


class PublicationQuerySet(models.QuerySet):
  def by_repo_name(self, name):
    return self.filter(repository__name=name)

  def non_revoked(self):
    return self.filter(revoked=False)

  def with_latest_field(self):
    return self.annotate(latest=Subquery(self.order_by('-name').values('name')[:1]))


class PublicationManager(models.Manager):
  def __init__(self, repo_name=None, *args, **kwargs):
    self._repo_name = repo_name
    super().__init__(*args, **kwargs)

  def get_queryset(self):
    queryset = PublicationQuerySet(model=self.model)
    if self._repo_name is not None:
      queryset = queryset.by_repo_name(self._repo_name)
    return queryset

  def by_name_or_latest(self, name=None, strict=False):
    """Return latest partner publication or by name.
    If `strict` is False, it will return the latest publication for a given name
    e.g.
      publications:
        - name=2020-10-10,    date=2020-10-10
        - name=2020-10-10-01, date=2020-10-10

      returns 2020-10-10-01
    """
    try:
      queryset = self.get_queryset().non_revoked().with_latest_field()

      if name:
        if strict:
          queryset = queryset.filter(name=name)
        else:
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

      publication = queryset.order_by('-name').first()
      if publication:
        return publication

      raise self.model.DoesNotExist
    except (IndexError, TypeError):
      raise self.model.DoesNotExist

  def non_revoked(self):
    return self.get_queryset().non_revoked()

  @classmethod
  def factory(cls, model, repo_name=None):
    manager = cls(repo_name)
    manager.model = model
    return manager


def publication_manager_for_partner(repo_name):
  from olaaf_django.models import Publication
  return PublicationManager.factory(model=Publication, repo_name=repo_name)
