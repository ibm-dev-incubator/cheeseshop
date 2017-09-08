SHELL := /bin/bash
REV_FILE=.make-rev-check

set-rev:
	git rev-parse --short HEAD > $(REV_FILE)

images: set-rev
	./deploy/images/make-image.sh deploy/images/static-server.Dockerfile "cheeseshop-static:$$(cat $(REV_FILE))"
	./deploy/images/make-image.sh deploy/images/cheeseshop.Dockerfile "cheeseshop-webapp:$$(cat $(REV_FILE))"

tag-images: set-rev
	sudo docker tag "cheeseshop-static:$$(cat $(REV_FILE))" "container-registry.dev.ibmesports.com/cheeseshop-static:$$(cat $(REV_FILE))"
	sudo docker tag "cheeseshop-webapp:$$(cat $(REV_FILE))" "container-registry.dev.ibmesports.com/cheeseshop-webapp:$$(cat $(REV_FILE))"

upload-images: set-rev
	sudo docker push "container-registry.dev.ibmesports.com/cheeseshop-static:$$(cat $(REV_FILE))"
	sudo docker push "container-registry.dev.ibmesports.com/cheeseshop-webapp:$$(cat $(REV_FILE))"

.PHONY: deploy
deploy: set-rev
	IMAGE_TAG=$$(cat $(REV_FILE)) envsubst < deploy/webapp.yaml | kubectl apply -f -

delete-deployments:
	kubectl delete deployment cheeseshop-static
	kubectl delete deployment cheeseshop-webapp

redeploy: delete-deployments deploy
