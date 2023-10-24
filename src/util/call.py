# -*- coding:utf-8 -*-

"""
system call function
"""

import asyncio


async def run_command(cmd: str) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd.split(" "),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        return True, stdout.decode().strip()
    else:
        return False, stderr.decode().strip()
