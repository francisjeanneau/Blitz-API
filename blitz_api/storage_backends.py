from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class S3MediaStorage(S3Boto3Storage):
	"""
	This class is needed to specify the folder in which media assets will be
	stored in the S3 bucket.
	"""
	location = 'media'
	file_overwrite = False


class S3StaticStorage(S3Boto3Storage):
	"""
	This class is needed to specify the folder in which static assets will be
	stored in the S3 bucket.
	"""
	location = 'static'
