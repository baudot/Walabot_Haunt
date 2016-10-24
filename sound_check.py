#!/usr/bin/env python

from subprocess import call

def main():
	call (["omxplayer", "-o", "both", "./sounds/target_detected.mp3"])
	return 0

if __name__ == '__main__':
	main()

