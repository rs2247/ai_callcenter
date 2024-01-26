source ../.env
if [[ ${PROD} = "True" ]];
then
	poetry run python bot_main.py
else
	source ../ai_callcenter/bin/activate
	python bot_main.py
fi
