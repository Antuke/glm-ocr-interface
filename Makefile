PID_FILE = server.pid
LOG_FILE = server.log

.PHONY: start stop watch

start:
	@if [ -f $(PID_FILE) ]; then \
		echo "Server is already running with PID `cat $(PID_FILE)`"; \
	else \
		nohup python main.py > $(LOG_FILE) 2>&1 & echo $$! > $(PID_FILE); \
		echo "Server started with PID `cat $(PID_FILE)`"; \
	fi

stop:
	@if [ -f $(PID_FILE) ]; then \
		kill `cat $(PID_FILE)` && rm $(PID_FILE); \
		echo "Server stopped"; \
	else \
		echo "Server is not running"; \
	fi

watch:
	tail -f $(LOG_FILE)

