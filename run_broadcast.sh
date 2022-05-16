export PYTHONPATH=.
export $(grep -v '^#' ./environment.env | xargs) # gets argument from .env file
python3 AdvancedAnalytics/RealtimeCommandsBroadcast.py 1h prod  #start_msg
