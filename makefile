# Used to pass in build-time variables to go build
BUILD_DATE := $(shell date +%Y-%m-%d\ %H:%M)
#BRANCH = $(shell git rev-parse --abbrev-ref HEAD)


py_setup:
	pip install wheel setuptools twine pytest
py_build:
	rm -rf dist/*
	python3 setup.py sdist bdist_wheel

py_upload: py_build
	python3 -m twine upload --repository local dist/*

py_install_locally:
	pip install .


