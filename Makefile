ZIP		?= zip

NAME		:= ocr-service
VERSION	:= 0.1.0
ANKIADDON	:= $(NAME)-$(VERSION).ankiaddon
DEPS		:= __init__.py \
		   config.json \
		   config.md \
		   manifest.json \
		   README.md \
		   CHANGELOG.md \
		   LICENSE

all: 	$(ANKIADDON)
clean:	; rm -rf *.ankiaddon __pycache__
.PHONY: all clean format lint
.DELETE_ON_ERROR:

format:
	isort *.py
	black *.py

lint:
	flake8 .

$(ANKIADDON): $(DEPS)
	rm -f $@
	$(ZIP) -r9 $@ $^ -x '*/__pycache__/*'
