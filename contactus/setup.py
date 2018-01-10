from setuptools import setup

setup(
  name='contactus',
  packages=['contactus'],
  include_package_data=True,
  instal_requires=[
    'flask',
    'boto3',
  ]
)
