.PHONY: update

IMAGE_NAME=docker.monicz.pl/teodle

update:
	docker buildx build -t $(IMAGE_NAME) --push .
