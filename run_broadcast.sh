export PYTHONPATH=.
export $(grep -v '^#' ./environment.env | xargs)
python3 AdvancedAnalytics/RealtimeCommandsBroadcast.py 1h prod  #start_msg
