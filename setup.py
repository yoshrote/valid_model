from setuptools import setup, find_packages

setup(name='valid_model',
      version='0.3.6',
      description="Generic data modeling and validation",
      long_description="""\
""",
      classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2.7'
      ],
      keywords='',
      author='Joshua Forman',
      author_email='josh@yoshrote.com',
      url='https://github.com/yoshrote/valid_model',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
            'six'
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
