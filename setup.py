from setuptools import setup, find_packages

with open("README.en.rst", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='astraflux',
    version='1.3.7',
    description="AstraFlux Description",
    long_description=long_description,
    include_package_data=True,
    author='YanPing',
    author_email='zyphhxx@foxmail.com',
    maintainer='YanPing',
    maintainer_email='zyphhxx@foxmail.com',
    license='MIT License',
    url='https://github.com/ZYPGITA/astraflux',
    packages=find_packages(),
    keywords=["distributed", "microservice", "task-queue", "rpc", "scheduler"],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    python_requires=">=3.9",
    install_requires=[
        'requests~=2.32.5',
        'pika~=1.3.2',
        'dill~=0.4.0',
        'PyYAML~=6.0.2',
        'pymongo~=4.15.3',
        'redis~=7.0.1',
        'psutil~=7.1.3',
        'flask_cors~=6.0.2',
        'flask~=3.1.2',
        'openai>=2.28',
        'openai-agents>=0.14'
    ]
)
