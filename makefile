.PHONY: build
dev:
	bash dev.sh
dev-server:
	sudo su root -c 'source /vagrant/vagrant-venv/bin/activate && cd /vagrant && export ENV="dev" && (make celery-server &) &&python main.py runserver'
celery-server:
	celery -A main.celery worker
build:
	bash build.sh
dev-requirements:
	pip freeze > requirements.txt
db-migrate:
	python main.py db migrate
db-deploy:
	python main.py deploy
py-lint:
	pylint --rcfile .pylintrc app/ tests/
shell:
	python main.py shell
test:
	make fmt-test
	make py-lint
	make smoke-test
	make unit-test
fmt:
	yapf -r -i app/ tests/ || :
fmt-test:
	yapf -r -d app/ tests/ || (echo "Document not formatted - run 'make fmt'" && exit 1)
unit-test:
	python main.py test
smoke-test:
	py.test tests/smoke -v -s
