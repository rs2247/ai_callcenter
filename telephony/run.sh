source ../.env
if [[ ${PROD} = "True" ]];
then
	poetry run python main.py
else
	source ../ai_callcenter/bin/activate
	python main.py
fi
