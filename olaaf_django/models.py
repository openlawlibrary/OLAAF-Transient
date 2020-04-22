from django.core.validators import MinLengthValidator
from django.db import models

from olaaf_django.utils import remove_endings

from .managers import publication_manager_for_partner


class LowerCharField(models.CharField):
  def get_prep_value(self, value):
    return str(value).lower()


class PathUrlField(LowerCharField):
  def get_prep_value(self, value):
    value = super().get_prep_value(value)
    return remove_endings(value).rstrip('/').lstrip('/')


class Repository(models.Model):
  name = LowerCharField(max_length=60)

  class Meta:
    verbose_name = "Repository"
    verbose_name_plural = "Repositories"

  def __str__(self):
    return self.name


class Publication(models.Model):
  name = models.CharField(max_length=13)
  date = models.DateField()
  revoked = models.BooleanField(default=False)
  repository = models.ForeignKey(Repository, on_delete=models.CASCADE)

  for_partner = publication_manager_for_partner

  class Meta:
    unique_together = ('repository', 'name')
    indexes = [
        models.Index(fields=['repository', 'name'])
    ]

  def __str__(self):
    return 'repository={}, name={}, date={}, revoked={}'.format(
        self.repository, self.name, self.date, self.revoked)


class Commit(models.Model):
  sha = models.CharField(max_length=40)
  date = models.DateField()
  document = models.CharField(max_length=100)
  revoked = models.BooleanField(default=False)
  publication = models.ForeignKey(Publication, on_delete=models.CASCADE)

  class Meta:
    unique_together = [('publication', 'sha')]  # not ready to add this yet ('date', 'document')]
    indexes = [
        models.Index(fields=['publication', 'sha']),
        models.Index(fields=['date', 'id'])
    ]

  def __str__(self):
    return 'sha={}, date={}'.format(self.sha, self.date)


class Path(models.Model):
  filesystem = models.CharField(max_length=260)
  url = PathUrlField(max_length=260)
  search_path = LowerCharField(max_length=200, null=True)
  citation = LowerCharField(max_length=100, null=True)
  publication = models.ForeignKey(Publication, on_delete=models.CASCADE)

  class Meta:
    unique_together = ('filesystem', 'publication')
    indexes = [
        models.Index(fields=['filesystem', 'publication']),
        models.Index(fields=['url', 'publication'])
    ]

  def __str__(self):
    return 'filesystem path: {}, url={}, citation={}, publication={}, search_path={}'. \
        format(self.filesystem, self.url, self.citation, self.publication, self.search_path)


class Hash(models.Model):
  BITSTREAM = 'B'
  RENDERED = 'R'
  TYPE_CHOICES = [
      (BITSTREAM, 'Bitstream'),
      (RENDERED, 'Rendered')
  ]
  value = models.CharField(max_length=64, validators=[MinLengthValidator(64)])
  path = models.ForeignKey(Path, on_delete=models.CASCADE)
  start_commit = models.ForeignKey(Commit, on_delete=models.CASCADE,
                                   related_name='hash_start_commit')
  end_commit = models.ForeignKey(Commit, on_delete=models.SET_NULL,
                                 null=True, related_name='hash_end_commit')
  hash_type = models.CharField(max_length=1, choices=TYPE_CHOICES, default=BITSTREAM)

  class Meta:
    verbose_name = "Hash"
    verbose_name_plural = "Hashes"

    unique_together = ('path', 'value', 'hash_type', 'start_commit')
    indexes = [
        models.Index(fields=['path', 'value', 'hash_type'])
    ]

  def __str__(self):
    return 'path={}, hash={}, start_commit={}, end_commit={}, type={}'.format(self.path, self.value,
                                                                              self.start_commit,
                                                                              self.end_commit,
                                                                              self.hash_type)
