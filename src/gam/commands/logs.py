import subprocess
import sys
import threading
from queue import Queue

from gam.stack_manager import StackManager


def cmd_logs(manager: StackManager, args) -> None:
    """Show logs from stack(s)."""
    stacks_to_show = []

    # Stack selection: positional > --all > --category > --tag > default
    if args.stacks:
        # Multiple specific stacks by name
        for stack_name in args.stacks:
            stack = manager.get_stack(stack_name)
            if not stack:
                print(f"Stack '{stack_name}' not found")
                sys.exit(1)
            stacks_to_show.append(stack)
    elif args.all:
        stacks_to_show = list(manager.stacks.values())
    elif args.category:
        stacks_to_show = manager.get_category_stacks(args.category)
        if not stacks_to_show:
            print(f"No stacks found in category '{args.category}'")
            sys.exit(1)
    elif args.tag:
        stacks_to_show = [
            s for s in manager.stacks.values() if args.tag in s.tags
        ]
        if not stacks_to_show:
            print(f"No stacks found with tag '{args.tag}'")
            sys.exit(1)
    else:
        # DEFAULT: Show all stacks (unique to logs command!)
        stacks_to_show = list(manager.stacks.values())

    if not stacks_to_show:
        print("No stacks found")
        sys.exit(1)

    # Build docker compose logs command
    cmd = ["docker", "compose", "logs"]
    if args.follow:
        cmd.append("--follow")
    if args.since:
        cmd.extend(["--since", args.since])
    if args.tail:
        cmd.extend(["--tail", args.tail])
    if args.timestamps:
        cmd.append("--timestamps")
    if args.until:
        cmd.extend(["--until", args.until])

    # Single stack: no prefixing, direct output
    if len(stacks_to_show) == 1:
        stack = stacks_to_show[0]
        print(f"Showing logs for {stack.name}...")
        subprocess.run(cmd, cwd=stack.path)
        return

    # Multiple stacks
    print(f"Showing logs from {len(stacks_to_show)} stack(s)...\n")

    if args.follow:
        _show_logs_parallel(stacks_to_show, cmd)
    else:
        _show_logs_serial(stacks_to_show, cmd)


def _show_logs_serial(stacks: list, cmd: list) -> None:
    """Show historical logs from multiple stacks serially."""
    for stack in stacks:
        result = subprocess.run(
            cmd,
            cwd=stack.path,
            capture_output=True,
            text=True
        )
        # Prefix each line with stack name
        if result.stdout:
            for line in result.stdout.splitlines():
                print(f"[{stack.name}] {line}")
        # Also show stderr if present
        if result.stderr:
            for line in result.stderr.splitlines():
                print(f"[{stack.name}] {line}", file=sys.stderr)


def _show_logs_parallel(stacks: list, cmd: list) -> None:
    """Stream logs from multiple stacks in parallel using threads."""
    output_queue = Queue()
    shutdown_event = threading.Event()
    threads = []

    # Start thread per stack
    for stack in stacks:
        thread = threading.Thread(
            target=_stream_logs_with_prefix,
            args=(stack.name, cmd, stack.path, output_queue,
                  shutdown_event)
        )
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # Print from queue until interrupted
    try:
        while True:
            if not output_queue.empty():
                line = output_queue.get()
                print(line, end='')
            else:
                # Small sleep to avoid busy waiting
                threading.Event().wait(0.01)
    except KeyboardInterrupt:
        print("\n\nStopping log streaming...")
        shutdown_event.set()
        for thread in threads:
            thread.join(timeout=2)


def _stream_logs_with_prefix(
    stack_name: str,
    cmd: list,
    cwd,
    output_queue: Queue,
    shutdown_event: threading.Event
) -> None:
    """Stream logs from a stack and prefix each line."""
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        try:
            for line in proc.stdout:
                if shutdown_event.is_set():
                    break
                output_queue.put(f"[{stack_name}] {line}")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
    except Exception as e:
        output_queue.put(
            f"[{stack_name}] Error streaming logs: {e}\n"
        )
