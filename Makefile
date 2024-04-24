install:
	@echo "Installing..."
	@python3 -m pip install -r requirements.txt --break-system-packages
	@sudo ./tools/llaves.py link