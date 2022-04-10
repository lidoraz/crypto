# copy from local to remote
scp -i "/Volumes/GoogleDrive/My Drive/Work/notebooks/unrelated/Crypto/shushu_entrance.pem" "/Users/lidorazulay/Library/Mobile Documents/com~apple~CloudDocs/DS/Crypto/crawler/crypto_crawler.py" ec2-user@ec2-18-134-142-217.eu-west-2.compute.amazonaws.com:crypto_crawler.py
scp -i "/Volumes/GoogleDrive/My Drive/Work/notebooks/unrelated/Crypto/shushu_entrance.pem" "/Users/lidorazulay/Library/Mobile Documents/com~apple~CloudDocs/DS/Crypto/crawler/crypto_crawler_hourly.py" ec2-user@ec2-18-134-142-217.eu-west-2.compute.amazonaws.com:crypto_crawler_hourly.py

# run on remote
# ps -ef | grep python
nohup python3 crypto_crawler.py > coin.out &
nohup python3 crypto_crawler_hourly.py > hourly.out &
