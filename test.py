import docker
import docker.errors
import subprocess

import os

paths_towalk = []


async def find_compose_files():
    compose_paths = []

    for p in paths_towalk:
        for root, dirs, files in os.walk(p):
            if "docker-compose.yaml" in files:
                compose_paths.append(root + "/docker-compose.yaml")
            if "docker-compose.yml" in files:
                compose_paths.append(root + "/docker-compose.yml")

    return compose_paths


async def getlogs(paths):
    # Path to Docker Compose file
    compose_file = paths

    # Get list of service names
    result = subprocess.run(
        ["/usr/bin/docker", "compose", "-f", compose_file, "ps", "-q"],
        stdout=subprocess.PIPE,
        text=True,
    )
    services = result.stdout.splitlines()

    # Create docker client
    docker_client = docker.from_env()
    logfiles = []
    servicenames = []
    # Loop through services
    for service in services:
        try:
            # Get container from service name
            container = docker_client.containers.get(service)

            # Get log path
            log_path = container.attrs["LogPath"]
            name = container.attrs["Name"].replace("/", "")
            servicenames.append(name)
            logfiles.append(log_path)

            # Print service name and log path
            print(f"{service} logfile location: {log_path}")

        except docker.errors.NotFound:
            print(f"Container for {service} not found")
    return logfiles, servicenames


TOKEN = ""
admins = [263887960, 209702860]


import telebot
from telebot.async_telebot import AsyncTeleBot

bot = AsyncTeleBot(TOKEN)


@bot.message_handler(commands=["getpaths"])
async def get_paths(message):
    if message.chat.id in admins:
        fileslist = await find_compose_files()
        result = ""
        for file in fileslist:
            result += file + "\n"

        await bot.reply_to(message, result)
    else:
        await bot.reply_to(message, "not allowed")


@bot.message_handler(commands=["getlogs"])
async def get_logs(message):
    if message.chat.id in admins:
        path = message.text.split()
        if len(path) > 1:
            path = path[1]
        fl = await find_compose_files()
        if path not in fl:
            await bot.reply_to(message, "no such path")
            return
        await bot.reply_to(message, f"getting logs on {path}")
        fileslist, names = await getlogs(path)

        for i, file in enumerate(fileslist):
            await bot.send_document(
                message.chat.id, open(file, "rb"), visible_file_name=names[i] + ".log"
            )

        await bot.reply_to(
            message,
            "done",
        )
    else:
        await bot.reply_to(message, "not allowed")


import asyncio

asyncio.run(bot.infinity_polling(timeout=10))
