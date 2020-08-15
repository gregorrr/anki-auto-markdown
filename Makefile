all: 
	cd auto_markdown && zip -r ../releases/$$(date +%Y%m%d)-auto_markdown.zip *
	
