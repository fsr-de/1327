from django.core.validators import RegexValidator
from django.db import models


class HexColorModelField(models.CharField):

	def __init__(self, *args, **kwargs):
		kwargs['max_length'] = 7
		super(HexColorModelField, self).__init__(*args, **kwargs)

	def to_python(self, value):
		" Normalize hex color to 6 digits"
		if value is None:
			return None
		if value[0] == '#' and len(value) == 4:
			return '#' + value[1] * 2 + value[2] * 2 + value[3] * 2
		return value

	default_validators = [RegexValidator("^#[0-9a-fA-F]{6}$")]
