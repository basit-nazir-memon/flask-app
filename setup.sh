#!/bin/bash

# Update and install dependencies
apt-get update
apt-get install -y wget gnupg

# Download and install Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome-stable_current_amd64.deb
apt-get -f install -y

# Download and install ChromeDriver
LATEST=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/$LATEST/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver /usr/local/bin/chromedriver
chmod +x /usr/local/bin/chromedriver

# Clean up
rm google-chrome-stable_current_amd64.deb
rm chromedriver_linux64.zip
