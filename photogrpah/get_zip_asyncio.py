import asyncio
import time


async def archivate():
    process = await asyncio.create_subprocess_shell('zip -r - files', stdout=asyncio.subprocess.PIPE)
    file = open('archive.zip', "wb")
    while True:
        archive = await process.stdout.read(n=1000)
        if process.stdout.at_eof():
            break
        file.write(archive)
    file.close()


async def main():
    print(f"started at {time.strftime('%X')}")
    task1 = asyncio.create_task(archivate())

    await task1

    print(f"finished at {time.strftime('%X')}")

if __name__ == '__main__':
    asyncio.run(main())