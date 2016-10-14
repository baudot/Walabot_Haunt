#!/usr/bin/env python

from subprocess import call

def main():
	call (["omxplayer", "./sounds/target_is_fleeing.mp3"])
	return 0

if __name__ == '__main__':
	main()

