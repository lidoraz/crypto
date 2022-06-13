export PYTHONPATH=.
export $(grep -v '^#' ./environment.env | xargs) # gets argument from .env file
python3 Realtime/Broadcast/HighChangeBroadcast.py 15min start_msg prod
