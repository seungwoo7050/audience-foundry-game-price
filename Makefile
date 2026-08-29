.PHONY: db-up db-down gate

db-up:
	docker compose -p gameprice-mvp up --detach --wait db

db-down:
	docker compose -p gameprice-mvp down --volumes --remove-orphans

gate:
	./scripts/gate.sh
