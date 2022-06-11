#!/usr/bin/python3
import subprocess


def main1():
    with open('photos.zip', "w") as outfile:
        subprocess.run(['zip', '-r', '-', 'files'], stdout=outfile)


def main():
    with open('archive.zip', "wb") as file:
        process = subprocess.Popen(['zip', '-r', '-', 'files'], stdout=subprocess.PIPE)
        archive, _ = process.communicate()
        file.write(archive)


if __name__ == '__main__':
    main()