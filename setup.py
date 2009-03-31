from setuptools import setup, find_packages

setup(
    name='django-navbar',
    version='0.1.0',
    description='',
    author='Doug Napoleone',
    author_email='doug.napoleone@gmail.com',
    url='http://code.google.com/p/django-navbar/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=['setuptools'],
)
