from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Address(models.Model):
	user = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name='addresses',
	)
	full_name = models.CharField(max_length=200)
	phone = models.CharField(max_length=20)
	city = models.CharField(max_length=120)
	address_line = models.CharField(max_length=255)
	postal_code = models.CharField(max_length=20)
	is_default = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-is_default', '-created_at']

	def __str__(self):
		return f'{self.user.username} - {self.city}, {self.address_line}'
