.PHONY: clean
clean:
	find . -name "*.pyc" -delete

.PHONY: test
test:
	rake test
