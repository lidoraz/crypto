export PYTHONPATH=.
export $(grep -v '^#' ./environment.env | xargs) # gets argument from .env file
python3 Realtime/Broadcast/RealtimeCommandsBroadcast.py 1h start_msg #prod  #
