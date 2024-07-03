
build:
	docker build -t fix-image-mtime .

run:
	docker run -it -v /Volumes/T5/Filmmaking/Footage/V002:/media fix-image-mtime /bin/bash
	# docker run -it -v ~/Development/fix-image-mtime:/x fix-image-mtime /bin/bash
