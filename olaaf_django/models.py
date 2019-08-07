from django.db import models
from django.core.validators import MinLengthValidator

# Create your models here.

class Repository(models.Model):
  name = models.CharField(max_length=60)

  def __str__(self):
    return self.name

class Edition(models.Model):
  date = models.DateField()
  name = models.CharField(max_length=10)
  repository = models.ForeignKey(Repository, on_delete=models.CASCADE)

  class Meta:
    unique_together = ('repository', 'date')
    indexes = [
      models.Index(fields=['repository', 'date'])
    ]

  def __str__(self):
    return 'repository={}, name={}, date={}'.format(self.repository, self.name, self.date)

class Commit(models.Model):
  sha = models.CharField(max_length=40)
  date = models.CharField(max_length=12)
  revoked = models.BooleanField(default=True)
  edition = models.ForeignKey(Edition, on_delete=models.CASCADE)

  class Meta:
    unique_together = ('edition', 'sha')
    indexes = [
      models.Index(fields=['edition', 'sha'])
    ]

  def __str__(self):
    return 'sha={}, date={}'.format(self.sha, self.date)

class Hash(models.Model):
  BITSTREAM = 'B'
  RENDERED = 'R'
  TYPE_CHOICES = [
    (BITSTREAM, 'Bitstream'),
    (RENDERED, 'Rendered')
  ]
  value = models.CharField(max_length=64, validators=[MinLengthValidator(64)])
  path = models.CharField(max_length=200)
  start_commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='hash_start_commit')
  end_commit = models.ForeignKey(Commit, on_delete=models.SET_NULL, null=True, related_name='hash_end_commit')
  hash_type = models.CharField(max_length=1, choices=TYPE_CHOICES, default=BITSTREAM)
  search_path = models.CharField(max_length=200)

  class Meta:
    unique_together = ('path', 'value')
    indexes = [
      models.Index(fields=['path', 'value'])
    ]

  def __str__(self):
    return 'path={}, hash={}, start_commit={}, end_commit={}'.format(self.path, self.value,
                                                                     self.start_commit,
                                                                     self.end_commit)
