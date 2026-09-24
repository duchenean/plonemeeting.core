from setuptools import find_packages
from setuptools import setup


version = '6.0.0.dev0'

setup(name='plonemeeting.core',
      version=version,
      description="Official meetings management",
      long_description=open("README.rst").read() + "\n" + open("CHANGES.rst").read(),
      # Get more strings from https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Development Status :: 6 - Mature",
          "Environment :: Web Environment",
          "Framework :: Plone",
          "Framework :: Plone :: 4.3",
          "Intended Audience :: Customer Service",
          "Intended Audience :: Developers",
          "Intended Audience :: End Users/Desktop",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Operating System :: OS Independent",
          "Programming Language :: Other Scripting Engines",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Topic :: Internet :: WWW/HTTP :: Site Management",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: Office/Business",
      ],
      keywords='plone official meetings management egov communesplone imio plonegov',
      author='Gauthier Bastien',
      author_email='gauthier@imio.be',
      url='https://www.imio.be/nos-applications/ia-delib',
      license='GPL',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['plonemeeting'],
      include_package_data=True,
      zip_safe=False,
      extras_require=dict(test=['imio.helpers[test]',
                                'ipdb',
                                'plone.app.testing',
                                'profilehooks',
                                'plone.app.robotframework',
                                'Products.CMFPlacefulWorkflow',
                                'python-magic'],
                          templates=['Genshi', ],
                          # temp backward compat
                          amqp=[]),
      install_requires=[
          'appy > 0.8.0',
          # 'archetypes.schematuning',  # P6 migration: AT-only perf overlay, irrelevant once MeetingItem/MeetingConfig are DX (Stage B/C)
          'beautifulsoup4',
          'natsort',
          'setuptools',
          'Plone',
          'Pillow',
          'collective.behavior.internalnumber',
          # 'collective.ckeditor',  # P6 migration: CKEditor dropped, configure stock TinyMCE in Stage D
          'collective.contact.plonegroup',
          # 'collective.datagridcolumns',  # P6 migration: AT DataGridField column types, no longer needed
          # 'collective.dexteritytextindexer',  # P6 migration: merged into plone.app.dexterity.textindexer
          'collective.js.fancytree',
          'collective.js.jqueryui',
          # 'collective.js.tablednd',  # P6 migration: uses removed includeDependencies directive
          'collective.iconifieddocumentactions',
          'collective.messagesviewlet',
          'collective.upgrade',
          # 'collective.usernamelogger',  # P6 migration: dev-only login event logger; reintroduce as a tiny PAS plugin in Stage D if still wanted
          # 'communesplone.layout',  # P6 migration: dead theme overlay, no Py3 release; reimplement in Stage D if any feature is still needed
          'dexterity.localrolesfield',
          'ftw.labels',
          'imio.annex',
          'imio.pm.locales',
          'imio.dashboard>=2.0',
          'imio.helpers[lxml]',
          'imio.migrator',
          'imio.pyutils',
          # 'imio.zamqp.pm',  # P6 migration: AMQP integration to be reimplemented in Stage D
          'imio.webspellchecker',
          'plone.app.lockingbehavior',
          'plone.app.versioningbehavior',
          'plone.directives.form',
          'plonemeeting.restapi',
          'plonetheme.imioapps',
          'Products.CPUtils',
          # 'Products.DataGridField',  # P6 migration: AT-only, replaced by collective.z3cform.datagridfield
          # 'Products.PasswordStrength',  # P6 migration: dropped
          'PyPDF2',
          'zope.formlib',
          # 'Products.cron4plone',  # P6 migration: cron4plone dropped, schedule via Plone clock-server
          ],
      entry_points={},
      )
